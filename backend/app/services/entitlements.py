"""Commercial entitlement boundary. Billing and workspace ownership are not implemented."""
from typing import Any

PLAN_FEATURES:dict[str,set[str]]={
    "free":{"today","discover","watchlists","reports","data_health"},
    "pro":{"today","discover","creator_intelligence","ideas","watchlists","alerts","reports","report_generation","exports","data_health"},
    "team":{"today","discover","creator_intelligence","ideas","watchlists","alerts","reports","report_generation","scheduled_reports","exports","review_queue","team_collaboration","data_health"},
    "enterprise":{"today","discover","creator_intelligence","ideas","watchlists","alerts","reports","report_generation","scheduled_reports","exports","review_queue","team_collaboration","data_health","api","sso"},
}
PLAN_QUOTAS:dict[str,dict[str,Any]]={
    "free":{"markets":1,"languages":1,"history_days":7,"results_per_view":5,"searches_per_month":10,"monitors":1,"alerts_per_month":0,"seats":1,"refresh_hours":24,"export_formats":[]},
    "pro":{"markets":3,"languages":2,"history_days":90,"results_per_view":100,"searches_per_month":500,"monitors":5,"alerts_per_month":100,"seats":1,"refresh_hours":6,"export_formats":["csv","xlsx","html"]},
    "team":{"markets":3,"languages":2,"history_days":365,"results_per_view":500,"searches_per_month":2_000,"monitors":20,"alerts_per_month":500,"seats":5,"refresh_hours":4,"export_formats":["csv","xlsx","html"]},
    "enterprise":{"markets":None,"languages":None,"history_days":None,"results_per_view":None,"searches_per_month":None,"monitors":None,"alerts_per_month":None,"seats":None,"refresh_hours":None,"export_formats":["csv","xlsx","html","api"]},
}
ADD_ON_FEATURES={"hashtag_research":{"hashtag_research"},"sound_intelligence":{"sound_intelligence"},"trend_depth_bundle":{"hashtag_research","sound_intelligence"}}

def resolve_entitlements(plan:str,addons:list[str]|None=None)->dict[str,Any]:
    selected=plan if plan in PLAN_FEATURES else "free"
    features=set(PLAN_FEATURES[selected])
    accepted=[]
    if selected!="free":
        for addon in addons or []:
            if addon in ADD_ON_FEATURES:
                features.update(ADD_ON_FEATURES[addon]);accepted.append(addon)
    return {"plan":selected,"features":sorted(features),"quotas":PLAN_QUOTAS[selected],"addons":accepted,"enforcement":"catalog_only_demo"}
