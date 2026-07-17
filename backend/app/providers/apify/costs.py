from __future__ import annotations

from dataclasses import asdict, dataclass

from .errors import ApifyBudgetError, ErrorContext
from .inputs import ActorRequest


ADVERTISED_PRICE_PER_1000_USD = {
    "clockworks~tiktok-scraper": 1.70,
    "clockworks~tiktok-profile-scraper": 1.00,
}


@dataclass(frozen=True)
class CostEstimate:
    actor_id: str
    collection_type: str
    maximum_result_count: int
    advertised_price_per_1000_usd: float | None
    estimated_result_cost_usd: float | None
    enforced_max_charge_usd: float
    monthly_budget_usd: float
    monthly_spend_usd: float
    remaining_monthly_budget_usd: float
    paid_input_features: tuple[str, ...]
    estimate_basis: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def estimate_cost(
    request: ActorRequest,
    *,
    monthly_budget_usd: float,
    monthly_spend_usd: float = 0,
    explicit_run_cap_usd: float | None = None,
) -> CostEstimate:
    remaining = round(max(0.0, monthly_budget_usd - monthly_spend_usd), 4)
    if remaining <= 0:
        raise ApifyBudgetError(
            "The configured monthly Apify budget has been exhausted",
            context=ErrorContext(category="monthly_budget_exhausted"),
        )
    unit_price = ADVERTISED_PRICE_PER_1000_USD.get(request.actor_id)
    result_estimate = (
        round(request.maximum_result_count * unit_price / 1000, 4)
        if unit_price is not None
        else None
    )
    # Actor pricing and paid input filters can change. The API-level maxTotalChargeUsd
    # remains the real ceiling; the catalogue price is only a planning estimate.
    buffered_estimate = max(0.05, (result_estimate or 0.05) * 1.25)
    requested_cap = (
        explicit_run_cap_usd if explicit_run_cap_usd is not None else buffered_estimate
    )
    if requested_cap <= 0:
        raise ApifyBudgetError(
            "The per-run Apify charge cap must be greater than zero",
            context=ErrorContext(category="invalid_run_cap"),
        )
    run_cap = round(min(remaining, requested_cap), 4)
    if run_cap <= 0:
        raise ApifyBudgetError(
            "No positive per-run Apify charge cap is available",
            context=ErrorContext(category="invalid_run_cap"),
        )
    return CostEstimate(
        actor_id=request.actor_id,
        collection_type=request.collection_type.value,
        maximum_result_count=request.maximum_result_count,
        advertised_price_per_1000_usd=unit_price,
        estimated_result_cost_usd=result_estimate,
        enforced_max_charge_usd=run_cap,
        monthly_budget_usd=round(monthly_budget_usd, 4),
        monthly_spend_usd=round(monthly_spend_usd, 4),
        remaining_monthly_budget_usd=remaining,
        paid_input_features=request.paid_input_features,
        estimate_basis=(
            "Advertised per-result price checked 2026-07-13; paid filters and pricing changes "
            "may alter actual cost. maxTotalChargeUsd is the enforced ceiling."
        ),
    )
