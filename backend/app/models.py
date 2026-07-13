from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utc_now() -> datetime:
    """Return a naive UTC value for the application's existing DateTime columns."""

    return datetime.now(UTC).replace(tzinfo=None)


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    kind: Mapped[str] = mapped_column(String(30))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ProviderRun(Base):
    __tablename__ = "provider_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(80), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    actor_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    external_run_id: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    collection_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    market: Mapped[str | None] = mapped_column(String(8), nullable=True)
    query_provenance: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    returned_records: Mapped[int] = mapped_column(Integer, default=0)
    accepted_records: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_records: Mapped[int] = mapped_column(Integer, default=0)
    invalid_records: Mapped[int] = mapped_column(Integer, default=0)
    missing_field_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    schema_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quality: Mapped[dict] = mapped_column(JSON, default=dict)
    error_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(100), unique=True)
    username: Mapped[str] = mapped_column(String(100), index=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # Legacy region is retained for compatibility. It is an account/provider field,
    # never an audience-geography field.
    region: Mapped[str] = mapped_column(String(8))
    account_region: Mapped[str | None] = mapped_column(String(8), nullable=True)
    followers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    niche: Mapped[str] = mapped_column(String(50))
    creator_type: Mapped[str] = mapped_column(String(80), default="Unknown")
    apparent_minor: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    provider: Mapped[str] = mapped_column(String(80), default="unknown")
    raw_reference: Mapped[str] = mapped_column(String(300), default="")
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    removed: Mapped[bool] = mapped_column(Boolean, default=False)


class Sound(Base):
    __tablename__ = "sounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(180))
    commercial_status: Mapped[str] = mapped_column(String(30), default="unknown")
    growth: Mapped[float] = mapped_column(Float, default=0)
    provider: Mapped[str] = mapped_column(String(80), default="unknown")
    raw_reference: Mapped[str] = mapped_column(String(300), default="")
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(100), unique=True)
    url: Mapped[str] = mapped_column(String(300))
    creator_id: Mapped[int] = mapped_column(ForeignKey("creators.id"), index=True)
    sound_id: Mapped[int | None] = mapped_column(ForeignKey("sounds.id"), nullable=True)
    provider_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("provider_runs.id"), nullable=True, index=True
    )
    caption: Mapped[str] = mapped_column(Text)
    hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    published_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    language: Mapped[str] = mapped_column(String(5))
    provider_language: Mapped[str | None] = mapped_column(String(12), nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(12), nullable=True)
    market: Mapped[str] = mapped_column(String(5))
    collection_market: Mapped[str | None] = mapped_column(String(8), nullable=True)
    category: Mapped[str] = mapped_column(String(50))
    product_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    toy_category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    content_mechanism: Mapped[str | None] = mapped_column(String(100), nullable=True)
    child_featured: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    safety_status: Mapped[str] = mapped_column(String(30), default="clear")
    safety_flags: Mapped[list[str]] = mapped_column(JSON, default=list)
    availability_status: Mapped[str] = mapped_column(String(30), default="available")
    discovery_query: Mapped[dict] = mapped_column(JSON, default=dict)
    provider: Mapped[str] = mapped_column(String(80))
    raw_reference: Mapped[str] = mapped_column(String(300), default="")
    schema_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    first_observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    removed: Mapped[bool] = mapped_column(Boolean, default=False)


class Snapshot(Base):
    __tablename__ = "video_snapshots"
    __table_args__ = (UniqueConstraint("video_id", "collected_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True)
    provider_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("provider_runs.id"), nullable=True, index=True
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime)
    freshness_at: Mapped[datetime] = mapped_column(DateTime)
    views: Mapped[int | None] = mapped_column(Integer, nullable=True)
    likes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    favourites: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creator_follower_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    availability_state: Mapped[str] = mapped_column(String(30), default="available")
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(80))


class ViralScore(Base):
    __tablename__ = "viral_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), unique=True)
    views_growth: Mapped[int] = mapped_column(Integer)
    views_per_hour: Mapped[float] = mapped_column(Float)
    acceleration: Mapped[float | None] = mapped_column(Float, nullable=True)
    avs: Mapped[float] = mapped_column(Float)
    evs: Mapped[float] = mapped_column(Float)
    nps: Mapped[float] = mapped_column(Float)
    anomaly: Mapped[float] = mapped_column(Float)
    adjusted: Mapped[float] = mapped_column(Float)
    confidence: Mapped[str] = mapped_column(String(10))
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    components: Mapped[dict] = mapped_column(JSON, default=dict)
    cohort: Mapped[dict] = mapped_column(JSON, default=dict)
    score_version: Mapped[str] = mapped_column(String(20), default="2.0")
    reason: Mapped[str] = mapped_column(Text)


class TrendCluster(Base):
    __tablename__ = "trend_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    rfs: Mapped[float] = mapped_column(Float)
    creators: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    adaptation: Mapped[str] = mapped_column(Text)


