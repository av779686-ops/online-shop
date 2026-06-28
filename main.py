from fastapi import FastAPI
from api.v1.endpoints.products import products_router
from api.v1.endpoints.users import users_router
from database import engine, Base

app = FastAPI()
Base.metadata.create_all(bind = engine)
app.include_router(users_router)
app.include_router(products_router)




