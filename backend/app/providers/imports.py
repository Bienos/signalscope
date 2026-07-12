import csv, io, json
from datetime import datetime
from .base import ProviderVideo
REQUIRED={"id","url","creator_id","username","caption","published_at","language","market","views","likes","comments","shares"}
def parse_csv(content:bytes)->list[ProviderVideo]:
    text=content.decode("utf-8-sig"); reader=csv.DictReader(io.StringIO(text)); missing=REQUIRED-set(reader.fieldnames or [])
    if missing: raise ValueError("Missing required headers: "+", ".join(sorted(missing)))
    return [_row(r,"csv_import") for r in reader]
def parse_json(content:bytes)->list[ProviderVideo]:
    value=json.loads(content); rows=value if isinstance(value,list) else value.get("videos",[])
    if not isinstance(rows,list): raise ValueError("JSON must be a list or contain a videos list")
    return [_row(r,"json_import") for r in rows]
def _row(r,provider):
    miss=[x for x in REQUIRED if r.get(x) in (None,"")]
    if miss: raise ValueError("Record missing: "+", ".join(sorted(miss)))
    return ProviderVideo(id=str(r["id"]),url=r["url"],creator_id=str(r["creator_id"]),username=r["username"],caption=r["caption"],published_at=datetime.fromisoformat(str(r["published_at"]).replace("Z","+00:00")).replace(tzinfo=None),language=r["language"],market=r["market"],metrics={k:int(r[k]) for k in ("views","likes","comments","shares")},hashtags=str(r.get("hashtags","")).split("|") if r.get("hashtags") else [],provider=provider,raw_reference=f"import://{r['id']}",missing_fields=miss)

