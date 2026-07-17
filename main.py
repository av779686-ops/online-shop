from fastapi import FastAPI
from api.v1.endpoints.products import products_router
from api.v1.endpoints.users import users_router
from api.v1.endpoints.auth import auth_router
from api.v1.endpoints.basket import basket_router
from database import engine, Base

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
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


