from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.auth import admin, current_user, token
from app.config import settings
from app.db import get_db
from app.models import Creator, DailyReport, DeletionRequest, ProviderRun, Snapshot, Sound, TrendCluster, User, Video, ViralScore
from app.providers.imports import parse_csv,parse_json
from app.services.pipeline import ingest,make_report,score_all
from app.services.report_exports import full_csv, full_html
from app.services.report_workbook import report_xlsx
from app.services.eligibility import emerging_eligibility
from app.services.entitlements import ADD_ON_FEATURES,PLAN_QUOTAS,resolve_entitlements
router=APIRouter(prefix="/api"); hashing=PasswordHash.recommended()
@router.post("/auth/token")
def login(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==form.username))
    if not u or not hashing.verify(form.password,u.password_hash): raise HTTPException(401,"Incorrect email or password")
    return {"access_token":token(u),"token_type":"bearer","role":u.role}
@router.get("/overview")
def overview(db:Session=Depends(get_db),_=Depends(current_user)):
    total=db.scalar(select(func.count()).select_from(Video).where(Video.removed==False)) or 0;latest=db.scalar(select(func.max(Snapshot.collected_at)));provider_freshness=db.scalar(select(func.max(Snapshot.freshness_at)));report=db.scalar(select(DailyReport).order_by(DailyReport.created_at.desc()))
    metadata=(report.payload or {}).get("metadata",{}) if report else {}
    if report is None or metadata.get("report_schema_version")!="2.0" or metadata.get("safety_rule_version")!="2.0":report=make_report(db)
    return {"videos":total,"creators":db.scalar(select(func.count()).select_from(Creator)) or 0,"collection_time":latest,"provider_freshness":provider_freshness,"provider":"MockProvider","data_mode":"Demo","coverage_warning":"Demo data. Coverage is not exhaustive; observed within the monitored sample.","signals":report.payload["executive"] if report else {}}
@router.get("/commercial/catalog")
def commercial_catalog(plan:str="free",addons:str="",_=Depends(current_user)):
    result=resolve_entitlements(plan,[x for x in addons.split(",") if x]);result["available_addons"]=sorted(ADD_ON_FEATURES);result["all_plan_quotas"]=PLAN_QUOTAS;result["billing"]="Not connected";return result
@router.get("/videos")
def videos(category:str|None=None,market:str|None=None,language:str|None=None,emerging:bool=False,state:str|None=None,q:str|None=None,limit:int=50,db:Session=Depends(get_db),_=Depends(current_user)):
    selected_state="emerging" if emerging else state if state in {"viral","emerging","all"} else "all"
    stmt=select(Video,ViralScore,Creator).join(ViralScore,Video.id==ViralScore.video_id).join(Creator).where(Video.removed==False)
    if category: stmt=stmt.where(Video.category==category)
    if market: stmt=stmt.where(Video.market==market)
    if language: stmt=stmt.where(Video.language==language)
    if q: stmt=stmt.where(or_(Video.caption.ilike(f"%{q}%"),Creator.username.ilike(f"%{q}%")))
    stmt=stmt.order_by((ViralScore.evs if selected_state=="emerging" else ViralScore.adjusted).desc()).limit(100)
    result=[]
    for v,s,c in db.execute(stmt):
        eligibility=emerging_eligibility(db,v,s)
        if selected_state=="emerging" and not eligibility["eligible"]:continue
        latest=db.scalar(select(Snapshot).where(Snapshot.video_id==v.id).order_by(Snapshot.collected_at.desc()))
        if selected_state=="viral" and (s.adjusted<settings().min_high_performance_avs or not latest or latest.views<settings().min_high_performance_views or eligibility["eligible"]):continue
        result.append({"id":v.id,"url":v.url,"creator":c.username,"caption":v.caption,"hashtags":v.hashtags,"published_at":v.published_at,"video_age_hours":eligibility["video_age_hours"],"snapshot_count":eligibility["snapshot_count"],"current_views":latest.views if latest else None,"market":v.market,"language":v.language,"category":v.category,"product_category":v.product_category,"safety":v.safety_status,"provider":v.provider,"evidence_type":"Demo" if v.provider=="mock" else "Provider reported","score":s.evs if selected_state=="emerging" else s.adjusted,"score_type":"EVS" if selected_state=="emerging" else "AVS","score_context":"Possible emerging" if selected_state=="emerging" else "High-performing in sample" if selected_state=="viral" else "Anomaly-adjusted performance","avs":s.avs,"evs":s.evs,"nps":s.nps,"growth":s.views_growth,"velocity":s.views_per_hour,"acceleration":s.acceleration,"anomaly":s.anomaly,"confidence":s.confidence,"confidence_score":s.confidence_score,"cohort":s.cohort,"score_components":s.components,"eligibility":eligibility,"reason":s.reason,"copyright_warning":"Use the broad mechanism only; do not copy protected execution.","last_retrieval":latest.collected_at if latest else None,"provider_freshness":latest.freshness_at if latest else None})
        if len(result)>=min(limit,100):break
    return result
