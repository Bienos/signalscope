from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.toys import refresh_offsets_hours
from app.models import Opportunity, SignalVideoEvidence, Snapshot, ToySignal, Video
from app.services.toy_intelligence import signal_evidence_identity

MAX_DUE_REFRESH_URLS = 20
TERMINAL_AVAILABILITY_STATES = frozenset({"deleted", "private", "unavailable"})
SAVED_OPPORTUNITY_STATES = frozenset(
    {"saved", "selected", "draft", "brief", "approved"}
)
CANDIDATE_LIFECYCLES = frozenset(
    {"Emerging", "Accelerating", "Breakout", "Viral", "Recurring"}
)


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _canonical_tiktok_url(value: str) -> bool:
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").casefold()
    path_parts = [part for part in parsed.path.split("/") if part]
    return bool(
        parsed.scheme == "https"
        and (hostname == "tiktok.com" or hostname.endswith(".tiktok.com"))
        and "video" in path_parts
        and path_parts[-1].isdigit()
    )


@dataclass(frozen=True)
class DueRefreshItem:
    video_id: int
    signal_id: int
    canonical_url: str
    market: str
    lifecycle: str
    opportunity_score: float
    saved: bool
    availability: str
    terminal_confirmation: bool
    policy_offset_hours: int
    due_at: datetime
    last_observed_at: datetime | None
    reason: str

    def payload(self) -> dict[str, object]:
        value = asdict(self)
        value["due_at"] = self.due_at.isoformat()
        value["last_observed_at"] = (
            self.last_observed_at.isoformat() if self.last_observed_at else None
        )
        return value


@dataclass(frozen=True)
class DueRefreshPlan:
    generated_at: datetime
    requested_limit: int
    applied_limit: int
    due_count: int
    omitted_due_count: int
    selected: tuple[DueRefreshItem, ...]
    skipped: dict[str, int]

    def payload(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "requested_limit": self.requested_limit,
            "applied_limit": self.applied_limit,
            "hard_limit": MAX_DUE_REFRESH_URLS,
            "due_count": self.due_count,
            "selected_count": len(self.selected),
            "omitted_due_count": self.omitted_due_count,
            "selected": [item.payload() for item in self.selected],
            "skipped": self.skipped,
            "read_only": True,
            "paid_run_started": False,
        }


