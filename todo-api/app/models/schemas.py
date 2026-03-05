from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# --- INPUT schemas (what the client sends to us) ---

class TodoCreate(BaseModel):
    """
    Schema for creating a new todo (POST /todos).
    
    Pydantic validates incoming JSON against this schema automatically.
    If the client sends invalid data (missing title, wrong type), FastAPI
    returns a 422 error with a clear explanation before our code even runs.
    
    Field() lets us add metadata: description for docs, constraints like min_length.
    """
    title: str = Field(..., min_length=1, max_length=200, description="The todo title")
    description: Optional[str] = Field(None, max_length=1000, description="Optional details")


class TodoUpdate(BaseModel):
    """
    Schema for updating a todo (PUT /todos/{id}).
    
    All fields are Optional here — the client can update just the title,
    just the completed status, or any combination. This is called a
    'partial update' pattern. None means 'don't change this field'.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None


# --- OUTPUT schemas (what we send back to the client) ---

class TodoResponse(BaseModel):
    """
    Schema for what we return to the client.
    
    This is important — we deliberately control what fields are exposed.
    In a real app you might have sensitive fields (user password hash, internal IDs)
    in your DB model that you never want to return. The response schema is your
    safety layer between your DB and the outside world.
    
    from_attributes=True tells Pydantic it can read data from SQLAlchemy
    model attributes (not just dicts). Without this, serialization would fail.
    """
    id: int
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
