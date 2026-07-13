from __future__ import annotations

from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import admin, current_user
from app.db import Base, get_db
from app.main import app
from app.models import DailyReport, SignalDecision, User
from app.providers.mock import MockProvider
from app.services.pipeline import ingest
from app.services.toy_intelligence import build_or_update_toy_signals


def _client() -> tuple[TestClient, Session, User]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine, expire_on_commit=False)
    user = User(
        email="toy-admin@example.test",
        password_hash="not-used",
        role="admin",
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    start = datetime(2026, 7, 13, 6)
    for run in range(4):
        ingest(db, MockProvider(run).discover_videos(24), start + timedelta(hours=run * 6))
    build_or_update_toy_signals(db, now=start + timedelta(hours=24))

    def database_override():
        yield db

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[current_user] = lambda: user
    app.dependency_overrides[admin] = lambda: user
    return TestClient(app), db, user


def test_toy_decision_brief_and_report_flow() -> None:
    client, db, user = _client()
    try:
        overview = client.get("/api/toys/overview")
        assert overview.status_code == 200
        assert overview.json()["mode_label"] == "DEMO TOY DATA"
        assert set(overview.json()["decision_queue"]) == {"act", "monitor", "avoid"}

        signals = client.get("/api/toys/signals")
        assert signals.status_code == 200
        assert signals.json()["items"]
        signal = signals.json()["items"][0]
        assert "evidence" in signal
        assert signal["demo"] is True
        assert signal["quality"]["coverage_limitations"]

        saved = client.post(
            f"/api/toys/signals/{signal['id']}/decision",
            json={"decision": "Monitor", "recommendation": "Monitor"},
        )
        assert saved.status_code == 200
        assert saved.json()["recommendation"] == "Monitor"
        decision = db.scalar(
            select(SignalDecision).where(
                SignalDecision.signal_id == int(signal["id"]),
                SignalDecision.user_key == str(user.id),
            )
        )
        assert decision is not None

        incomplete = client.post(
            f"/api/toys/signals/{signal['id']}/create-brief",
            json={"title": "Original test", "originality_checks": {}, "safety_checks": {}},
        )
        assert incomplete.status_code == 422

        brief = client.post(
            f"/api/toys/signals/{signal['id']}/create-brief",
            json={
                "title": "Original toy stress-test concept",
                "audience_need": "Help gift buyers compare durability.",
                "original_hook": "Which build survives a new three-part test?",
                "originality_checks": {"Original execution": True},
                "safety_checks": {"Safety and rights reviewed": True},
            },
        )
        assert brief.status_code == 200
        assert brief.json()["signal_id"] == signal["id"]

        report = client.post("/api/toys/reports", json={"market": "GB"})
        assert report.status_code == 200
        assert report.json()["limitations"]
        assert set(report.json()) >= {"act", "monitor", "avoid", "opportunities"}
        workbook = client.get(f"/api/reports/{report.json()['id']}/export.xlsx")
        assert workbook.status_code == 200
        assert workbook.content.startswith(b"PK")
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_apify_preflight_never_executes_without_confirmation() -> None:
    client, db, _ = _client()
    try:
        result = client.post(
            "/api/providers/apify/discover",
            json={
                "collection_type": "keyword",
                "market": "GB",
                "values": ["viral toys"],
                "max_results": 5,
                "confirm_live_run": False,
            },
        )
        assert result.status_code == 200
        payload = result.json()
        assert payload["executed"] is False
        assert payload["confirmation_required"] is True
        assert payload["preflight"]["maximum_result_count"] == 5
        assert payload["preflight"]["safety"]["media_downloads_disabled"] is True
        assert payload["preflight"]["safety"]["comments_disabled"] is True
        assert payload["preflight"]["token_in_url"] is False

        blocked = client.post(
            "/api/providers/apify/discover",
            json={
                "collection_type": "keyword",
                "market": "GB",
                "values": ["viral toys"],
                "max_results": 1,
                "confirm_live_run": True,
            },
        )
        assert blocked.status_code == 409
        assert "no paid run was started" in blocked.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_toy_reports_are_scoped_to_the_authenticated_user() -> None:
    client, db, first_user = _client()
    try:
        first = client.post("/api/toys/reports", json={})
        assert first.status_code == 200

        second_user = User(
            email="second-toy-user@example.test",
            password_hash="not-used",
            role="admin",
            active=True,
        )
        db.add(second_user)
        db.commit()
        db.refresh(second_user)
        app.dependency_overrides[current_user] = lambda: second_user
        app.dependency_overrides[admin] = lambda: second_user

        hidden = client.get("/api/toys/reports")
        assert hidden.status_code == 200
        assert hidden.json()["items"] == []
        forbidden_export = client.get(
            f"/api/reports/{first.json()['id']}/export.xlsx"
        )
        assert forbidden_export.status_code == 404

        second = client.post("/api/toys/reports", json={})
        assert second.status_code == 200
        assert second.json()["id"] != first.json()["id"]
        reports = db.scalars(select(DailyReport)).all()
        assert {report.user_key for report in reports} == {
            str(first_user.id),
            str(second_user.id),
        }
    finally:
        app.dependency_overrides.clear()
        db.close()
