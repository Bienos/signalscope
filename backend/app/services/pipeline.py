from datetime import datetime
from math import log1p
from statistics import median
from collections import defaultdict
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Creator, Snapshot, Sound, Video, ViralScore
from app.providers.base import ProviderVideo
from app.services.reporting import generate_report

TOY={"toy","parenting","board_game","educational","collectible","family"}
UNSAFE=("niebezpieczne","dangerous challenge","choking","gambling","alcohol","medical cure")
def classify(text:str,hashtags:list[str])->tuple[str,str]:
    s=(text+" "+" ".join(hashtags)).lower()
    if any(x in s for x in UNSAFE): return "safety_review_required","review"
    if any(x in s for x in ("stem toy","educational toy","learning toy")): return "educational","clear"
    if any(x in s for x in ("collectible","blind box")): return "collectible","clear"
    if any(x in s for x in ("parent","family","rodzin","gift for kid","kids activ")): return "family","clear"
    if any(x in s for x in ("toy","zabawk","building set","construction set","sensory","plush","doll","action figure","outdoor play")): return "toy","clear"
    if any(x in s for x in ("board game","card game")): return "board_game","clear"
    return "general","clear"
def product_category(text:str,hashtags:list[str])->str|None:
    s=(text+" "+" ".join(hashtags)).lower()
    for terms,label in [
        (("stem","educational","learning toy"),"Educational & STEM toys"),
        (("sensory","fidget"),"Sensory toys"),
        (("collectible","blind box"),"Collectibles"),
        (("construction","building set","blocks"),"Construction toys"),
        (("plush","stuffed toy"),"Plush toys"),
        (("doll","action figure"),"Dolls & action figures"),
        (("outdoor toy","outdoor play"),"Outdoor toys"),
        (("parent","gift for kid","gift idea"),"Parent & gift-buyer content"),
        (("toy","zabawk"),"Children's toys"),
    ]:
        if any(term in s for term in terms): return label
    return None
def ingest(db:Session, rows:list[ProviderVideo], collected_at:datetime|None=None)->dict:
    now=collected_at or datetime.utcnow(); new=dupes=0
    for r in rows:
        creator=db.scalar(select(Creator).where(Creator.provider_id==r.creator_id))
        if not creator:
            creator=Creator(provider_id=r.creator_id,username=r.username,display_name=None,region=r.market if r.provider=="mock" else "ZZ",followers=5000+(hash(r.creator_id)%500000) if r.provider=="mock" else None,niche="toy" if classify(r.caption,r.hashtags)[0] in TOY else "general",apparent_minor=None); db.add(creator); db.flush()
        sound=None
        if r.sound_id:
            sound=db.scalar(select(Sound).where(Sound.provider_id==r.sound_id))
            if not sound: sound=Sound(provider_id=r.sound_id,title=r.sound_title or "Unknown",commercial_status="unknown",growth=0); db.add(sound); db.flush()
        video=db.scalar(select(Video).where(Video.provider_id==r.id))
        category,safety=classify(r.caption,r.hashtags)
        if not video:
            video=Video(provider_id=r.id,url=r.url,creator_id=creator.id,sound_id=sound.id if sound else None,caption=r.caption,hashtags=r.hashtags,published_at=r.published_at,language=r.language,market=r.market,category=category,product_category=product_category(r.caption,r.hashtags),child_featured=None,safety_status=safety,provider=r.provider,raw_reference=r.raw_reference,missing_fields=r.missing_fields); db.add(video); db.flush(); new+=1
        else:
            dupes+=1
            if not video.raw_reference and r.raw_reference: video.raw_reference=r.raw_reference
        if not db.scalar(select(Snapshot).where(Snapshot.video_id==video.id,Snapshot.collected_at==now)):
            m=r.metrics; db.add(Snapshot(video_id=video.id,collected_at=now,freshness_at=r.freshness_at,views=m.get("views"),likes=m.get("likes"),comments=m.get("comments"),shares=m.get("shares"),favourites=m.get("favourites"),missing_fields=r.missing_fields,source=r.provider))
    db.commit(); return {"new":new,"duplicates":dupes,"total":len(rows)}
def _pct(values:list[float],x:float)->float: return 100*sum(v<=x for v in values)/max(1,len(values))
def _observed(snapshot:Snapshot,field:str)->int:
    value=getattr(snapshot,field)
    if value is None: raise ValueError(f"Missing observed metric: {field}")
    return value
def _age_band(hours:float)->str:
    for limit,label in [(6,"0-6h"),(12,"6-12h"),(24,"12-24h"),(48,"24-48h"),(72,"48-72h"),(168,"3-7d"),(720,"7-30d")]:
        if hours<=limit:return label
    return "30d+"
