from fastapi import FastAPI

import app.models  # noqa: F401  (registers all tables with Base)
from app.api.routes import (
    ask,
    claims,
    customers,
    documents,
    health,
    policies,
    search,
    version,
)
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.include_router(health.router, prefix="/api/v1")
app.include_router(version.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(policies.router, prefix="/api/v1")
app.include_router(claims.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(ask.router, prefix="/api/v1")