def plan_due_video_refreshes(
    db: Session,
    *,
    now: datetime | None = None,
    limit: int = MAX_DUE_REFRESH_URLS,
) -> DueRefreshPlan:
    """Select a bounded direct-refresh plan without mutating state or calling a provider.

    Only non-demo evidence is eligible. Candidate signals use the bounded domain
    schedule; saturated/declining evidence is included only when explicitly saved.
    Two consecutive terminal observations stop monitoring after the required single
    confirmation.
    """

    if limit < 1:
        raise ValueError("Refresh planning limit must be at least 1")
    generated_at = _utc_naive(now or datetime.now(UTC))
    applied_limit = min(limit, MAX_DUE_REFRESH_URLS)
    skipped = {
        "demo_or_mixed_evidence": 0,
        "not_candidate_or_saved": 0,
        "invalid_canonical_url": 0,
        "terminal_confirmed": 0,
        "schedule_complete": 0,
        "not_due": 0,
    }

    opportunities = db.scalars(select(Opportunity)).all()
    saved_at: dict[int, datetime] = {}
    for opportunity in opportunities:
        saved = (
            opportunity.state.casefold() in SAVED_OPPORTUNITY_STATES
            or opportunity.include_in_report
        )
        if not saved:
            continue
        existing = saved_at.get(opportunity.source_signal_id)
        observed = _utc_naive(opportunity.created_at)
        if existing is None or observed < existing:
            saved_at[opportunity.source_signal_id] = observed

    due: list[DueRefreshItem] = []
    signals = db.scalars(
        select(ToySignal).order_by(ToySignal.opportunity_score.desc(), ToySignal.id)
    ).all()
    for signal in signals:
        evidence_mode, _providers = signal_evidence_identity(db, signal)
        if evidence_mode != "live":
            skipped["demo_or_mixed_evidence"] += 1
            continue
        is_saved = signal.id in saved_at
        is_candidate = (
            signal.lifecycle in CANDIDATE_LIFECYCLES
            or signal.opportunity_score >= 50
        )
        if not is_saved and not is_candidate:
            skipped["not_candidate_or_saved"] += 1
            continue

        memberships = db.scalars(
            select(SignalVideoEvidence).where(
                SignalVideoEvidence.signal_id == signal.id
            )
        ).all()
        for membership in memberships:
            video = db.get(Video, membership.video_id)
            if video is None or not _canonical_tiktok_url(video.url):
                skipped["invalid_canonical_url"] += 1
                continue
            snapshots = db.scalars(
                select(Snapshot)
                .where(
                    Snapshot.video_id == video.id,
                    Snapshot.source == video.provider,
                )
                .order_by(Snapshot.collected_at)
            ).all()
            latest_snapshot = snapshots[-1] if snapshots else None
            availability = (
                latest_snapshot.availability_state
                if latest_snapshot
                else video.availability_status
            ).casefold()
            terminal = availability in TERMINAL_AVAILABILITY_STATES
            terminal_confirmed = bool(
                terminal
                and len(snapshots) >= 2
                and snapshots[-2].availability_state.casefold()
                in TERMINAL_AVAILABILITY_STATES
            )
            if terminal_confirmed:
                skipped["terminal_confirmed"] += 1
                continue

            offsets = refresh_offsets_hours(
                lifecycle=signal.lifecycle,
                opportunity_score=signal.opportunity_score,
                saved=is_saved,
                availability=availability,
                terminal_confirmed=terminal_confirmed,
            )
            if not offsets:
                skipped["schedule_complete"] += 1
                continue

            last_observed = (
                _utc_naive(latest_snapshot.collected_at)
                if latest_snapshot
                else video.last_observed_at
            )
            if terminal:
                anchor = last_observed or _utc_naive(video.first_observed_at or signal.created_at)
                policy_offset = offsets[0]
                due_at = anchor + timedelta(hours=policy_offset)
                reason = "Confirm the observed terminal state once, then stop monitoring."
                terminal_confirmation = True
            else:
                video_anchor = _utc_naive(
                    video.first_observed_at or signal.first_detected_at
                )
                selection_anchor = saved_at.get(signal.id, video_anchor)
                anchor = max(video_anchor, selection_anchor)
                observations_after_selection = [
                    snapshot
                    for snapshot in snapshots
                    if _utc_naive(snapshot.collected_at) >= anchor
                ]
                completed_followups = max(0, len(observations_after_selection) - 1)
                if completed_followups >= len(offsets):
                    skipped["schedule_complete"] += 1
                    continue
                policy_offset = offsets[completed_followups]
                due_at = anchor + timedelta(hours=policy_offset)
                reason = (
                    "Saved evidence follows the bounded selected-video schedule."
                    if is_saved
                    else "Candidate evidence follows the bounded lifecycle schedule."
                )
                terminal_confirmation = False

            if due_at > generated_at:
                skipped["not_due"] += 1
                continue
            due.append(
                DueRefreshItem(
                    video_id=video.id,
                    signal_id=signal.id,
                    canonical_url=video.url,
                    market=(video.collection_market or video.market).upper(),
                    lifecycle=signal.lifecycle,
                    opportunity_score=round(signal.opportunity_score, 1),
                    saved=is_saved,
                    availability=availability,
                    terminal_confirmation=terminal_confirmation,
                    policy_offset_hours=policy_offset,
                    due_at=due_at,
                    last_observed_at=last_observed,
                    reason=reason,
                )
            )

    due.sort(
        key=lambda item: (
            not item.terminal_confirmation,
            not item.saved,
            item.due_at,
            -item.opportunity_score,
            item.video_id,
        )
    )
    selected = tuple(due[:applied_limit])
    return DueRefreshPlan(
        generated_at=generated_at,
        requested_limit=limit,
        applied_limit=applied_limit,
        due_count=len(due),
        omitted_due_count=max(0, len(due) - len(selected)),
        selected=selected,
        skipped=skipped,
    )
