import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import datetime
from io import BytesIO

from .database import get_db
from .models import init_db, ResearchTopic, ResearchResult, CrawlingLog
from .scheduler import start_scheduler, add_topic_job, remove_topic_job, run_topic_research
from .export import export_results_to_excel, update_workspace_excel

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="ResearchForge AI API", version="1.0.0")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class TopicCreate(BaseModel):
    name: str
    query: str
    search_type: str = "both"  # "news", "web", "both"
    interval_minutes: int = 15
    agent_mode: str = "search"  # "search", "url_scrape", "historical"

class TopicResponse(BaseModel):
    id: int
    name: str
    query: str
    search_type: str
    interval_minutes: int
    is_active: bool
    agent_mode: str
    created_at: datetime.datetime
    last_searched_at: Optional[datetime.datetime] = None
    results_count: int

    class Config:
        from_attributes = True

# Initialize database and scheduler on startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing database tables...")
    init_db()
    
    logger.info("Synchronizing workspace Excel sheet...")
    db = next(get_db())
    try:
        update_workspace_excel(db)
        logger.info("Starting background search jobs...")
        start_scheduler(db)
    finally:
        db.close()

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total_topics = db.query(ResearchTopic).count()
    total_results = db.query(ResearchResult).count()
    
    # Calculate discoveries today (UTC)
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    discoveries_today = db.query(ResearchResult).filter(ResearchResult.discovered_at >= today_start).count()
    
    active_monitors = db.query(ResearchTopic).filter(ResearchTopic.is_active == True).count()
    
    # Get last 15 discoveries with topic names
    recent = db.query(ResearchResult).order_by(ResearchResult.discovered_at.desc()).limit(15).all()
    recent_list = []
    for r in recent:
        recent_list.append({
            "id": r.id,
            "topic_name": r.topic.name if r.topic else "Unknown",
            "title": r.title,
            "source": r.source,
            "category": r.category,
            "url": r.url,
            "discovered_at": r.discovered_at
        })
        
    return {
        "total_topics": total_topics,
        "total_results": total_results,
        "discoveries_today": discoveries_today,
        "active_monitors": active_monitors,
        "recent_discoveries": recent_list
    }

