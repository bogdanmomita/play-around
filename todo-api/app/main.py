from fastapi import FastAPI
from app.database import engine, Base
from app.routes import todos

app = FastAPI(
    title="Todo API",
    description="A simple Todo REST API built with FastAPI, PostgreSQL, and Redis",
    version="1.0.0",
)

app.include_router(todos.router)


@app.on_event("startup")
def startup():
    """
    This runs when the server actually starts — NOT at import time.
    Tests import the app but never start the server, so this never
    fires during testing. The test fixture creates its own tables.
    """
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}