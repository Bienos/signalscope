from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitoringPolicy:
    """Bounded repeated-observation policy for selected canonical video URLs."""

    low_potential_hours: tuple[int, ...] = (24,)
    candidate_hours: tuple[int, ...] = (6, 24)
    strong_candidate_hours: tuple[int, ...] = (1, 6, 24, 72)
    terminal_confirmation_hours: tuple[int, ...] = (24,)


DEFAULT_MONITORING_POLICY = MonitoringPolicy()


def refresh_offsets_hours(
    *,
    lifecycle: str,
    opportunity_score: float | None,
    saved: bool = False,
    availability: str = "available",
    terminal_confirmed: bool = False,
    policy: MonitoringPolicy = DEFAULT_MONITORING_POLICY,
) -> tuple[int, ...]:
    """Return follow-up offsets without expanding discovery into full rescans.

    A caller must still pass the selected canonical URLs to the direct-refresh
    Actor input. This function never discovers or starts a provider job.
    """

    state = availability.casefold()
    if state in {"deleted", "private", "unavailable"}:
        return () if terminal_confirmed else policy.terminal_confirmation_hours
    if lifecycle in {"Saturated", "Declining"}:
        return policy.low_potential_hours if saved else ()
    if lifecycle in {"Breakout", "Accelerating"} and (
        opportunity_score is None or opportunity_score >= 70
    ):
        return policy.strong_candidate_hours
    if lifecycle in {"Emerging", "Viral"} or (
        opportunity_score is not None and opportunity_score >= 50
    ):
        return policy.candidate_hours
    return policy.low_potential_hours
