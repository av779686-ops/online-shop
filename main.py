
from time import perf_counter

from fastapi import FastAPI
from fastapi import Request
from api.v1.endpoints.products import products_router
from api.v1.endpoints.users import users_router
from api.v1.endpoints.auth import auth_router
from api.v1.endpoints.basket import basket_router
from database import engine, Base
from logging_config import logger

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


@app.middleware("http")
async def log_endpoint_call(request: Request, call_next):
    """Log every HTTP endpoint call without recording credentials or bodies."""
    started_at = perf_counter()
    client = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "%s %s -> 500 client=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            client,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    log = logger.warning if response.status_code >= 400 else logger.info
    log(
        "%s %s -> %s client=%s duration_ms=%.2f",
        request.method,
        request.url.path,
        response.status_code,
        client,
        duration_ms,
    )
    return response


Base.metadata.create_all(bind = engine)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(basket_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5555",
        "http://localhost:5555",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
