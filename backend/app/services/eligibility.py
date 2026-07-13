from __future__ import annotations
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Snapshot, Video, ViralScore

def emerging_eligibility(db:Session,video:Video,score:ViralScore,now:datetime|None=None)->dict:
    cfg=settings(); current=now or datetime.utcnow()
    snapshots=db.scalars(select(Snapshot).where(Snapshot.video_id==video.id).order_by(Snapshot.collected_at)).all()
    latest=snapshots[-1] if snapshots else None
    age=max(0,(current-video.published_at).total_seconds()/3600)
    checks={
        "age_within_limit":age<=cfg.emerging_max_age_hours,
        "enough_snapshots":len(snapshots)>=2,
        "below_viral_threshold":bool(latest and latest.views is not None and latest.views<cfg.viral_view_threshold),
        "minimum_growth":score.views_growth>=cfg.min_emerging_growth,
        "acceptable_anomaly":score.anomaly<=cfg.max_emerging_anomaly,
        "safety_clear":video.safety_status=="clear",
        "metrics_complete":not any(x in {"views","shares","published_at"} for x in video.missing_fields),
        "active":not video.removed,
    }
    return {"eligible":all(checks.values()),"checks":checks,"video_age_hours":round(age,1),"snapshot_count":len(snapshots),"current_views":latest.views if latest else None,"viral_threshold":cfg.viral_view_threshold,"view_growth":score.views_growth,"minimum_growth_required":cfg.min_emerging_growth,"anomaly_score":score.anomaly,"maximum_anomaly":cfg.max_emerging_anomaly,"safety_status":video.safety_status,"failed_conditions":[k for k,v in checks.items() if not v]}
