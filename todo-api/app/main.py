from fastapi import FastAPI
from app.database import engine, Base
from app.routes import todos

# Create all database tables on startup if they don't exist.
# In production you'd use Alembic migrations instead (more controlled),
# but for development this is convenient.
Base.metadata.create_all(bind=engine)

# FastAPI() creates the application instance.
# title, description, version show up in the auto-generated /docs page.
app = FastAPI(
    title="Todo API",
    description="A simple Todo REST API built with FastAPI, PostgreSQL, and Redis",
    version="1.0.0",
)

# Mount the todos router.
# All routes defined in todos.py are now accessible under /todos/...
# This is how you scale a FastAPI app — each domain (todos, users, auth)
# gets its own router file, all mounted here.
app.include_router(todos.router)


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    
    This is critical for Kubernetes — K3s calls this endpoint periodically
    (liveness probe) to know if the container is healthy. If it returns
    anything other than 2xx, K3s restarts the pod.
    
    In a production app you'd also check DB connectivity here.
    """
    return {"status": "ok"}
