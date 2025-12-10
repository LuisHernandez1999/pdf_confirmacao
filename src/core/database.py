from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings
print("\n" + "="*60)
print("DEBUG DE CONEXÃO - VALORES DO settings")
print("="*60)
print(f"DB_HOST: {settings.DB_HOST}")
print(f"DB_PORT: {settings.DB_PORT}")
print(f"DB_USER: {settings.DB_USER}")
print(f"DB_NAME: {settings.DB_NAME}")
print(f"DB_PASSWORD: {'*' * len(settings.DB_PASSWORD)} (len: {len(settings.DB_PASSWORD)})")
print(f"DATABASE_URL GERADA: mysql+pymysql://{settings.DB_USER}:****@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
print("="*60 + "\n")

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


# 🔥 ESTA É A FUNÇÃO QUE O FASTAPI ESPERA
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