def score_all(db:Session)->int:
    calculations:list[dict[str,Any]]=[];now=datetime.utcnow()
    for v in db.scalars(select(Video).where(Video.removed==False)).all():
        snapshots=db.scalars(select(Snapshot).where(Snapshot.video_id==v.id).order_by(Snapshot.collected_at)).all()
        ss=[s for s in snapshots if all(getattr(s,field) is not None for field in ("views","likes","comments","shares"))]
        if len(ss)<2: continue
        hours=max((ss[-1].collected_at-ss[0].collected_at).total_seconds()/3600,.1); growth=_observed(ss[-1],"views")-_observed(ss[0],"views"); velocity=growth/hours
        a=0.0
        if len(ss)>=3:
            h1=max((ss[-2].collected_at-ss[-3].collected_at).total_seconds()/3600,.1); h2=max((ss[-1].collected_at-ss[-2].collected_at).total_seconds()/3600,.1); a=(_observed(ss[-1],"views")-_observed(ss[-2],"views"))/h2-(_observed(ss[-2],"views")-_observed(ss[-3],"views"))/h1
        engagement=(_observed(ss[-1],"likes")+_observed(ss[-1],"comments")+_observed(ss[-1],"shares"))/max(_observed(ss[-1],"views"),1); share=_observed(ss[-1],"shares")/max(_observed(ss[-1],"views"),1); jump=70 if growth<0 or growth>max(_observed(ss[0],"views")*5,2_000_000) else 0
        share_velocity=(_observed(ss[-1],"shares")-_observed(ss[0],"shares"))/hours
        calculations.append({"video":v,"latest":ss[-1],"growth":growth,"velocity":velocity,"acceleration":a,"engagement":engagement,"share_rate":share,"share_velocity":share_velocity,"anomaly":jump,"snapshots":ss,"age_hours":max(0,(now-v.published_at).total_seconds()/3600)})
    if not calculations:return 0
    creator_velocities:dict[int,list[float]]=defaultdict(list)
    for x in calculations:creator_velocities[x["video"].creator_id].append(x["velocity"])
    spread_by_video={}
    for x in calculations:
        v=x["video"];peers={y["video"].creator_id for y in calculations if y["video"].sound_id==v.sound_id or bool(set(y["video"].hashtags)&set(v.hashtags))};spread_by_video[v.id]=len(peers)
    cohorts:dict[tuple,list[dict]]=defaultdict(list)
    for x in calculations:
        v=x["video"];key=(v.market,v.language,v.category,_age_band(x["age_hours"]));cohorts[key].append(x);x["cohort_key"]=key
    for x in calculations:
        v=x["video"];s=x["latest"];g=x["growth"];vel=x["velocity"];acc=x["acceleration"];eng=x["engagement"];shr=x["share_rate"];anom=x["anomaly"];ss=x["snapshots"];cohort=cohorts[x["cohort_key"]]
        creator_median=median(creator_velocities[v.creator_id]);baseline_lift=vel/max(creator_median,1)
        raw={"views":log1p(max(s.views,0)),"view_velocity":log1p(max(vel,0)),"share_rate":shr,"engagement_rate":eng,"acceleration":acc,"creator_baseline_lift":baseline_lift,"spread":spread_by_video[v.id],"percentage_growth":max(0,g/max(s.views-g,1)),"share_velocity":max(0,x["share_velocity"]),"novelty":max(0,100-x["age_hours"]/0.72)}
        fields=list(raw);percentiles={f:_pct([float((log1p(max(y["latest"].views,0)) if f=="views" else log1p(max(y["velocity"],0)) if f=="view_velocity" else y["share_rate"] if f=="share_rate" else y["engagement"] if f=="engagement_rate" else y["acceleration"] if f=="acceleration" else y["growth"]/max(y["latest"].views-y["growth"],1) if f=="percentage_growth" else max(0,y["share_velocity"]) if f=="share_velocity" else max(0,100-y["age_hours"]/0.72) if f=="novelty" else len({z["video"].creator_id for z in calculations if z["video"].sound_id==y["video"].sound_id or bool(set(z["video"].hashtags)&set(y["video"].hashtags))}) if f=="spread" else y["velocity"]/max(median(creator_velocities[y["video"].creator_id]),1))) for y in cohort],float(raw[f])) for f in fields}
        avs_weights={"views":.25,"view_velocity":.25,"share_rate":.15,"engagement_rate":.10,"acceleration":.10,"creator_baseline_lift":.10,"spread":.05};evs_weights={"view_velocity":.30,"acceleration":.25,"percentage_growth":.15,"share_velocity":.10,"creator_baseline_lift":.10,"novelty":.10};nps_weights={"views":.30,"creator_baseline_lift":.25,"view_velocity":.20,"engagement_rate":.15,"share_rate":.10}
        avs=sum(percentiles[k]*w for k,w in avs_weights.items());evs=sum(percentiles[k]*w for k,w in evs_weights.items());nps=sum(percentiles[k]*w for k,w in nps_weights.items());adjusted=avs*(1-.5*anom/100)
        freshness=max(0,(now-s.freshness_at).total_seconds()/3600);confidence_score=min(100,len(ss)*18)+min(20,len(cohort)*2)-len(v.missing_fields)*10-(20 if freshness>24 else 10 if freshness>8 else 0);confidence_score=max(0,min(100,confidence_score));confidence="High" if confidence_score>=75 else "Medium" if confidence_score>=45 else "Low"
        components={"raw":raw,"percentiles":percentiles,"avs_weights":avs_weights,"evs_weights":evs_weights,"nps_weights":nps_weights,"missing_components":[],"evidence_type":"Demo" if v.provider=="mock" else "Derived"}
        row=db.scalar(select(ViralScore).where(ViralScore.video_id==v.id)) or ViralScore(video_id=v.id);db.add(row);row.views_growth=g;row.views_per_hour=vel;row.acceleration=acc;row.avs=round(avs,1);row.evs=round(evs,1);row.nps=round(nps,1);row.anomaly=anom;row.adjusted=round(adjusted,1);row.confidence=confidence;row.confidence_score=round(confidence_score,1);row.components=components;row.cohort={"market":v.market,"language":v.language,"category":v.category,"video_age_band":_age_band(x["age_hours"]),"sample_size":len(cohort),"fallback":len(cohort)<5};row.score_version="2.0";row.reason=f"{confidence} confidence: {len(ss)} snapshots, cohort size {len(cohort)}, observed velocity {vel:,.0f}/hr."
    db.commit(); return len(calculations)
def make_report(db:Session):
    return generate_report(db)
