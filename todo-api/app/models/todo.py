from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Todo(Base):
    """
    This class IS the database table. SQLAlchemy maps it to a table called 'todos'.
    Each attribute with Column() becomes a column in that table.
    
    This is called an ORM (Object Relational Mapper) model — it lets us
    work with database rows as Python objects instead of writing raw SQL.
    """
    __tablename__ = "todos"

    # Primary key — a unique integer ID auto-incremented by the DB.
    # Every row in a relational DB needs a unique identifier.
    id = Column(Integer, primary_key=True, index=True)

    # The todo title. nullable=False means the DB will reject a row without it.
    # index=True creates a DB index — makes searching by title faster.
    title = Column(String, nullable=False, index=True)

    # Optional longer description. nullable=True (default) means it can be empty.
    description = Column(String, nullable=True)

    # Whether the todo is done. Defaults to False when a new todo is created.
    completed = Column(Boolean, default=False, nullable=False)

    # Timestamps — automatically set by the database server, not our app.
    # server_default=func.now() means the DB sets this to 'now' on INSERT.
    # onupdate=func.now() means the DB updates this to 'now' on every UPDATE.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
