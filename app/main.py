import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, SessionLocal, Base
from app.schema import graphql_router
from app.seeds.seeder import run_seed

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    Base.metadata.create_all(bind=engine)
    # Seed if empty
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Pokemon GraphQL API",
    description="Demonstrates GraphQL vs REST using PokeAPI data.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(graphql_router, prefix="/graphql")


@app.get("/health")
def health():
    return {"status": "ok"}
