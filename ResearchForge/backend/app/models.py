from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .database import Base, engine

class ResearchTopic(Base):
    __tablename__ = "research_topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    query = Column(String, nullable=False)
    search_type = Column(String, default="both")  # "news", "web", "both"
    interval_minutes = Column(Integer, default=15)
    is_active = Column(Boolean, default=True)
    agent_mode = Column(String, default="search")  # "search", "url_scrape", "historical"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_searched_at = Column(DateTime, nullable=True)

    results = relationship("ResearchResult", back_populates="topic", cascade="all, delete-orphan")

class ResearchResult(Base):
    __tablename__ = "research_results"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("research_topics.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    source = Column(String, nullable=True)
    url = Column(String, nullable=False)
    published_date = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    content_hash = Column(String, unique=True, index=True, nullable=False)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)

    topic = relationship("ResearchTopic", back_populates="results")

class CrawlingLog(Base):
    __tablename__ = "crawling_logs"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("research_topics.id", ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    topic = relationship("ResearchTopic")

def init_db():
    Base.metadata.create_all(bind=engine)
