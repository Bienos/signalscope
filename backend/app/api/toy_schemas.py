from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


DecisionValue = Literal["Act", "Monitor", "Avoid"]
CollectionType = Literal["keyword", "hashtag", "profile", "direct_refresh"]


class DecisionInput(BaseModel):
    decision: DecisionValue
    # A quick queue action may be saved before an analyst adds the rationale.
    # Empty rationale remains visible as incomplete in report readiness.
    reason: str = Field(default="", max_length=1_000)
    recommendation: DecisionValue | None = None
    analyst_note: str | None = Field(default=None, max_length=4_000)
    review_date: date | None = None


class NoteInput(BaseModel):
    analyst_note: str = Field(min_length=1, max_length=4_000)


class SaveOpportunityInput(BaseModel):
    decision: DecisionValue | None = None
    title: str | None = Field(default=None, max_length=240)
    rationale: str | None = Field(default=None, max_length=4_000)
    client_context: str | None = Field(default=None, max_length=2_000)
    decision_window: str | None = Field(default=None, max_length=240)
    include_in_report: bool = False


class BriefInput(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    audience_need: str | None = Field(default=None, max_length=2_000)
    original_hook: str | None = Field(default=None, max_length=2_000)
    content_structure: str | None = Field(default=None, max_length=4_000)
    recommended_creator_type: str | None = Field(default=None, max_length=160)
    production_complexity: Literal["Low", "Medium", "High", "Unknown"] = "Unknown"
    elements_not_to_copy: str | None = Field(default=None, max_length=4_000)
    safety_considerations: str | None = Field(default=None, max_length=4_000)
    rights_considerations: str | None = Field(default=None, max_length=4_000)
    evidence_limitations: str | None = Field(default=None, max_length=4_000)
    originality_checks: dict[str, bool] = Field(default_factory=dict)
    safety_checks: dict[str, bool] = Field(default_factory=dict)

    @field_validator("originality_checks", "safety_checks")
    @classmethod
    def confirmations_must_be_boolean(cls, value: dict[str, bool]) -> dict[str, bool]:
        return {str(key): bool(checked) for key, checked in value.items()}


class ReportInput(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    market: Literal["GB", "PL"] | None = None
    language: Literal["en", "pl"] | None = None
    include_opportunity_ids: list[int] | None = None


class ProviderPreflightInput(BaseModel):
    collection_type: CollectionType
    market: Literal["GB", "PL"]
    values: list[str] = Field(min_length=1, max_length=50)
    max_results: int = Field(default=5, ge=1, le=50)
    latest_only: bool = True

    @field_validator("values")
    @classmethod
    def clean_values(cls, values: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not cleaned:
            raise ValueError("At least one non-empty discovery value is required")
        return cleaned


class ProviderExecutionInput(ProviderPreflightInput):
    confirm_live_run: bool = False


class ProviderRefreshInput(BaseModel):
    market: Literal["GB", "PL"]
    video_urls: list[HttpUrl] = Field(min_length=1, max_length=50)
    max_results: int = Field(default=5, ge=1, le=50)
    confirm_live_run: bool = False
