from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.toy_schemas import (
    BriefInput,
    DecisionInput,
    NoteInput,
    ProviderExecutionInput,
    ProviderPreflightInput,
    ProviderRefreshInput,
    ReportInput,
    SaveOpportunityInput,
)
from app.auth import admin, current_user
from app.config import settings
from app.db import get_db
from app.models import (
    DailyReport,
    Opportunity,
    ProviderQuarantine,
    ProviderRun,
    SignalDecision,
    Snapshot,
    ToySignal,
    User,
)
from app.providers.apify import (
    ActorRequest,
    ApifyProviderError,
    ApifyProviderSettings,
    ApifyTikTokProvider,
)
from app.providers.apify.errors import redact_text
from app.services.pipeline import ingest
from app.services.toy_api import (
    collection_envelope,
    creator_collection,
    hashtag_collection,
    provider_context,
    report_payload,
    serialize_opportunity,
    serialize_report,
    serialize_signal,
    sound_collection,
    utc_now,
    watchlist_collection,
)
from app.services.toy_intelligence import (
    active_toy_signals,
    active_videos,
    build_or_update_toy_signals,
)

router = APIRouter(prefix="/api", tags=["toy trend intelligence"])


def _user_key(user: User) -> str:
    return str(user.id)


def _ensure_signals(db: Session) -> list[ToySignal]:
    signals = active_toy_signals(db)
    if not signals and active_videos(db):
        build_or_update_toy_signals(db)
        signals = active_toy_signals(db)
    return signals