class ToySignal(Base):
    __tablename__ = "toy_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    stable_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(220))
    toy_category: Mapped[str] = mapped_column(String(100), index=True)
    content_mechanism: Mapped[str] = mapped_column(String(100), default="Unknown")
    lifecycle: Mapped[str] = mapped_column(String(40), default="Insufficient evidence", index=True)
    recommended_decision: Mapped[str] = mapped_column(String(20), default="Monitor")
    confidence: Mapped[str] = mapped_column(String(12), default="Low")
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    first_detected_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_calculated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    data_freshness_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    unique_creators: Mapped[int] = mapped_column(Integer, default=0)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    cohort_size: Mapped[int] = mapped_column(Integer, default=0)
    markets: Mapped[list[str]] = mapped_column(JSON, default=list)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    related_hashtags: Mapped[list[str]] = mapped_column(JSON, default=list)
    related_sounds: Mapped[list[str]] = mapped_column(JSON, default=list)
    saturation: Mapped[str] = mapped_column(String(20), default="Low")
    saturation_score: Mapped[float] = mapped_column(Float, default=0)
    opportunity_score: Mapped[float] = mapped_column(Float, default=0)
    main_supporting_evidence: Mapped[str] = mapped_column(Text, default="")
    main_contradictory_evidence: Mapped[str] = mapped_column(Text, default="")
    safety_state: Mapped[str] = mapped_column(String(30), default="Unknown")
    explanation: Mapped[str] = mapped_column(Text, default="")
    components: Mapped[dict] = mapped_column(JSON, default=dict)
    missing_components: Mapped[list[str]] = mapped_column(JSON, default=list)
    score_version: Mapped[str] = mapped_column(String(20), default="toy-1.0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class SignalVideoEvidence(Base):
    __tablename__ = "signal_video_evidence"
    __table_args__ = (UniqueConstraint("signal_id", "video_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("toy_signals.id"), index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(40), default="supporting")
    supporting: Mapped[bool] = mapped_column(Boolean, default=True)
    weight: Mapped[float] = mapped_column(Float, default=1)
    rationale: Mapped[str] = mapped_column(Text, default="")
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class SignalDecision(Base):
    __tablename__ = "signal_decisions"
    __table_args__ = (UniqueConstraint("signal_id", "user_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_id: Mapped[int] = mapped_column(ForeignKey("toy_signals.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_key: Mapped[str] = mapped_column(String(80), default="single-user")
    decision: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str] = mapped_column(Text, default="")
    analyst_note: Mapped[str] = mapped_column(Text, default="")
    review_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_signal_id: Mapped[int] = mapped_column(ForeignKey("toy_signals.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_key: Mapped[str] = mapped_column(String(80), default="single-user")
    state: Mapped[str] = mapped_column(String(30), default="saved")
    decision: Mapped[str] = mapped_column(String(20), default="Monitor")
    title: Mapped[str] = mapped_column(String(220))
    rationale: Mapped[str] = mapped_column(Text, default="")
    analyst_note: Mapped[str] = mapped_column(Text, default="")
    client_context: Mapped[str] = mapped_column(Text, default="")
    decision_window: Mapped[str] = mapped_column(String(120), default="")
    mechanism: Mapped[str] = mapped_column(String(100), default="")
    adaptation_notes: Mapped[str] = mapped_column(Text, default="")
    audience_need: Mapped[str] = mapped_column(Text, default="")
    original_hook: Mapped[str] = mapped_column(Text, default="")
    content_structure: Mapped[str] = mapped_column(Text, default="")
    recommended_creator_type: Mapped[str] = mapped_column(String(100), default="Unknown")
    production_complexity: Mapped[str] = mapped_column(String(40), default="Unknown")
    elements_not_to_copy: Mapped[list[str]] = mapped_column(JSON, default=list)
    safety_considerations: Mapped[list[str]] = mapped_column(JSON, default=list)
    rights_considerations: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    originality_checks: Mapped[dict] = mapped_column(JSON, default=dict)
    safety_checks: Mapped[dict] = mapped_column(JSON, default=dict)
    rights_note: Mapped[str] = mapped_column(Text, default="")
    brief_status: Mapped[str] = mapped_column(String(30), default="draft")
    review_status: Mapped[str] = mapped_column(String(30), default="pending")
    include_in_report: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Watchlist(Base):
    __tablename__ = "watchlists"
    __table_args__ = (UniqueConstraint("user_key", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    user_key: Mapped[str] = mapped_column(String(80), default="single-user")
    name: Mapped[str] = mapped_column(String(160))
    objective: Mapped[str] = mapped_column(Text, default="")
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    markets: Mapped[list[str]] = mapped_column(JSON, default=list)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    data_status: Mapped[str] = mapped_column(String(30), default="demo")
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ProviderQuarantine(Base):
    __tablename__ = "provider_quarantine"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("provider_runs.id"), nullable=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(80), index=True)
    external_record_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    reason_code: Mapped[str] = mapped_column(String(80))
    redacted_summary: Mapped[str] = mapped_column(Text, default="")
    raw_reference: Mapped[str] = mapped_column(String(300), default="")
    schema_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    missing_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    quarantined_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)


class DailyReport(Base):
    __tablename__ = "daily_reports"
    __table_args__ = (
        UniqueConstraint("report_date", "user_key", name="uq_daily_report_date_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    report_date: Mapped[str] = mapped_column(String(10), index=True)
    user_key: Mapped[str] = mapped_column(String(80), default="single-user", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="published")


class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    target: Mapped[str] = mapped_column(String(150))
    reason: Mapped[str] = mapped_column(Text)
    processed_at: Mapped[datetime] = mapped_column(DateTime)
    result: Mapped[str] = mapped_column(String(80))


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(180), unique=True)
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
