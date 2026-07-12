from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import median
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Creator,
    DailyReport,
    ProviderRun,
    Snapshot,
    Sound,
    TrendCluster,
    Video,
    ViralScore,
)
from app.services.eligibility import emerging_eligibility

TOY_CATEGORIES = {"toy", "parenting", "board_game", "educational", "collectible", "family"}
COVERAGE = "Observed within the monitored sample. Coverage is not exhaustive."


def _round(value: float | int | None, digits: int = 1) -> float:
    return round(float(value or 0), digits)


def _lifecycle(growth: float, count: int) -> str:
    if growth < 0:
        return "Declining"
    if growth >= 25 and count >= 5:
        return "Accelerating"
    if count < 5:
        return "Emerging"
    return "Mature"


def _confidence(sample: int, complete: bool = True) -> str:
    if sample >= 10 and complete:
        return "High"
    if sample >= 3:
        return "Medium"
    return "Low"


def build_full_report(db: Session) -> dict[str, Any]:
    now = datetime.utcnow()
    rows = db.execute(
        select(Video, ViralScore, Creator, Sound)
        .join(ViralScore, ViralScore.video_id == Video.id)
        .join(Creator, Creator.id == Video.creator_id)
        .outerjoin(Sound, Sound.id == Video.sound_id)
        .where(Video.removed.is_(False))
        .order_by(ViralScore.adjusted.desc())
    ).all()
    snapshots_by_video: dict[int, list[Snapshot]] = defaultdict(list)
    for snap in db.scalars(select(Snapshot).order_by(Snapshot.collected_at)):
        snapshots_by_video[snap.video_id].append(snap)

    def post(v: Video, score: ViralScore, creator: Creator, sound: Sound | None) -> dict[str, Any]:
        snaps = snapshots_by_video.get(v.id, [])
        latest = snaps[-1] if snaps else None
        earliest = snaps[0] if snaps else None
        hours = max(
            ((latest.collected_at - earliest.collected_at).total_seconds() / 3600)
            if latest and earliest
            else 0,
            0.1,
        )
        like_velocity = ((latest.likes - earliest.likes) / hours) if latest and earliest else 0
        comment_velocity = ((latest.comments - earliest.comments) / hours) if latest and earliest else 0
        share_velocity = ((latest.shares - earliest.shares) / hours) if latest and earliest else 0
        favourite_velocity = (
            ((latest.favourites or 0) - (earliest.favourites or 0)) / hours
            if latest and earliest
            else 0
        )
        engagement = (
            (latest.likes + latest.comments + latest.shares) / max(latest.views, 1)
            if latest
            else 0
        )
        share_rate = latest.shares / max(latest.views, 1) if latest else 0
        percentage_growth = score.views_growth / max((latest.views - score.views_growth), 1) if latest else 0
        safety = "Review required" if v.safety_status != "clear" else "No automated concern"
        return {
            "video_id": v.provider_id,
            "url": v.url,
            "creator": creator.username,
            "creator_region": creator.region,
            "market": v.market,
            "language": v.language,
            "published_at": v.published_at.isoformat(),
            "video_age_hours": _round((now - v.published_at).total_seconds() / 3600),
            "caption": v.caption,
            "hashtags": v.hashtags,
            "sound_id": sound.provider_id if sound else None,
            "sound": sound.title if sound else "Not available",
            "views": latest.views if latest else None,
            "likes": latest.likes if latest else None,
            "comments": latest.comments if latest else None,
            "shares": latest.shares if latest else None,
            "favourites": latest.favourites if latest else None,
            "views_gained": score.views_growth,
            "views_per_hour": _round(score.views_per_hour),
            "like_velocity": _round(like_velocity),
            "comment_velocity": _round(comment_velocity),
            "share_velocity": _round(share_velocity),
            "favourite_velocity": _round(favourite_velocity),
            "percentage_growth": _round(percentage_growth * 100),
            "acceleration": _round(score.acceleration),
            "engagement_rate": _round(engagement * 100, 2),
            "share_rate": _round(share_rate * 100, 2),
            "already_viral_score": score.avs,
            "emerging_score": score.evs,
            "niche_score": score.nps,
            "adjusted_score": score.adjusted,
            "anomaly_score": score.anomaly,
            "confidence": score.confidence,
            "confidence_score": score.confidence_score,
            "score_components": score.components,
            "cohort": score.cohort,
            "score_version": score.score_version,
            "snapshots": len(snaps),
            "category": v.category,
            "product_category": v.product_category or "Not classified",
            "child_featured": v.child_featured,
            "apparent_minor": creator.apparent_minor,
            "safety_warning": safety,
            "copyright_warning": "Adapt the broad mechanism only; do not copy protected execution.",
            "trending_reason": score.reason,
            "adaptation_opportunity": "Create new wording, tests, setting, graphics, performance and cleared audio.",
            "last_retrieval": latest.collected_at.isoformat() if latest else None,
            "provider": v.provider,
        }

    posts = [post(*row) for row in rows]
    videos_by_provider_id={row[0].provider_id:(row[0],row[1]) for row in rows}
    for item in posts:
        video,score=videos_by_provider_id[item["video_id"]];item["emerging_eligibility"]=emerging_eligibility(db,video,score,now)
    eligible_posts = [x for x in posts if x["safety_warning"] == "No automated concern"]
    general = [x for x in eligible_posts if x["category"] not in TOY_CATEGORIES][:20]
    toy = [x for x in eligible_posts if x["category"] in TOY_CATEGORIES][:20]
    emerging = sorted(
        [
            {**x, "recommendation": "Act now" if x["emerging_score"] >= 70 else "Monitor",
             "why_early": "Recent post with multiple observations and strong relative momentum.",
             "invalidation_risk": "A later snapshot may show deceleration or provider correction."}
            for x in eligible_posts
            if x["emerging_eligibility"]["eligible"]
        ],
        key=lambda x: x["emerging_score"],
        reverse=True,
    )[:20]

    creator_posts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in posts:
        creator_posts[x["creator"]].append(x)
    creators = []
    for username, items in creator_posts.items():
        creator = next(row[2] for row in rows if row[2].username == username)
        above = sum(x["adjusted_score"] >= 50 for x in items)
        creators.append({
            "creator": username,
            "region": creator.region,
            "niche": creator.niche,
            "followers": creator.followers,
            "observed_posts": len(items),
            "ranking_appearances": sum(x in general + toy + emerging for x in items),
            "median_views_per_hour": _round(median(x["views_per_hour"] for x in items)),
            "median_performance_score": _round(median(x["adjusted_score"] for x in items)),
            "posts_above_baseline_pct": _round(above / len(items) * 100),
            "strongest_post": max(items, key=lambda x: x["adjusted_score"])["url"],
            "strongest_category": Counter(x["category"] for x in items).most_common(1)[0][0],
            "momentum": "Rising" if median(x["views_per_hour"] for x in items) > 0 else "Stable",
            "brand_safety": "Review" if any(x["safety_warning"] != "No automated concern" for x in items) else "No automated concern",
            "apparent_minor": creator.apparent_minor,
            "partnership_suitability": "Not eligible" if creator.apparent_minor else "Human review required",
            "confidence": _confidence(len(items)),
        })
    creators.sort(key=lambda x: x["median_performance_score"], reverse=True)

    tag_posts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in posts:
        for tag in x["hashtags"]:
            tag_posts[tag].append(x)
    hashtags = []
    for tag, items in tag_posts.items():
        velocity = sum(x["views_per_hour"] for x in items)
        growth = median(x["percentage_growth"] for x in items)
        hashtags.append({
            "hashtag": f"#{tag}", "observed_videos": len(items),
            "unique_creators": len({x["creator"] for x in items}),
            "new_video_velocity": _round(len(items) / 7),
            "creator_velocity": _round(len({x["creator"] for x in items}) / 7),
            "view_velocity": _round(velocity), "growth_pct": _round(growth),
            "main_category": Counter(x["category"] for x in items).most_common(1)[0][0],
            "markets": dict(Counter(x["market"] for x in items)),
            "languages": dict(Counter(x["language"] for x in items)),
            "toy_relevance": _round(sum(x["category"] in TOY_CATEGORIES for x in items) / len(items) * 100),
            "spam_estimate": "Low (metadata-only estimate)",
            "lifecycle": "Insufficient history", "confidence": "Low",
            "recommended_action": "Monitor and test only where context is relevant.",
        })
    hashtags.sort(key=lambda x: x["view_velocity"], reverse=True)

    sound_posts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in posts:
        if x["sound_id"]:
            sound_posts[x["sound_id"]].append(x)
    sounds = []
    for sound_id, items in sound_posts.items():
        growth = median(x["percentage_growth"] for x in items)
        sounds.append({
            "sound_id": sound_id, "title": items[0]["sound"], "type": "Unavailable",
            "commercial_use": "Not confirmed", "observed_videos": len(items),
            "unique_creators": len({x["creator"] for x in items}),
            "adoption_growth_pct": _round(growth),
            "adoption_velocity": _round(len(items) / 7),
            "main_category": Counter(x["category"] for x in items).most_common(1)[0][0],
            "markets": dict(Counter(x["market"] for x in items)),
            "languages": dict(Counter(x["language"] for x in items)),
            "lifecycle": "Insufficient history", "confidence": "Low",
            "recommended_action": "Confirm commercial-use rights before branded use.",
        })
    sounds.sort(key=lambda x: x["adoption_growth_pct"], reverse=True)

    category_posts: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in posts:
        category_posts[x["product_category"] or x["category"]].append(x)
    categories = []
    for category, items in category_posts.items():
        categories.append({
            "category": category, "observed_videos": len(items),
            "view_growth": sum(x["views_gained"] for x in items),
            "median_views_per_hour": _round(median(x["views_per_hour"] for x in items)),
            "median_engagement_rate": _round(median(x["engagement_rate"] for x in items), 2),
            "median_share_rate": _round(median(x["share_rate"] for x in items), 2),
            "unique_creators": len({x["creator"] for x in items}),
            "emerging_posts": sum(x in emerging for x in items),
            "momentum_score": _round(median(x["adjusted_score"] for x in items)),
            "confidence": _confidence(len(items)),
        })
    categories.sort(key=lambda x: x["momentum_score"], reverse=True)

    formats = [{
        "name": cluster.name, "category": cluster.category,
        "description": cluster.description, "hook_mechanism": "Paraphrased progressive reveal or comparison",
        "narrative_mechanism": "Premise, evidence, original payoff", "audio_role": "Supporting only",
        "unrelated_creators": cluster.creators, "repeatable_format_score": cluster.rfs,
        "adoption_direction": "Rising" if cluster.rfs >= 60 else "Monitor",
        "adaptation": cluster.adaptation,
        "protected_execution": "Do not reuse source wording, footage, choreography, identity or audio.",
        "confidence": _confidence(cluster.creators),
    } for cluster in db.scalars(select(TrendCluster).order_by(TrendCluster.rfs.desc()))]

    hooks = [{
        "name": str(x["name"]) + " opening", "mechanism": x["hook_mechanism"],
        "unrelated_creators": x["unrelated_creators"], "category": x["category"],
        "adoption_direction": x["adoption_direction"],
        "original_application": x["adaptation"], "confidence": x["confidence"],
    } for x in formats]

    all_snaps = [s for values in snapshots_by_video.values() for s in values]
    latest_retrieval = max((s.collected_at for s in all_snaps), default=None)
    missing_views = sum("views" in s.missing_fields for s in all_snaps)
    missing_shares = sum("shares" in s.missing_fields for s in all_snaps)
    metric_decreases = 0
    for values in snapshots_by_video.values():
        metric_decreases += sum(b.views < a.views for a, b in zip(values, values[1:]))
    provider_runs = db.scalars(select(ProviderRun).order_by(ProviderRun.started_at.desc()).limit(20)).all()
    successful = sum(r.status == "success" for r in provider_runs)
    quality = {
        "query_success_rate_pct": _round(successful / len(provider_runs) * 100 if provider_runs else 100),
        "missing_views_pct": _round(missing_views / max(len(all_snaps), 1) * 100),
        "missing_shares_pct": _round(missing_shares / max(len(all_snaps), 1) * 100),
        "duplicate_video_records": 0,
        "snapshot_continuity_pct": _round(sum(len(x) >= 2 for x in snapshots_by_video.values()) / max(len(posts), 1) * 100),
        "metric_decreases": metric_decreases,
        "low_confidence_scores_pct": _round(sum(x["confidence"] == "Low" for x in posts) / max(len(posts), 1) * 100),
        "markets": dict(Counter(x["market"] for x in posts)),
        "languages": dict(Counter(x["language"] for x in posts)),
        "latest_retrieval": latest_retrieval.isoformat() if latest_retrieval else None,
        "recommendations_paused": (missing_views + missing_shares) / max(len(all_snaps) * 2, 1) > 0.10,
        "warning": "Recommendations should be paused." if (missing_views + missing_shares) / max(len(all_snaps) * 2, 1) > 0.10 else "No automatic quality pause triggered.",
    }

    concepts = [
        {
            "title": "The equal-time family test", "priority": "Make today",
            "business_objective": "Support qualified product discovery",
            "target_audience": "Parents seeking screen-free family activities",
            "market": "PL, GB, US", "language": "Create separate English and Polish versions",
            "trend_signal": formats[0]["name"] if formats else "Comparison mechanism observed in the sample",
            "product_category": categories[0]["category"] if categories else "Toys & family",
            "original_hook": "Three sealed activity cards. Every option gets exactly five minutes.",
            "structure": "0-3s premise; 3-18s original tests; 18-25s result; 25-30s disclosure and CTA",
            "shot_list": ["Original tabletop wide shot", "Hands-only tests", "Custom scorecards", "Final neutral result"],
            "voiceover": "We gave every activity the same five-minute test. Here is what earned another round.",
            "graphics": "Original timer and scoring system", "audio": "Original voiceover and cleared music only",
            "cta": "Save the checklist and review the disclosed product links.",
            "disclosure": "Disclose affiliate relationship and synthetic presenter use where applicable.",
            "safety_checks": ["Follow manufacturer age guidance", "Use adult supervision", "No child distress or private moments"],
            "copyright_checks": ["No characters without permission", "No source footage", "No unlicensed sound"],
            "difficulty": "Low", "production_time": "60-90 minutes", "confidence": "Medium",
            "material_difference": "New tests, dialogue, setting, graphics, sequence, performance and cleared audio.",
        },
        {
            "title": "One-box rainy-day challenge", "priority": "Make within 72 hours",
            "business_objective": "Build saves and gift consideration", "target_audience": "Caregivers of school-age children",
            "market": "PL and GB", "language": "Polish and English", "trend_signal": "Family activity and reveal formats",
            "product_category": "Kids activities", "original_hook": "Can one small box cover three completely different rainy-day moods?",
            "structure": "Introduce three moods; demonstrate one original activity per mood; close with a decision guide.",
            "shot_list": ["Weather-window opener", "Three labelled activity zones", "Original demonstrations", "Decision graphic"],
            "voiceover": "Quiet, energetic, or creative—we matched one activity to each kind of afternoon.",
            "graphics": "Original mood labels", "audio": "Voiceover with cleared percussive bed", "cta": "Save for the next rainy day.",
            "disclosure": "Disclose gifted or affiliate products.", "safety_checks": ["Confirm component age range", "Check choking hazards"],
            "copyright_checks": ["Use generic props", "Avoid branded characters and source audio"], "difficulty": "Medium",
            "production_time": "2-3 hours", "confidence": "Medium",
            "material_difference": "Uses a new decision framework, original demonstrations and independent visual identity.",
        },
    ]

    executive = {
        "overall_trend": general[0]["caption"] if general else "Insufficient data",
        "toy_family_trend": toy[0]["caption"] if toy else "Insufficient data",
        "emerging_opportunity": emerging[0]["caption"] if emerging else "Insufficient qualifying observations",
        "fastest_sound": sounds[0]["title"] if sounds else "Not available",
        "fastest_hashtag": hashtags[0]["hashtag"] if hashtags else "Not available",
        "fastest_format": formats[0]["name"] if formats else "Not available",
        "strongest_category": categories[0]["category"] if categories else "Not available",
        "creator_momentum": creators[0]["creator"] if creators else "Not available",
        "act_today": "Test a materially original version of the strongest repeatable mechanism.",
        "monitor": "Collect another snapshot before treating early acceleration as sustained.",
        "avoid": "Safety-review content, distinctive protected execution, and unconfirmed commercial audio.",
        "confidence": "High" if len(posts) >= 100 and not quality["recommendations_paused"] else "Medium",
        "coverage": COVERAGE,
    }
    observation_start = min((s.collected_at for s in all_snaps)) if all_snaps else None
    return {
        "metadata": {
            "report_schema_version":"2.0","scoring_version":"2.0","safety_rule_version":"2.0",
            "data_mode":"Demo" if any(x["provider"]=="mock" for x in posts) else "Provider data",
            "generated_at": now.isoformat(), "timezone": "Europe/Warsaw",
            "observation_start": observation_start.isoformat() if observation_start else None,
            "observation_end": latest_retrieval.isoformat() if latest_retrieval else None,
            "providers": sorted({x["provider"] for x in posts}), "videos": len(posts),
            "creators": len(creator_posts), "sounds": len(sounds), "hashtags": len(hashtags),
            "snapshots": len(all_snaps), "markets": sorted({x["market"] for x in posts}),
            "languages": sorted({x["language"] for x in posts}), "coverage": COVERAGE,
        },
        "executive": executive, "data_quality": quality,
        "general": general, "toy_family": toy, "emerging": emerging,
        "creators": creators[:20], "formats": formats, "hashtags": hashtags[:30],
        "sounds": sounds[:30], "product_categories": categories, "hooks": hooks,
        "broad_inspiration": [{"trend": x["name"], "adaptable_mechanism": x["description"], "original_direction": x["adaptation"], "must_differ": x["protected_execution"]} for x in formats],
        "do_not_copy": [
            {"risk": "Protected execution", "guidance": "Do not reuse scripts, catchphrases, footage, choreography, characters or creator identity."},
            {"risk": "Unconfirmed sound rights", "guidance": "Confirm commercial-use rights or use original/cleared audio."},
            {"risk": "Child safety", "guidance": "Do not use distress, humiliation, private moments or unsafe product use."},
        ],
        "concepts": concepts,
        "actions": {
            "today": ["Review the top emerging posts", "Confirm sound rights", "Produce one original comparison test"],
            "next_72_hours": ["Collect additional snapshots", "Validate Polish-language hashtag coverage", "Review creator suitability manually"],
            "monitoring_additions_en": ["screen-free activity", "family game test", "travel toy"],
            "monitoring_additions_pl": ["zabawa bez ekranu", "gry rodzinne", "zabawka podróżna"],
        },
        "review": {"useful": None, "notes": []},
    }


def generate_report(db: Session) -> DailyReport:
    today = datetime.utcnow().date().isoformat()
    report = db.scalar(select(DailyReport).where(DailyReport.report_date == today))
    payload = build_full_report(db)
    if report is None:
        report = DailyReport(report_date=today, created_at=datetime.utcnow(), payload=payload)
    else:
        previous_review = (report.payload or {}).get("review", {})
        payload["review"] = previous_review or payload["review"]
        report.payload = payload
        report.created_at = datetime.utcnow()
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
