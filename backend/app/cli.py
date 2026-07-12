import sys
from datetime import datetime,timedelta
from pathlib import Path
from sqlalchemy import select
from pwdlib import PasswordHash
from .db import Base,SessionLocal,engine
from .models import ProviderRun,TrendCluster,User
from .providers.mock import MockProvider
from .services.pipeline import ingest,make_report,score_all
def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(User).where(User.email=="admin@viralradar.local")): db.add(User(email="admin@viralradar.local",password_hash=PasswordHash.recommended().hash("RadarDemo!2026"),role="admin"))
        for run in range(4): ingest(db,MockProvider(run).discover_videos(),datetime.utcnow()-timedelta(hours=18-run*6))
        if not db.scalar(select(TrendCluster)):
            db.add_all([TrendCluster(name="Constraint comparison",category="toy",rfs=84,creators=8,description="Several unrelated creators compare products under a simple shared constraint.",adaptation="Create new tests, visuals, wording and audio around an original decision criterion."),TrendCluster(name="Three-stage reveal",category="general",rfs=77,creators=6,description="Premise, progressive evidence, concise payoff.",adaptation="Use an original setting and evidence sequence with cleared audio.")]);db.commit()
        score_all(db); make_report(db)
    print("Seeded deterministic demo data")
def collect():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        run=ProviderRun(provider="mock",started_at=datetime.utcnow(),status="running",quality={});db.add(run);db.commit()
        try:
            result=ingest(db,MockProvider(int(datetime.utcnow().timestamp()//21600)%20).discover_videos(),datetime.utcnow()); score_all(db);run.status="success";run.quality={**result,"query_success_rate":1,"missing_priority_metrics":0,"market_coverage":["PL","GB","US"],"language_coverage":["en","pl"]}
        except Exception as e: run.status="failed";run.error=str(e)
        db.commit()
    print(run.status)
def report():
    with SessionLocal() as db:r=make_report(db);Path("outputs").mkdir(exist_ok=True);Path(f"outputs/report-{r.report_date}.json").write_text(__import__('json').dumps(r.payload,indent=2));print(r.id)
if __name__=="__main__": {"seed":seed,"collect":collect,"score":lambda: score_all(SessionLocal()),"report":report}.get(sys.argv[1] if len(sys.argv)>1 else "",lambda:print("Use seed|collect|score|report"))()
