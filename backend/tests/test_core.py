from datetime import datetime,timedelta
from sqlalchemy import create_engine,select
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models import Snapshot,TrendCluster,Video,ViralScore
from app.providers.imports import parse_csv
from app.providers.mock import MockProvider
from app.services.pipeline import classify,ingest,make_report,score_all
from app.services.eligibility import emerging_eligibility
from app.services.report_exports import full_csv,full_html
from app.services.report_workbook import report_xlsx
from app.services.entitlements import resolve_entitlements
from app.api.routes import videos
def db():
    e=create_engine("sqlite://");Base.metadata.create_all(e);return sessionmaker(e)()
def test_import_headers():
    try:parse_csv(b"id,url\n1,x\n");assert False
    except ValueError as e:assert "Missing required headers" in str(e)
def test_classification_and_negative_filter():
    assert classify("best toy test",[])[0]=="toy";assert classify("dangerous challenge",[])[1]=="review"
def test_append_dedupe_and_scoring():
    d=db(); rows=MockProvider(0).discover_videos(8); t=datetime.utcnow()-timedelta(hours=6);ingest(d,rows,t);ingest(d,MockProvider(1).discover_videos(8),datetime.utcnow());assert d.query(Video).count()==8;assert d.query(Snapshot).count()==16;assert score_all(d)==8;s=d.scalars(select(ViralScore)).first();assert 0<=s.adjusted<=100;assert s.confidence in {"Low","Medium","High"};assert s.score_version=="2.0";assert "percentiles" in s.components;assert s.cohort["sample_size"]>=1
def test_decreasing_metric_anomaly():
    d=db(); rows=MockProvider(1).discover_videos(1);ingest(d,rows,datetime.utcnow()-timedelta(hours=2));rows[0].metrics["views"]=1;ingest(d,rows,datetime.utcnow());score_all(d);assert d.scalars(select(ViralScore)).first().anomaly>0
def test_complete_report_and_exports():
    d=db();
    for run in range(4): ingest(d,MockProvider(run).discover_videos(30),datetime.utcnow()-timedelta(hours=18-run*6))
    d.add(TrendCluster(name="Original comparison",category="toy",rfs=80,creators=5,description="Shared comparison mechanism",adaptation="Use new tests and original execution."));d.commit();score_all(d)
    report=make_report(d); required={"metadata","executive","data_quality","general","toy_family","emerging","creators","formats","hashtags","sounds","product_categories","hooks","concepts","actions","do_not_copy"};assert required<=set(report.payload);assert "section,record,field,value" in full_csv(report.payload);assert "SignalScope" in full_html(report.report_date,report.payload);assert report_xlsx(report.report_date,report.payload).startswith(b"PK");assert all(x.get("partnership_suitability")!="Eligible" for x in report.payload["creators"]);assert all(x["safety_warning"]=="No automated concern" for x in report.payload["emerging"])
def test_emerging_eligibility_rejects_unsafe_content():
    d=db();rows=MockProvider(0).discover_videos(2);t=datetime.utcnow()-timedelta(hours=6);ingest(d,rows,t);ingest(d,MockProvider(1).discover_videos(2),datetime.utcnow());score_all(d);video=d.scalar(select(Video).where(Video.provider_id=="mock-0000"));score=d.scalar(select(ViralScore).where(ViralScore.video_id==video.id));result=emerging_eligibility(d,video,score);assert not result["eligible"];assert "safety_clear" in result["failed_conditions"]
def test_commercial_entitlements_require_paid_base_for_addons():
    free=resolve_entitlements("free",["trend_depth_bundle"]);assert "hashtag_research" not in free["features"];assert free["quotas"]["monitors"]==1
    paid=resolve_entitlements("pro",["trend_depth_bundle"]);assert {"creator_intelligence","report_generation","hashtag_research","sound_intelligence"}<=set(paid["features"]);assert paid["quotas"]["monitors"]==5;assert paid["enforcement"]=="catalog_only_demo"
    team=resolve_entitlements("team");assert team["quotas"]["monitors"]==20
def test_discovery_states_use_distinct_explained_scores():
    d=db()
    for run in range(4):ingest(d,MockProvider(run).discover_videos(30),datetime.utcnow()-timedelta(hours=18-run*6))
    score_all(d)
    all_rows=videos(state="all",limit=100,db=d,_=None);high=videos(state="viral",limit=100,db=d,_=None);emerging=videos(state="emerging",limit=100,db=d,_=None)
    assert all_rows and all(x["score_type"]=="AVS" for x in all_rows)
    assert high and len(high)<len(all_rows) and all(x["score"]>=70 and x["current_views"]>=250_000 and x["score_context"]=="High-performing in sample" for x in high)
    assert all(x["score_type"]=="EVS" and x["score_context"]=="Possible emerging" for x in emerging)

