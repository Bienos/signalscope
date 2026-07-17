from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from pwdlib import PasswordHash
from sqlalchemy import func, select

from .config import Settings, settings
from .db import Base, SessionLocal, engine
from .domain.toys import load_toy_taxonomy
from .models import (
    DailyReport,
    ProviderQuarantine,
    ProviderRun,
    TrendCluster,
    User,
    Watchlist,
)
from .providers.apify import ActorRequest, ApifyProviderSettings, ApifyTikTokProvider
from .providers.factory import provider_factory
from .providers.mock import MockProvider
from .services.pipeline import ingest, make_report, score_all
from .services.toy_api import report_payload
from .services.toy_intelligence import build_or_update_toy_signals
from .services.toy_monitoring import MAX_DUE_REFRESH_URLS, plan_due_video_refreshes

DEMO_ADMIN_EMAIL = "admin@viralradar.local"


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _print_json(value: object) -> None:
    print(json.dumps(value, indent=2, default=str, sort_keys=True))


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _confirmed(args: list[str]) -> bool:
    """A paid run needs a deliberate, exact command-line confirmation."""

    return "--confirm-live-run" in args


def _values(args: list[str], flag: str) -> list[str]:
    values: list[str] = []
    for index, argument in enumerate(args):
        if argument == flag and index + 1 < len(args):
            values.append(args[index + 1])
        elif argument.startswith(f"{flag}="):
            values.append(argument.split("=", 1)[1])
    return [value for value in values if value]


def _positive_int_value(args: list[str], flag: str, default: int) -> int:
    values = _values(args, flag)
    if not values:
        return default
    try:
        value = int(values[-1])
    except ValueError as exc:
        raise ValueError(f"{flag} must be a positive integer") from exc
    if value < 1:
        raise ValueError(f"{flag} must be a positive integer")
    return value


def _apify_provider(cfg: Settings | None = None) -> ApifyTikTokProvider:
    selected = cfg or settings()
    taxonomy = load_toy_taxonomy()
    explicit_queries = _split(selected.apify_search_queries)
    explicit_hashtags = _split(selected.apify_hashtags)
    taxonomy_queries = [
        term
        for language in sorted(taxonomy.search_terms)
        for term in taxonomy.search_terms[language]
    ]
    return ApifyTikTokProvider(
        settings=ApifyProviderSettings.from_app_settings(selected),
        search_queries=explicit_queries or taxonomy_queries,
        hashtags=explicit_hashtags or list(taxonomy.hashtags),
        profiles=_split(selected.apify_profiles),
        post_urls=_split(selected.apify_post_urls),
        max_items=selected.apify_max_items,
        max_total_charge_usd=selected.apify_max_total_charge_usd,
    )


def _month_spend() -> float:
    month_start = utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    with SessionLocal() as db:
        return float(
            db.scalar(
                select(func.coalesce(func.sum(ProviderRun.cost), 0.0)).where(
                    ProviderRun.provider.like("apify:%"),
                    ProviderRun.started_at >= month_start,
                )
            )
            or 0.0
        )


def _default_report_user_key(db: Any) -> str:
    demo_user = db.scalar(select(User).where(User.email == DEMO_ADMIN_EMAIL))
    return str(demo_user.id) if demo_user is not None else "single-user"


def _discovery_requests(provider: ApifyTikTokProvider) -> list[ActorRequest]:
    requests: list[ActorRequest] = []
    if provider.search_queries:
        requests.append(provider.keyword_request(provider.search_queries))
    if provider.hashtags:
        requests.append(provider.hashtag_request(provider.hashtags))
    if provider.profiles:
        requests.append(provider.profile_request(provider.profiles))
    return requests


