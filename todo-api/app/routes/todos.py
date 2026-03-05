from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.todo import Todo
from app.models.schemas import TodoCreate, TodoUpdate, TodoResponse
from app.cache import get_cached, set_cached, invalidate_cache

# APIRouter is like a mini FastAPI app — it groups related endpoints.
# We mount it in main.py with a prefix, so all routes here become /todos/...
# This keeps the code organized: todos logic lives here, not in main.py.
router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """
    Create a new todo.
    
    'todo: TodoCreate' — FastAPI automatically parses the request body JSON
    and validates it against the TodoCreate schema. If validation fails,
    it returns 422 before this function is ever called.
    
    'db: Session = Depends(get_db)' — dependency injection. FastAPI calls
    get_db(), gets the session, and passes it here. We never manually
    create a session in route handlers.
    
    HTTP 201 Created is more semantically correct than 200 OK for creation.
    """
    # Create a new SQLAlchemy model instance from the validated input
    db_todo = Todo(
        title=todo.title,
        description=todo.description,
    )

    db.add(db_todo)      # Stage the INSERT in the session
    db.commit()          # Execute the INSERT and save to DB
    db.refresh(db_todo)  # Reload the object to get DB-generated fields (id, created_at)

    # Invalidate the list cache since we added a new item
    invalidate_cache("todos:all")

    return db_todo


@router.get("/", response_model=List[TodoResponse])
def get_todos(db: Session = Depends(get_db)):
    """
    Get all todos.
    
    List[TodoResponse] means we return an array of todo objects.
    
    We check the cache first. Cache key 'todos:all' represents the full list.
    On a cache miss, we query the DB and then populate the cache.
    On a cache hit, we skip the DB entirely — much faster.
    """
    cache_key = "todos:all"
    cached = get_cached(cache_key)
    if cached:
        return cached

    todos = db.query(Todo).order_by(Todo.created_at.desc()).all()

    # Serialize to dict for caching (SQLAlchemy objects can't be JSON serialized directly)
    todos_data = [TodoResponse.model_validate(t).model_dump() for t in todos]
    set_cached(cache_key, todos_data)

    return todos


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """
    Get a single todo by ID.
    
    'todo_id: int' — FastAPI extracts this from the URL path and validates
    it's an integer. /todos/abc would return a 422 automatically.
    
    We raise HTTPException with 404 if not found. This is the standard
    REST convention: 404 Not Found when a resource doesn't exist.
    """
    cache_key = f"todos:{todo_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )

    todo_data = TodoResponse.model_validate(todo).model_dump()
    set_cached(cache_key, todo_data)

    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)):
    """
    Update a todo. Only updates fields that are explicitly provided.
    
    We iterate over the update schema fields and only apply the ones
    that are not None. This is the partial update pattern — the client
    can send just {"completed": true} and we won't touch the title.
    
    exclude_unset=True is key: it only includes fields the client actually
    sent, not fields that defaulted to None. This prevents accidentally
    overwriting data with None.
    """
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )

    # Get only the fields the client actually provided
    update_data = todo_update.model_dump(exclude_unset=True)

    # Apply each update to the SQLAlchemy object
    for field, value in update_data.items():
        setattr(todo, field, value)

    db.commit()
    db.refresh(todo)

    # Invalidate both the individual and list caches
    invalidate_cache(f"todos:{todo_id}")
    invalidate_cache("todos:all")

    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """
    Delete a todo.
    
    HTTP 204 No Content is the standard for successful deletion —
    the operation succeeded but there's nothing to return.
    We still return 404 if the todo doesn't exist.
    """
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )

    db.delete(todo)
    db.commit()

    invalidate_cache(f"todos:{todo_id}")
    invalidate_cache("todos:all")
