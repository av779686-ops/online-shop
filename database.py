from sqlalchemy import  create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from settings import DB_USER, DB_PASS, DB_NAME, DB_HOST, DB_PORT

DATABASE_URL = "postgresql://postgres:04102003@localhost:5432/postgres"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