@app.post("/api/topics", response_model=TopicResponse)
def create_topic(topic: TopicCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    new_topic = ResearchTopic(
        name=topic.name,
        query=topic.query,
        search_type=topic.search_type,
        interval_minutes=topic.interval_minutes,
        agent_mode=topic.agent_mode
    )
    db.add(new_topic)
    db.commit()
    db.refresh(new_topic)
    
    # Register background task
    add_topic_job(new_topic.id, new_topic.interval_minutes)
    
    # Trigger initial search run immediately in background
    background_tasks.add_task(run_topic_research, new_topic.id)
    
    # Format return
    return {
        "id": new_topic.id,
        "name": new_topic.name,
        "query": new_topic.query,
        "search_type": new_topic.search_type,
        "interval_minutes": new_topic.interval_minutes,
        "is_active": new_topic.is_active,
        "agent_mode": new_topic.agent_mode,
        "created_at": new_topic.created_at,
        "last_searched_at": new_topic.last_searched_at,
        "results_count": 0
    }

@app.get("/api/topics", response_model=List[TopicResponse])
def get_topics(db: Session = Depends(get_db)):
    topics = db.query(ResearchTopic).all()
    results = []
    for topic in topics:
        count = db.query(ResearchResult).filter(ResearchResult.topic_id == topic.id).count()
        results.append({
            "id": topic.id,
            "name": topic.name,
            "query": topic.query,
            "search_type": topic.search_type,
            "interval_minutes": topic.interval_minutes,
            "is_active": topic.is_active,
            "agent_mode": topic.agent_mode,
            "created_at": topic.created_at,
            "last_searched_at": topic.last_searched_at,
            "results_count": count
        })
    return results

@app.get("/api/topics/{topic_id}")
def get_topic_detail(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(ResearchTopic).filter(ResearchTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    results = db.query(ResearchResult)\
        .filter(ResearchResult.topic_id == topic_id)\
        .order_by(ResearchResult.discovered_at.desc())\
        .all()
        
    results_list = []
    for r in results:
        results_list.append({
            "id": r.id,
            "title": r.title,
            "source": r.source,
            "url": r.url,
            "published_date": r.published_date,
            "summary": r.summary,
            "category": r.category,
            "discovered_at": r.discovered_at
        })
        
    return {
        "id": topic.id,
        "name": topic.name,
        "query": topic.query,
        "search_type": topic.search_type,
        "interval_minutes": topic.interval_minutes,
        "is_active": topic.is_active,
        "agent_mode": topic.agent_mode,
        "created_at": topic.created_at,
        "last_searched_at": topic.last_searched_at,
        "results": results_list
    }

@app.delete("/api/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(ResearchTopic).filter(ResearchTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    # Remove scheduled job
    remove_topic_job(topic_id)
    
    # Delete from DB
    db.delete(topic)
    db.commit()
    return {"message": f"Successfully deleted topic '{topic.name}'"}

@app.post("/api/topics/{topic_id}/sync")
def sync_topic_now(topic_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    topic = db.query(ResearchTopic).filter(ResearchTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    # Run sync in background task
    background_tasks.add_task(run_topic_research, topic_id)
    return {"message": "Sync job triggered successfully in the background."}

@app.post("/api/topics/{topic_id}/pause")
def pause_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(ResearchTopic).filter(ResearchTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    topic.is_active = False
    db.commit()
    
    # Remove from active scheduler jobs
    remove_topic_job(topic_id)
    
    return {"message": f"Successfully paused monitoring for '{topic.name}'", "is_active": False}

@app.post("/api/topics/{topic_id}/resume")
def resume_topic(topic_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    topic = db.query(ResearchTopic).filter(ResearchTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    topic.is_active = True
    db.commit()
    
    # Re-register scheduled job
    add_topic_job(topic_id, topic.interval_minutes)
    
    # Trigger an immediate run in the background
    background_tasks.add_task(run_topic_research, topic_id)
    
    return {"message": f"Successfully resumed monitoring for '{topic.name}'", "is_active": True}

@app.get("/api/topics/{topic_id}/logs")
def get_topic_logs(topic_id: int, db: Session = Depends(get_db)):
    """
    Fetches the latest crawling logs for a specific research topic.
    """
    logs = db.query(CrawlingLog)\
        .filter(CrawlingLog.topic_id == topic_id)\
        .order_by(CrawlingLog.timestamp.asc())\
        .all()
    return [{"id": l.id, "message": l.message, "timestamp": l.timestamp} for l in logs]

@app.get("/api/topics/{topic_id}/export")
def export_topic_results(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(ResearchTopic).filter(ResearchTopic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    results = db.query(ResearchResult).filter(ResearchResult.topic_id == topic_id).all()
    excel_data = export_results_to_excel(results)
    
    filename = f"research_{topic.name.lower().replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== INTERACTIVE AI AGENT ROUTES ====================
from .agent_engine import agent_session, PDF_EXPORT_PATH
from fastapi.responses import FileResponse
import os

class AgentChatRequest(BaseModel):
    message: str

class AgentCredentialRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    otp: Optional[str] = None

@app.get("/api/agent/status")
def get_agent_status():
    """Returns current live state, chat history, and logs of the interactive agent."""
    return agent_session.get_status()

@app.post("/api/agent/chat")
def agent_chat(req: AgentChatRequest):
    """Processes user instructions, mission assignments, and live corrections."""
    return agent_session.handle_user_message(req.message)

@app.post("/api/agent/credentials")
def agent_submit_credentials(req: AgentCredentialRequest):
    """Securely accepts login credentials, OTP, or session token to access protected portals."""
    return agent_session.process_credentials(email=req.email, password=req.password, token=req.token, otp=req.otp)

@app.post("/api/agent/reset")
def agent_reset():
    """Resets the interactive agent state."""
    agent_session.__init__()
    return agent_session.get_status()

@app.get("/api/agent/export-pdf")
def agent_export_pdf():
    """Downloads the unified multi-page Problem Statements PDF."""
    if not os.path.exists(PDF_EXPORT_PATH):
        raise HTTPException(status_code=404, detail="PDF has not been generated yet.")
    return FileResponse(
        PDF_EXPORT_PATH,
        media_type="application/pdf",
        filename="Techgium_Problem_Statements_All.pdf"
    )

