from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "04102003")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "online-shop")
MONGODB_LOG_COLLECTION = os.getenv("MONGODB_LOG_COLLECTION", "logs")

FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "3000"))
FRONTEND_PORT = os.getenv("FRONTEND_PORT")
