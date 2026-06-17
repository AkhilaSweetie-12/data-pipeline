"""FastAPI application entrypoint for the Retail DataSecOps platform."""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.logging_config import configure_logging
from app.auth import seed_default_users
from app.routers import customers, orders, dashboard, auth as auth_router

configure_logging()
logger = logging.getLogger("retail_api")
settings = get_settings()

# Create tables automatically in DEV. Retry to tolerate a DB container that is
# still starting up (e.g. under docker-compose). For Azure SQL prod use sql/ scripts.
def _init_db(retries: int = 10, delay: float = 3.0) -> None:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            try:
                seed_default_users(db)
            finally:
                db.close()
            logger.info("Database initialized (attempt %s)", attempt)
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            logger.warning("DB not ready (attempt %s/%s): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError(f"Database initialization failed after {retries} attempts: {last_err}")


_init_db()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Retail Sales Management API for the End-to-End DataSecOps platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "environment": settings.environment}


app.include_router(auth_router.router)
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(dashboard.router)