def _persist_quarantine(
    db: Any,
    run: ProviderRun,
    records: list[dict[str, Any]],
) -> None:
    for record in records:
        db.add(
            ProviderQuarantine(
                provider_run_id=run.id,
                provider=run.provider,
                external_record_id=(
                    str(record.get("index")) if record.get("index") is not None else None
                ),
                reason_code=str(
                    record.get("category") or record.get("reason") or "invalid_record"
                ),
                redacted_summary=str(record.get("summary") or "Invalid provider record")[:2000],
                schema_fingerprint=record.get("schema_fingerprint"),
                missing_fields=list(record.get("missing_fields") or []),
            )
        )


def _execute_request(provider: ApifyTikTokProvider, request: ActorRequest) -> dict[str, Any]:
    """Execute one confirmed request and preserve its run-level evidence."""

    preflight = provider.preflight(request)
    if not provider.enabled:
        raise RuntimeError(
            "Live Apify collection is disabled or incomplete; no paid run was started"
        )
    with SessionLocal() as db:
        run = ProviderRun(
            provider=f"apify:{request.actor_id}",
            actor_id=request.actor_id,
            collection_type=request.collection_type.value,
            market=request.market,
            query_provenance={"values": list(request.source_values)},
            started_at=utc_now(),
            status="running",
            quality={"preflight": preflight},
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        try:
            rows = provider.collect_sync(request)
            quality = dict(provider.last_run_quality)
            ingest_result = ingest(
                db,
                rows,
                collected_at=utc_now(),
                provider_run_id=run.id,
                collection_market=request.market,
            )
            build_or_update_toy_signals(db)
            run.actor_version = quality.get("actor_version")
            run.external_run_id = quality.get("external_run_id")
            run.dataset_id = quality.get("dataset_id")
            run.status = str(quality.get("status") or "success")
            run.finished_at = utc_now()
            run.returned_records = int(quality.get("returned_records") or len(rows))
            run.accepted_records = int(quality.get("accepted_records") or len(rows))
            run.invalid_records = int(quality.get("invalid_records") or 0)
            run.duplicate_records = int(ingest_result.get("duplicates") or 0)
            run.missing_field_rate = (
                sum(len(row.missing_fields) for row in rows) / max(1, len(rows) * 5)
            )
            run.cost = quality.get("cost_usd")
            run.currency = str(quality.get("currency") or "USD")
            fingerprints = list(quality.get("schema_fingerprints") or [])
            run.schema_fingerprint = ",".join(fingerprints)[:128] or None
            run.quality = {
                "preflight": preflight,
                "ingest": ingest_result,
                "provider": quality,
            }
            _persist_quarantine(db, run, list(quality.get("quarantine") or []))
            db.commit()
            return {
                "executed": True,
                "run_id": run.id,
                "status": run.status,
                "ingest": ingest_result,
                "cost_usd": run.cost,
            }
        except Exception as exc:
            # Never include the token in persisted or printed diagnostics.
            token = settings().apify_token.get_secret_value()
            safe_error = str(exc).replace(token, "[REDACTED]") if token else str(exc)
            run.status = "failed"
            run.finished_at = utc_now()
            run.error_category = exc.__class__.__name__
            run.error_summary = safe_error[:2000]
            db.commit()
            raise


def seed() -> None:
    Base.metadata.create_all(engine)
    now = utc_now()
    with SessionLocal() as db:
        demo_user = db.scalar(select(User).where(User.email == DEMO_ADMIN_EMAIL))
        if demo_user is None:
            demo_user = User(
                email=DEMO_ADMIN_EMAIL,
                password_hash=PasswordHash.recommended().hash("RadarDemo!2026"),
                role="admin",
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
        demo_user_key = str(demo_user.id)
        for run_index in range(4):
            collected_at = now - timedelta(hours=18 - run_index * 6)
            provider_run = ProviderRun(
                provider="mock",
                collection_type="demo_fixture",
                market="GB,PL",
                query_provenance={"fixture_version": "mock-toy-1.0"},
                started_at=collected_at,
                finished_at=collected_at,
                status="success",
                returned_records=48,
                accepted_records=48,
                quality={"data_state": "synthetic_demo"},
            )
            db.add(provider_run)
            db.commit()
            db.refresh(provider_run)
            ingest(
                db,
                MockProvider(run_index).discover_videos(),
                collected_at,
                provider_run_id=provider_run.id,
            )
        if not db.scalar(select(TrendCluster)):
            db.add_all(
                [
                    TrendCluster(
                        name="Toy constraint comparison",
                        category="toy",
                        rfs=84,
                        creators=8,
                        description=(
                            "Several synthetic toy creators compare products under a shared "
                            "constraint."
                        ),
                        adaptation=(
                            "Create new tests, visuals, wording and cleared audio around an "
                            "original decision criterion."
                        ),
                    ),
                    TrendCluster(
                        name="Toy reveal sequence",
                        category="toy",
                        rfs=77,
                        creators=6,
                        description="Premise, progressive toy evidence and concise payoff.",
                        adaptation=(
                            "Use an original setting and evidence sequence with cleared audio."
                        ),
                    ),
                ]
            )
        if not db.scalar(
            select(Watchlist).where(
                Watchlist.user_key == demo_user_key, Watchlist.name == "UK toy radar"
            )
        ):
            db.add(
                Watchlist(
                    user_key=demo_user_key,
                    name="UK toy radar",
                    objective="Detect evidence-backed toy momentum for UK client briefs.",
                    categories=[
                        "Sensory and fidget toys",
                        "Plush and soft toys",
                        "Blind boxes and collectibles",
                        "Construction toys",
                        "STEM and educational toys",
                    ],
                    markets=["GB"],
                    languages=["en"],
                    data_status="demo",
                )
            )
        if not db.scalar(
            select(Watchlist).where(
                Watchlist.user_key == demo_user_key,
                Watchlist.name == "Poland toy radar",
            )
        ):
            db.add(
                Watchlist(
                    user_key=demo_user_key,
                    name="Poland toy radar",
                    objective="Monitor Polish toy and gift-buyer signals.",
                    categories=[
                        "Seasonal and gifting toys",
                        "Construction toys",
                        "Sensory and fidget toys",
                        "Blind boxes and collectibles",
                    ],
                    markets=["PL"],
                    languages=["pl"],
                    data_status="demo",
                )
            )
        db.commit()
        score_all(db)
        signals = build_or_update_toy_signals(db, now=now)
        make_report(db, user_key=demo_user_key)
        payload = report_payload(db, user_key=demo_user_key)
        report_row = db.scalar(
            select(DailyReport).where(
                DailyReport.report_date == now.date().isoformat(),
                DailyReport.user_key == demo_user_key,
            )
        )
        if report_row:
            report_row.payload = payload
            report_row.created_at = now
            report_row.status = "draft"
        db.commit()
    print(f"Seeded deterministic toy demo data with {len(signals)} decision signals")


def collect() -> None:
    """Legacy collection command; Apify is redirected to safe preflight."""

    Base.metadata.create_all(engine)
    cfg = settings()
    if cfg.provider_type.strip().lower() == "apify":
        print(
            "The legacy collect command never starts Apify. Use toy-discover for a "
            "preflight, then add --confirm-live-run only after reviewing the cost ceiling."
        )
        toy_discover([])
        return
    provider = provider_factory(
        cfg, mock_run=int(utc_now().timestamp() // 21600) % 20
    )
    health = provider.health_check()
    with SessionLocal() as db:
        run = ProviderRun(
            provider=str(health.get("provider", cfg.provider_type)),
            started_at=utc_now(),
            status="running",
            quality={"health": health},
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        try:
            rows = provider.discover_videos()
            result = ingest(db, rows, utc_now(), provider_run_id=run.id)
            score_all(db)
            build_or_update_toy_signals(db)
            run.status = "success"
            run.finished_at = utc_now()
            run.returned_records = len(rows)
            run.accepted_records = len(rows)
            run.duplicate_records = int(result["duplicates"])
            run.quality = {
                **result,
                "query_success_rate": 1,
                "missing_priority_metrics": sum(bool(row.missing_fields) for row in rows),
                "market_coverage": sorted({row.market for row in rows}),
                "language_coverage": sorted({row.language for row in rows}),
                **getattr(provider, "last_run_quality", {}),
            }
        except Exception as exc:
            run.status = "failed"
            run.finished_at = utc_now()
            run.error = str(exc)
        db.commit()
        final_status = run.status
    print(final_status)


def report() -> None:
    with SessionLocal() as db:
        generated = make_report(db, user_key=_default_report_user_key(db))
        Path("outputs").mkdir(exist_ok=True)
        Path(f"outputs/report-{generated.report_date}.json").write_text(
            json.dumps(generated.payload, indent=2), encoding="utf-8"
        )
        print(generated.id)


def toy_score() -> None:
    with SessionLocal() as db:
        legacy_count = score_all(db)
        signals = build_or_update_toy_signals(db)
    _print_json({"videos_scored": legacy_count, "toy_signals": len(signals)})


def toy_report() -> None:
    now = utc_now()
    with SessionLocal() as db:
        user_key = _default_report_user_key(db)
        build_or_update_toy_signals(db, now=now)
        payload = report_payload(db, user_key=user_key)
        report_date = now.date().isoformat()
        row = db.scalar(
            select(DailyReport).where(
                DailyReport.report_date == report_date,
                DailyReport.user_key == user_key,
            )
        )
        if row is None:
            row = DailyReport(
                report_date=report_date,
                user_key=user_key,
                created_at=now,
                payload=payload,
                status="draft",
            )
            db.add(row)
        else:
            row.created_at = now
            row.payload = payload
            row.status = "draft"
        db.commit()
        db.refresh(row)
        Path("outputs").mkdir(exist_ok=True)
        output = Path(f"outputs/toy-report-{report_date}.json")
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _print_json({"report_id": row.id, "status": row.status, "path": str(output)})


def apify_config_check(_: list[str] | None = None) -> None:
    """Validate configuration only; no network request or Actor run occurs."""

    provider = _apify_provider()
    _print_json({**provider.health_check(), "paid_run_started": False})


def provider_health(_: list[str] | None = None) -> None:
    cfg = settings()
    if cfg.provider_type.strip().lower() == "apify":
        health = _apify_provider(cfg).health_check()
    elif cfg.provider_type.strip().lower() == "mock":
        health = MockProvider().health_check()
    else:
        health = {
            "ok": None,
            "provider": cfg.provider_type,
            "network_check": "not_run",
            "note": "Configuration summary only; no provider request was sent.",
        }
    with SessionLocal() as db:
        latest = db.scalar(select(ProviderRun).order_by(ProviderRun.started_at.desc()))
        persisted = (
            {
                "run_id": latest.id,
                "status": latest.status,
                "started_at": latest.started_at,
                "finished_at": latest.finished_at,
                "missing_field_rate": latest.missing_field_rate,
            }
            if latest
            else None
        )
    _print_json({**health, "latest_persisted_run": persisted, "paid_run_started": False})


def provider_costs(_: list[str] | None = None) -> None:
    cfg = settings()
    spend = _month_spend()
    _print_json(
        {
            "currency": "USD",
            "monthly_budget": cfg.apify_monthly_budget_usd,
            "observed_monthly_spend": round(spend, 4),
            "remaining_budget": round(
                max(0.0, cfg.apify_monthly_budget_usd - spend), 4
            ),
            "paid_run_started": False,
            "note": (
                "Preflight estimates are planning values; maxTotalChargeUsd is the "
                "execution ceiling."
            ),
        }
    )


def toy_discover(args: list[str] | None = None) -> None:
    arguments = list(args or [])
    provider = _apify_provider()
    provider.monthly_spend_usd = _month_spend()
    requests = _discovery_requests(provider)
    if not requests:
        raise ValueError("Configure at least one toy keyword, hashtag or selected profile")
    preflights = [provider.preflight(request) for request in requests]
    if not _confirmed(arguments):
        _print_json(
            {
                "executed": False,
                "confirmation_required": True,
                "confirmation_flag": "--confirm-live-run",
                "preflights": preflights,
            }
        )
        return
    results = [_execute_request(provider, request) for request in requests]
    _print_json({"executed": True, "runs": results})


def toy_refresh(args: list[str] | None = None) -> None:
    arguments = list(args or [])
    cfg = settings()
    due_mode = "--due" in arguments
    if any(argument.startswith("--due=") for argument in arguments):
        raise ValueError("--due is a flag and does not accept a value")
    explicit_urls = _values(arguments, "--url")
    if due_mode and explicit_urls:
        raise ValueError("Use either --due or --url, not both")

    plan_payload: dict[str, object] | None = None
    due_items = []
    if due_mode:
        requested_limit = _positive_int_value(
            arguments, "--limit", MAX_DUE_REFRESH_URLS
        )
        provider_url_limit = (
            cfg.apify_results_per_page or cfg.apify_max_results_per_query
        )
        with SessionLocal() as db:
            plan = plan_due_video_refreshes(
                db, limit=min(requested_limit, provider_url_limit)
            )
        plan_payload = plan.payload()
        plan_payload["cli_requested_limit"] = requested_limit
        plan_payload["provider_url_limit"] = provider_url_limit
        due_items = list(plan.selected)
        urls = [item.canonical_url for item in due_items]
    else:
        if _values(arguments, "--limit"):
            raise ValueError("--limit is only supported with --due")
        urls = explicit_urls or _split(cfg.apify_post_urls)
    if not urls:
        if due_mode:
            _print_json(
                {
                    "executed": False,
                    "confirmation_required": False,
                    "plan": plan_payload,
                    "message": "No eligible canonical video URL is currently due.",
                }
            )
            return
        raise ValueError(
            "Provide at least one canonical TikTok video URL with --url; no URL was refreshed"
        )
    provider = _apify_provider(cfg)
    provider.monthly_spend_usd = _month_spend()
    if due_mode:
        requests = [
            provider.direct_refresh_request(
                [item.canonical_url for item in due_items if item.market == market],
                market=market,
            )
            for market in sorted({item.market for item in due_items})
        ]
    else:
        requests = [provider.direct_refresh_request(urls)]
    preflights = [provider.preflight(request) for request in requests]
    if not _confirmed(arguments):
        _print_json(
            {
                "executed": False,
                "confirmation_required": True,
                "confirmation_flag": "--confirm-live-run",
                "plan": plan_payload,
                "preflights": preflights,
            }
        )
        return
    results = [_execute_request(provider, request) for request in requests]
    _print_json(
        {
            "executed": True,
            "plan": plan_payload,
            "runs": results,
        }
    )


def _legacy_score(_: list[str] | None = None) -> None:
    with SessionLocal() as db:
        print(score_all(db))


def _run_no_args(function: Callable[[], None]) -> Callable[[list[str]], None]:
    return lambda _args: function()


COMMANDS: dict[str, Callable[[list[str]], None]] = {
    "seed": _run_no_args(seed),
    "collect": _run_no_args(collect),
    "score": _legacy_score,
    "report": _run_no_args(report),
    "apify-config-check": apify_config_check,
    "toy-discover": toy_discover,
    "toy-refresh": toy_refresh,
    "toy-score": _run_no_args(toy_score),
    "toy-report": _run_no_args(toy_report),
    "provider-health": provider_health,
    "provider-costs": provider_costs,
}


def main(argv: list[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    if not arguments or arguments[0] not in COMMANDS:
        print("Use " + "|".join(COMMANDS))
        return 2
    COMMANDS[arguments[0]](arguments[1:])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
