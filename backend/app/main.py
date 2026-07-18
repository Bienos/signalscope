from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .api.routes import router
from .api.toy_routes import router as toy_router
from .db import engine
app=FastAPI(title="SignalScope",version="0.1.0",description="Provider-independent monitored-sample trend intelligence. No scraping or stored media.")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
# Register resource-specific toy routes before the legacy catch-all resource
# route so that `/api/toys/*` and `/api/providers/apify/*` cannot be shadowed.
app.include_router(toy_router)
app.include_router(router)
@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/ready")
def ready():
    try:
        with engine.connect() as c:c.execute(text("select 1"))
        return {"status":"ready"}
    except Exception:return {"status":"not_ready"}