@router.get("/toys/overview")
def toy_overview(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    context = provider_context(db)
    signals = _ensure_signals(db)
    items = [serialize_signal(db, signal, user_key=_user_key(user)) for signal in signals]
    queues = {
        "act": [item for item in items if item["recommendation"] == "Act"],
        "monitor": [item for item in items if item["recommendation"] == "Monitor"],
        "avoid": [item for item in items if item["recommendation"] == "Avoid"],
    }
    opportunities = db.scalars(
        select(Opportunity).where(Opportunity.user_key == _user_key(user))
    ).all()
    notes_completed = db.scalar(
        select(func.count())
        .select_from(SignalDecision)
        .where(
            SignalDecision.user_key == _user_key(user),
            SignalDecision.analyst_note != "",
        )
    ) or 0
    top = sorted(signals, key=lambda item: item.opportunity_score, reverse=True)
    return {
        **context,
        "since_last_review": _since_last_review(signals),
        "decision_queue": queues,
        "market_pulse": {
            "categories": _unique([item.toy_category for item in top])[:5],
            "hashtags": [f"#{tag.removeprefix('#')}" for tag in _unique([tag for item in top for tag in item.related_hashtags or []])[:5]],
            "creators": [item["username"] for item in creator_collection(db)[:5]],
            "mechanisms": _unique([item.content_mechanism for item in top])[:5],
            "sounds": _unique([sound for item in top for sound in item.related_sounds or []])[:5],
        },
        "report_readiness": {
            "opportunities_selected": sum(item.include_in_report for item in opportunities),
            "notes_completed": int(notes_completed),
            "awaiting_review": sum(item.review_status != "Approved" for item in opportunities),
            "status": "Ready for analyst review" if opportunities and all(item.review_status == "Approved" for item in opportunities) else "Draft requires review",
        },
    }


@router.get("/toys/signals")
def toy_signals(
    market: str | None = None,
    language: str | None = None,
    category: str | None = None,
    mechanism: str | None = None,
    lifecycle: str | None = None,
    decision: str | None = None,
    confidence: str | None = None,
    safety: str | None = None,
    q: str | None = None,
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    results = [
        serialize_signal(db, signal, user_key=_user_key(user), include_detail=True)
        for signal in _ensure_signals(db)
    ]
    query = (q or "").casefold()
    results = [
        item
        for item in results
        if (not market or market in item["markets"])
        and (not language or language in item["languages"])
        and (not category or item["category"] == category)
        and (not mechanism or item["mechanism"] == mechanism)
        and (not lifecycle or item["lifecycle"] == lifecycle)
        and (not decision or item["recommendation"] == decision)
        and (not confidence or item["confidence"] == confidence)
        and (not safety or item["safety_state"] == safety)
        and (
            not query
            or query
            in f"{item['title']} {item['conclusion']} {item['category']} {item['mechanism']}".casefold()
        )
    ][:limit]
    return collection_envelope(db, results)


@router.get("/toys/signals/{signal_id}")
def toy_signal_detail(
    signal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    signal = db.get(ToySignal, signal_id)
    if signal is None:
        raise HTTPException(404, "Toy signal not found")
    return serialize_signal(db, signal, user_key=_user_key(user), include_detail=True)


@router.get("/toys/videos")
def toy_videos(
    limit: int = Query(default=100, ge=1, le=250),
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
) -> dict[str, Any]:
    items = []
    videos = sorted(
        (video for video in active_videos(db) if video.toy_category is not None),
        key=lambda video: video.last_observed_at or video.published_at,
        reverse=True,
    )[:limit]
    for video in videos:
        latest = db.scalar(
            select(Snapshot)
            .where(
                Snapshot.video_id == video.id,
                Snapshot.source == video.provider,
            )
            .order_by(Snapshot.collected_at.desc())
        )
        items.append(
            {
                "id": str(video.id),
                "canonical_url": video.url,
                "caption": video.caption,
                "toy_category": video.toy_category,
                "content_mechanism": video.content_mechanism,
                "market": video.collection_market or video.market,
                "language": video.provider_language or video.language,
                "published_at": video.published_at,
                "views": latest.views if latest else None,
                "likes": latest.likes if latest else None,
                "comments": latest.comments if latest else None,
                "shares": latest.shares if latest else None,
                "saves": latest.favourites if latest else None,
                "missing_fields": sorted(set(video.missing_fields or []).union(latest.missing_fields or [] if latest else [])),
                "provider": video.provider,
                "availability": video.availability_status,
            }
        )
    return collection_envelope(db, items)


@router.get("/toys/creators")
def toy_creators(db: Session = Depends(get_db), _: User = Depends(current_user)) -> dict[str, Any]:
    return collection_envelope(db, creator_collection(db))


@router.get("/toys/hashtags")
def toy_hashtags(db: Session = Depends(get_db), _: User = Depends(current_user)) -> dict[str, Any]:
    return collection_envelope(db, hashtag_collection(db))


@router.get("/toys/sounds")
def toy_sounds(db: Session = Depends(get_db), _: User = Depends(current_user)) -> dict[str, Any]:
    return collection_envelope(db, sound_collection(db))


@router.get("/toys/watchlists")
def toy_watchlists(db: Session = Depends(get_db), _: User = Depends(current_user)) -> dict[str, Any]:
    return collection_envelope(db, watchlist_collection(db))


@router.get("/toys/opportunities")
def toy_opportunities(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    items = [
        serialize_opportunity(db, item)
        for item in db.scalars(
            select(Opportunity)
            .where(Opportunity.user_key == _user_key(user))
            .order_by(Opportunity.updated_at.desc())
        ).all()
    ]
    return collection_envelope(db, items)


@router.get("/toys/reports")
def toy_reports(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    reports = db.scalars(
        select(DailyReport)
        .where(DailyReport.user_key == _user_key(user))
        .order_by(DailyReport.created_at.desc())
        .limit(30)
    ).all()
    return collection_envelope(db, [serialize_report(db, report) for report in reports])


@router.get("/toys/data-health")
def toy_data_health(db: Session = Depends(get_db), _: User = Depends(current_user)) -> dict[str, Any]:
    context = provider_context(db)
    runs = db.scalars(select(ProviderRun).order_by(ProviderRun.started_at.desc()).limit(30)).all()
    quarantine_count = db.scalar(select(func.count()).select_from(ProviderQuarantine)) or 0
    return {
        **context,
        "runs": [_run_payload(run) for run in runs],
        "quarantined_records": quarantine_count,
        "rules": {
            "missing_is_not_zero": True,
            "snapshots_append_only": True,
            "creator_region_is_audience_geography": False,
            "age_inference_enabled": False,
            "media_downloads_enabled": False,
        },
    }


@router.post("/toys/signals/{signal_id}/decision")
def save_signal_decision(
    signal_id: int,
    value: DecisionInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    signal = _require_signal(db, signal_id)
    user_key = _user_key(user)
    item = db.scalar(
        select(SignalDecision).where(
            SignalDecision.signal_id == signal.id,
            SignalDecision.user_key == user_key,
        )
    )
    now = utc_now()
    if item is None:
        item = SignalDecision(
            signal_id=signal.id,
            user_id=user.id,
            user_key=user_key,
            decision=value.decision,
            created_at=now,
        )
        db.add(item)
    item.decision = value.decision
    item.reason = value.reason
    item.analyst_note = value.analyst_note or item.analyst_note
    item.review_date = (
        datetime.combine(value.review_date, datetime.min.time()) if value.review_date else None
    )
    item.updated_at = now
    db.commit()
    return serialize_signal(db, signal, user_key=user_key, include_detail=True)


@router.post("/toys/signals/{signal_id}/notes")
def save_signal_note(
    signal_id: int,
    value: NoteInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    signal = _require_signal(db, signal_id)
    user_key = _user_key(user)
    item = db.scalar(
        select(SignalDecision).where(
            SignalDecision.signal_id == signal.id,
            SignalDecision.user_key == user_key,
        )
    )
    now = utc_now()
    if item is None:
        item = SignalDecision(
            signal_id=signal.id,
            user_id=user.id,
            user_key=user_key,
            decision=signal.recommended_decision,
            created_at=now,
        )
        db.add(item)
    item.analyst_note = value.analyst_note
    item.updated_at = now
    db.commit()
    return serialize_signal(db, signal, user_key=user_key, include_detail=True)


@router.post("/toys/signals/{signal_id}/save")
def save_opportunity(
    signal_id: int,
    value: SaveOpportunityInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    signal = _require_signal(db, signal_id)
    item = _opportunity_for(db, signal, user)
    item.decision = value.decision or signal.recommended_decision
    item.title = value.title or signal.title
    item.rationale = value.rationale or signal.main_supporting_evidence
    item.client_context = value.client_context or item.client_context
    item.decision_window = value.decision_window or _window(signal.lifecycle)
    item.mechanism = signal.content_mechanism
    item.include_in_report = value.include_in_report
    item.updated_at = utc_now()
    db.commit()
    return serialize_opportunity(db, item)


@router.post("/toys/signals/{signal_id}/create-brief")
def create_brief(
    signal_id: int,
    value: BriefInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    signal = _require_signal(db, signal_id)
    if not value.originality_checks or not all(value.originality_checks.values()):
        raise HTTPException(422, "Complete every originality confirmation before saving a brief")
    if not value.safety_checks or not all(value.safety_checks.values()):
        raise HTTPException(422, "Complete every safety and rights confirmation before saving a brief")
    item = _opportunity_for(db, signal, user)
    item.state = "brief"
    item.title = value.title or signal.title
    item.decision = signal.recommended_decision
    item.rationale = signal.main_supporting_evidence
    item.decision_window = _window(signal.lifecycle)
    item.mechanism = signal.content_mechanism
    item.audience_need = value.audience_need or ""
    item.original_hook = value.original_hook or ""
    item.content_structure = value.content_structure or ""
    item.recommended_creator_type = value.recommended_creator_type or "Unknown"
    item.production_complexity = value.production_complexity
    item.elements_not_to_copy = _lines(value.elements_not_to_copy) or ["Source wording", "Identifiable creator execution", "Uncleared audio"]
    item.safety_considerations = _lines(value.safety_considerations) or ["Complete product-specific toy safety review"]
    item.rights_considerations = _lines(value.rights_considerations) or ["Music rights unknown", "Verify licensed-character permissions"]
    item.evidence_limitations = _lines(value.evidence_limitations) or [signal.main_contradictory_evidence]
    item.originality_checks = value.originality_checks
    item.safety_checks = value.safety_checks
    item.brief_status = "ready_for_review"
    item.review_status = "pending"
    item.updated_at = utc_now()
    db.commit()
    return serialize_opportunity(db, item)


@router.post("/toys/reports")
def create_toy_report(
    value: ReportInput,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
) -> dict[str, Any]:
    _ensure_signals(db)
    payload = report_payload(
        db,
        user_key=_user_key(user),
        include_opportunity_ids=value.include_opportunity_ids,
    )
    if value.market:
        for group in ("act", "monitor", "avoid"):
            payload[group] = [item for item in payload[group] if value.market in item["markets"]]
    if value.language:
        for group in ("act", "monitor", "avoid"):
            payload[group] = [item for item in payload[group] if value.language in item["languages"]]
    today = datetime.now(UTC).date().isoformat()
    user_key = _user_key(user)
    report = db.scalar(
        select(DailyReport).where(
            DailyReport.report_date == today,
            DailyReport.user_key == user_key,
        )
    )
    if report is None:
        report = DailyReport(
            report_date=today,
            user_key=user_key,
            created_at=utc_now(),
            payload=payload,
            status="draft",
        )
        db.add(report)
    else:
        report.created_at = utc_now()
        report.payload = payload
        report.status = "draft"
    db.commit()
    db.refresh(report)
    return serialize_report(db, report)


def _provider() -> ApifyTikTokProvider:
    return ApifyTikTokProvider(settings=ApifyProviderSettings.from_app_settings(settings()))


def _actor_request(provider: ApifyTikTokProvider, value: ProviderPreflightInput) -> ActorRequest:
    if value.collection_type == "keyword":
        return provider.keyword_request(value.values, market=value.market, result_limit=value.max_results)
    if value.collection_type == "hashtag":
        return provider.hashtag_request(value.values, market=value.market, result_limit=value.max_results)
    if value.collection_type == "profile":
        return provider.profile_request(value.values, market=value.market, result_limit=value.max_results)
    if value.collection_type == "discover":
        return provider.discover_expansion_request(
            value.values, market=value.market, result_limit=value.max_results
        )
    raise HTTPException(422, "Use /api/providers/apify/refresh for canonical video URLs")


def _monthly_spend(db: Session) -> float:
    first = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    return float(
        db.scalar(
            select(func.coalesce(func.sum(ProviderRun.cost), 0.0)).where(
                ProviderRun.provider.like("apify:%"),
                ProviderRun.started_at >= first,
            )
        )
        or 0.0
    )


@router.post("/providers/apify/discover")
async def apify_discover(
    value: ProviderExecutionInput,
    db: Session = Depends(get_db),
    _: User = Depends(admin),
) -> dict[str, Any]:
    provider = _provider()
    provider.monthly_spend_usd = _monthly_spend(db)
    request = _actor_request(provider, value)
    preflight = provider.preflight(request)
    if not value.confirm_live_run:
        return {"executed": False, "confirmation_required": True, "preflight": preflight}
    return await _execute_provider_run(db, provider, request, preflight)


@router.post("/providers/apify/preflight")
def apify_preflight(
    value: ProviderPreflightInput,
    db: Session = Depends(get_db),
    _: User = Depends(admin),
) -> dict[str, Any]:
    """Return the complete safety/cost envelope without making a network request."""

    provider = _provider()
    provider.monthly_spend_usd = _monthly_spend(db)
    request = _actor_request(provider, value)
    return {"executed": False, "confirmation_required": True, "preflight": provider.preflight(request)}


@router.post("/providers/apify/refresh")
async def apify_refresh(
    value: ProviderRefreshInput,
    db: Session = Depends(get_db),
    _: User = Depends(admin),
) -> dict[str, Any]:
    provider = _provider()
    provider.monthly_spend_usd = _monthly_spend(db)
    urls = [str(url) for url in value.video_urls]
    request = provider.direct_refresh_request(urls, market=value.market)
    preflight = provider.preflight(request)
    if not value.confirm_live_run:
        return {"executed": False, "confirmation_required": True, "preflight": preflight}
    return await _execute_provider_run(db, provider, request, preflight)


@router.get("/providers/apify/runs")
def apify_runs(db: Session = Depends(get_db), _: User = Depends(admin)) -> list[dict[str, Any]]:
    runs = db.scalars(
        select(ProviderRun)
        .where(ProviderRun.provider.like("apify:%"))
        .order_by(ProviderRun.started_at.desc())
        .limit(100)
    ).all()
    return [_run_payload(run) for run in runs]


@router.get("/providers/apify/health")
def apify_health(db: Session = Depends(get_db), _: User = Depends(admin)) -> dict[str, Any]:
    # Deliberately config-only: the health endpoint never starts an Actor or incurs a run charge.
    provider = _provider()
    return {**provider.health_check(), "data_state": provider_context(db)["provider"]}


@router.get("/providers/apify/costs")
def apify_costs(db: Session = Depends(get_db), _: User = Depends(admin)) -> dict[str, Any]:
    cfg = settings()
    spend = _monthly_spend(db)
    return {
        "currency": "USD",
        "monthly_budget": cfg.apify_monthly_budget_usd,
        "observed_monthly_spend": round(spend, 4),
        "remaining_budget": round(max(0.0, cfg.apify_monthly_budget_usd - spend), 4),
        "note": "Preflight estimates are planning values; maxTotalChargeUsd is the execution ceiling.",
    }


async def _execute_provider_run(
    db: Session,
    provider: ApifyTikTokProvider,
    request: ActorRequest,
    preflight: dict[str, Any],
) -> dict[str, Any]:
    if not provider.enabled:
        raise HTTPException(409, "Live Apify collection is disabled or incomplete; no paid run was started")
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
        rows = await provider.collect(request)
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
        run.status = quality.get("status", "success")
        run.finished_at = utc_now()
        run.returned_records = int(quality.get("returned_records") or len(rows))
        run.accepted_records = int(quality.get("accepted_records") or len(rows))
        run.invalid_records = int(quality.get("invalid_records") or 0)
        run.duplicate_records = int(ingest_result.get("duplicates") or 0)
        run.missing_field_rate = (
            sum(len(row.missing_fields) for row in rows) / max(1, len(rows) * 5)
        )
        run.cost = quality.get("cost_usd")
        run.currency = quality.get("currency", "USD")
        fingerprints = quality.get("schema_fingerprints") or []
        run.schema_fingerprint = ",".join(fingerprints)[:128] if fingerprints else None
        run.quality = {"preflight": preflight, "ingest": ingest_result, "provider": quality}
        for record in quality.get("quarantine", []):
            db.add(
                ProviderQuarantine(
                    provider_run_id=run.id,
                    provider=run.provider,
                    external_record_id=record.get("external_record_id"),
                    reason_code=record.get("reason", "invalid_record"),
                    redacted_summary=redact_text(record.get("summary", "Invalid provider record"), [settings().apify_token.get_secret_value()]),
                    schema_fingerprint=record.get("schema_fingerprint"),
                    missing_fields=record.get("missing_fields") or [],
                )
            )
        db.commit()
        return {"executed": True, "preflight": preflight, "run": _run_payload(run), "ingest": ingest_result}
    except ApifyProviderError as exc:
        db.rollback()
        run.status = "failed"
        run.finished_at = utc_now()
        run.error_category = exc.context.category
        run.error_summary = redact_text(exc, [settings().apify_token.get_secret_value()])
        db.commit()
        raise HTTPException(502, run.error_summary) from exc
    except Exception as exc:
        # Ingestion and persistence errors must also close the provider run.
        # Return a fixed, redacted summary so database details and secrets never
        # cross the API boundary.
        db.rollback()
        failed_run = db.get(ProviderRun, run.id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.finished_at = utc_now()
            failed_run.error_category = "internal_ingestion_error"
            failed_run.error_summary = (
                "The provider returned, but SignalScope could not safely persist the run."
            )
            db.commit()
        raise HTTPException(
            500,
            "The provider run stopped because its results could not be safely persisted.",
        ) from exc


def _run_payload(run: ProviderRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "provider": run.provider,
        "actor_id": run.actor_id,
        "actor_version": run.actor_version,
        "external_run_id": run.external_run_id,
        "dataset_id": run.dataset_id,
        "collection_type": run.collection_type,
        "market": run.market,
        "query_provenance": run.query_provenance,
        "status": run.status,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "returned_records": run.returned_records,
        "accepted_records": run.accepted_records,
        "duplicate_records": run.duplicate_records,
        "invalid_records": run.invalid_records,
        "missing_field_rate": run.missing_field_rate,
        "cost": run.cost,
        "currency": run.currency,
        "error_category": run.error_category,
        "error_summary": run.error_summary,
        "schema_fingerprint": run.schema_fingerprint,
    }


def _require_signal(db: Session, signal_id: int) -> ToySignal:
    signal = db.get(ToySignal, signal_id)
    if signal is None:
        raise HTTPException(404, "Toy signal not found")
    return signal


def _opportunity_for(db: Session, signal: ToySignal, user: User) -> Opportunity:
    user_key = _user_key(user)
    item = db.scalar(
        select(Opportunity)
        .where(
            Opportunity.source_signal_id == signal.id,
            Opportunity.user_key == user_key,
        )
        .order_by(Opportunity.updated_at.desc())
    )
    if item:
        return item
    now = utc_now()
    item = Opportunity(
        source_signal_id=signal.id,
        user_id=user.id,
        user_key=user_key,
        state="saved",
        decision=signal.recommended_decision,
        title=signal.title,
        rationale=signal.main_supporting_evidence,
        decision_window=_window(signal.lifecycle),
        mechanism=signal.content_mechanism,
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    db.flush()
    return item


def _since_last_review(signals: list[ToySignal]) -> list[dict[str, Any]]:
    # Review timestamps and prior signal states are not persisted yet. Current
    # counts are available elsewhere on Today, but they are not a historical
    # delta and must not be presented as one.
    return [
        {
            "type": "history",
            "label": "Insufficient history",
            "count": 0,
            "detail": (
                "No previous review checkpoint is stored. Current signal counts are "
                "shown below, but cannot be described as changes since your last review."
            ),
        }
    ]


def _window(lifecycle: str) -> str:
    return {
        "Breakout": "Decide within 24 hours",
        "Accelerating": "Review within 24 hours",
        "Emerging": "Review after the next observation",
        "Saturated": "Hold unless a materially original angle exists",
        "Declining": "Do not prioritise without new evidence",
    }.get(lifecycle, "Wait for additional observations")


def _lines(value: str | None) -> list[str]:
    return [line.strip(" -") for line in (value or "").splitlines() if line.strip(" -")]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