@router.get("/{resource}")
def resources(resource:str,db:Session=Depends(get_db),_=Depends(current_user)):
    if resource=="creators":
        rows=[]
        for x in db.scalars(select(Creator).where(Creator.removed==False).limit(100)):
            scores=db.scalars(select(ViralScore).join(Video).where(Video.creator_id==x.id).order_by(ViralScore.views_per_hour.desc())).all()
            baseline=round(sum(s.views_per_hour for s in scores)/len(scores)) if scores else 0
            rows.append({"username":x.username,"niche":x.niche,"region":x.region,"followers":x.followers,"evidence_type":"Simulated baseline" if x.provider_id.startswith("creator-") else "Provider reported","partnership_suitability":"Not eligible" if x.apparent_minor else "Human review required","baseline_velocity":baseline,"posts_observed":len(scores),"median_engagement_rate":round(6.2+(x.id%9)*.35,1),"audience_fit":"Demo: family/creator interest proxy","shop_signal":"Demo: product mention observed" if x.id%3==0 else "Demo: not observed"})
        return rows
    if resource=="sounds":
        return [{"id":x.provider_id,"title":x.title,"growth":round(8+(x.id%8)*7.4,1),"lifecycle":["Emerging","Accelerating","Peaking","Stable"][x.id%4],"commercial_use":"Demo: review required","evidence_type":"Simulated 7-day history","history":[max(1,round((12+x.id%7)*(1+i*(.08+(x.id%4)*.04)))) for i in range(7)],"creators_using":3+x.id%14} for x in db.scalars(select(Sound).limit(100))]
    if resource=="formats" or resource=="clusters": return [{"name":x.name,"category":x.category,"rfs":x.rfs,"unrelated_creators":x.creators,"description":x.description,"adaptation":x.adaptation,"ip_warning":"Adapt the mechanism, not protected expression."} for x in db.scalars(select(TrendCluster).limit(100))]
    if resource=="reports": return [{"id":x.id,"date":x.report_date,"status":x.status,"payload":x.payload} for x in db.scalars(select(DailyReport).order_by(DailyReport.created_at.desc()).limit(30))]
    if resource=="providers": return [{"provider":x.provider,"started_at":x.started_at,"status":x.status,"quality":x.quality,"error":x.error} for x in db.scalars(select(ProviderRun).order_by(ProviderRun.started_at.desc()).limit(30))]
    if resource=="provider-capabilities":
        return {"provider":"MockProvider","mode":"Demo","last_checked":datetime.utcnow(),"capabilities":[{"name":"Video metrics","status":"Simulated","fields":["views","likes","comments","shares","favourites"]},{"name":"Creator intelligence","status":"Simulated","fields":["followers","recent posts","comparable-post baseline","niche"]},{"name":"Trend history","status":"Simulated","fields":["hashtag adoption","sound adoption","lifecycle"]},{"name":"Commerce","status":"Partial demo","fields":["product mention proxy","shop signal proxy"]},{"name":"Audience insights","status":"Unavailable","fields":[]},{"name":"Media & music rights","status":"Unavailable","fields":[]}]}
    if resource=="hashtags":
        tags:dict[str,int]={};
        for v in db.scalars(select(Video)): 
            for t in v.hashtags: tags[t]=tags.get(t,0)+1
        return [{"name":k,"observed_videos":v,"growth":round(12+(i%6)*13.5,1),"lifecycle":["Emerging","Accelerating","Peaking","Stable"][i%4],"confidence":"Demo","evidence_type":"Simulated 7-day history","history":[max(1,round(v*(.35+j*(.09+(i%4)*.025)))) for j in range(7)],"creators_using":max(2,v//2),"commercial_note":"Simulated adoption curve—not platform-wide volume."} for i,(k,v) in enumerate(sorted(tags.items(),key=lambda x:-x[1]))]
    raise HTTPException(404,"Unknown resource")
@router.post("/imports")
async def imports(file:UploadFile=File(...),db:Session=Depends(get_db),_=Depends(current_user)):
    content=await file.read()
    if len(content)>10_000_000: raise HTTPException(413,"Import exceeds 10 MB")
    try: rows=parse_json(content) if (file.filename or "").endswith(".json") else parse_csv(content); result=ingest(db,rows); score_all(db); return result
    except (ValueError,UnicodeError) as e: raise HTTPException(422,str(e)) from e
@router.post("/reports/generate")
def generate(db:Session=Depends(get_db),_=Depends(current_user)): return {"id":make_report(db).id}
@router.get("/reports/{report_id}")
def report_detail(report_id:int,db:Session=Depends(get_db),_=Depends(current_user)):
    report=db.get(DailyReport,report_id)
    if not report: raise HTTPException(404,"Report not found")
    return {"id":report.id,"date":report.report_date,"status":report.status,"created_at":report.created_at,"payload":report.payload}
@router.post("/reports/{report_id}/review")
def review_report(report_id:int,useful:bool|None=None,note:str|None=None,db:Session=Depends(get_db),_=Depends(current_user)):
    report=db.get(DailyReport,report_id)
    if not report: raise HTTPException(404,"Report not found")
    payload=dict(report.payload or {}); review=dict(payload.get("review") or {"useful":None,"notes":[]})
    if useful is not None: review["useful"]=useful
    if note: review.setdefault("notes",[]).append({"text":note,"created_at":datetime.utcnow().isoformat()})
    payload["review"]=review; report.payload=payload; db.add(report); db.commit()
    return review
@router.get("/reports/{report_id}/export.{fmt}")
def export(report_id:int,fmt:str,db:Session=Depends(get_db),_=Depends(current_user)):
    r=db.get(DailyReport,report_id)
    if not r: raise HTTPException(404,"Report not found")
    if fmt=="html":
        return HTMLResponse(full_html(r.report_date,r.payload),headers={"Content-Disposition":f"attachment; filename=signalscope-{r.report_date}.html"})
    if fmt=="csv":
        content=full_csv(r.payload)
        return StreamingResponse(iter([content]),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename=signalscope-{r.report_date}-complete.csv"})
    if fmt=="xlsx":
        xlsx_content=report_xlsx(r.report_date,r.payload)
        return StreamingResponse(iter([xlsx_content]),media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":f"attachment; filename=signalscope-{r.report_date}.xlsx"})
    raise HTTPException(400,"Use html, csv or xlsx")
@router.post("/deletions")
def deletion(target:str,reason:str,db:Session=Depends(get_db),_=Depends(admin)):
    videos=db.scalars(select(Video).join(Creator).where(or_(Video.provider_id==target,Creator.username==target))).all()
    for v in videos: v.removed=True
    req=DeletionRequest(target=target,reason=reason,processed_at=datetime.utcnow(),result=f"removed {len(videos)} videos"); db.add(req); db.commit(); return {"result":req.result}
