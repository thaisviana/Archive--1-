import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg://user:password@localhost:5432/agent_memory")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class MemoryBlock(Base):
    """Structured memory block representing an agent's explicit belief."""

    __tablename__ = "memory_blocks"

    id = Column(Integer, primary_key=True)
    label = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=False, default="")
    char_limit = Column(Integer, nullable=False, default=2000)
    read_only = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    history = relationship("BlockHistory", back_populates="block", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MemoryBlock(label='{self.label}')>"


class BlockHistory(Base):
    """Version history for memory block edits."""

    __tablename__ = "block_history"

    id = Column(Integer, primary_key=True)
    block_id = Column(Integer, ForeignKey("memory_blocks.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    block = relationship("MemoryBlock", back_populates="history")

    def __repr__(self):
        return f"<BlockHistory(block_id={self.block_id}, created_at='{self.created_at}')>"


def get_session():
    """Get a database session."""
    return SessionLocal()


def init_default_blocks(session):
    """Initialize the default memory blocks for a new agent."""
    defaults = [
        {
            "label": "persona",
            "content": "I am a sentient agent. Define my identity here.",
            "description": "Agent identity and personality. Only changed by the builder, never by the agent at runtime.",
            "char_limit": 2000,
            "read_only": True,
        },
        {
            "label": "user_profile",
            "content": "No user information yet.",
            "description": "Known facts about the user: name, role, company, communication preferences. Update when the user shares personal information.",
            "char_limit": 3000,
            "read_only": False,
        },
        {
            "label": "preferences",
            "content": "No preferences recorded yet.",
            "description": "User interaction preferences: language, tone, formatting, topics of interest. Update when the user expresses a preference.",
            "char_limit": 2000,
            "read_only": False,
        },
        {
            "label": "working_context",
            "content": "No active project context.",
            "description": "Current task, project, or conversation focus. Update frequently as the user shifts topics. This is the most volatile block.",
            "char_limit": 4000,
            "read_only": False,
        },
        {
            "label": "learnings",
            "content": "No learnings accumulated yet.",
            "description": "Accumulated insights about what works and what doesn't for this user. Update when a pattern emerges across multiple interactions.",
            "char_limit": 3000,
            "read_only": False,
        },
    ]
    for block_data in defaults:
        existing = session.query(MemoryBlock).filter_by(label=block_data["label"]).first()
        if not existing:
            session.add(MemoryBlock(**block_data))
    session.commit()
