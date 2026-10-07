import logging
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import ResearchTopic, ResearchResult, CrawlingLog
from .searcher import perform_search
from .ai_extractor import extract_structured_data
from .deduplicator import generate_content_hash
from .crawler import scrape_specific_url
from .export import update_workspace_excel

logger = logging.getLogger(__name__)

# Initialize background scheduler
scheduler = BackgroundScheduler()

def run_topic_research(topic_id: int):
    """
    Background job that crawls/searches based on the topic mode,
    runs AI structured extraction, saves results, and syncs Excel.
    """
    logger.info(f"Starting scheduled research job for Topic ID: {topic_id}")
    db: Session = SessionLocal()
    
    # Helper function to emit real-time logs to DB crawling_logs table
    def log_event(message: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        logger.info(f"[Topic {topic_id}] {formatted_message}")
        try:
            db_log = CrawlingLog(topic_id=topic_id, message=formatted_message)
            db.add(db_log)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging event to DB: {e}")

    try:
        topic = db.query(ResearchTopic).filter(ResearchTopic.id == topic_id).first()
        if not topic:
            logger.warning(f"Topic {topic_id} not found in database. Removing job.")
            remove_topic_job(topic_id)
            return

        if not topic.is_active:
            logger.info(f"Topic {topic_id} is inactive. Skipping search.")
            return

        # Clear old crawling logs for this topic to start fresh
        db.query(CrawlingLog).filter(CrawlingLog.topic_id == topic_id).delete()
        db.commit()

        log_event(f"Initializing Research Agent for task: '{topic.name}'")
        log_event(f"Mode: {topic.agent_mode.upper()} | Scan Query/URL: '{topic.query}'")

        raw_results = []

        if topic.agent_mode == "url_scrape":
            # Targeted Website Crawler
            log_event(f"Invoking targeted crawling engine for domain page...")
            raw_results = scrape_specific_url(topic.query, topic.name, log_event)
            
        elif topic.agent_mode == "historical":
            # Date-Wise Event Scraper
            log_event(f"Invoking Date-Wise Event aggregator for date: '{topic.query}'")
            historical_queries = [
                f"major events on {topic.query}",
                f"news {topic.query}",
                f"what happened on {topic.query} history"
            ]
            for query in historical_queries:
                log_event(f"Searching web archive for: '{query}'")
                found = perform_search(query, "web")
                raw_results.extend(found)
                
        else:
            # Standard 24/7 Web/News Search Monitor
            log_event(f"Invoking DuckDuckGo web search engine...")
            raw_results = perform_search(topic.query, topic.search_type)

        log_event(f"Discovered {len(raw_results)} total items. Deduplicating and processing...")

        new_results_count = 0
        
        for idx, raw in enumerate(raw_results):
            title = raw["title"]
            url = raw["url"]
            
            # 1. Deduplicate
            content_hash = generate_content_hash(url, title)
            existing_result = db.query(ResearchResult).filter(ResearchResult.content_hash == content_hash).first()
            if existing_result:
                continue

            log_event(f"New Discovery Found: '{title[:50]}...'")
            
            # For specific url scraper, the results are already structured by Ollama in scrape_specific_url
            if topic.agent_mode == "url_scrape":
                new_result = ResearchResult(
                    topic_id=topic.id,
                    title=title,
                    source=raw["source"],
                    url=url,
                    published_date=raw["published_date"],
                    summary=raw["snippet"],
                    category=raw["category"],
                    content_hash=content_hash,
                    discovered_at=datetime.datetime.utcnow()
                )
                db.add(new_result)
                db.commit()
                new_results_count += 1
                
                # Sync excel in real-time
                update_workspace_excel(db)
                continue

            # 2. Extract structured summary & relevance score using Ollama
            log_event(f"Running Ollama AI structured analysis on: '{title[:40]}...'")
            ai_data = extract_structured_data(topic.query, title, raw["snippet"])
            
            # If AI rates relevance too low, skip it
            if ai_data["relevance_score"] < 0.3:
                log_event(f"-> Skipped: '{title[:30]}' (low relevance score: {ai_data['relevance_score']})")
                continue

            # 3. Save new unique result
            new_result = ResearchResult(
                topic_id=topic.id,
                title=title,
                source=raw["source"] or ai_data.get("category", "Web"),
                url=url,
                published_date=raw["published_date"],
                summary=ai_data["summary"],
                category=ai_data["category"],
                content_hash=content_hash,
                discovered_at=datetime.datetime.utcnow()
            )
            db.add(new_result)
            db.commit()  # Commit immediately so it is visible in real-time
            new_results_count += 1
            
            log_event(f"-> Saved: '{ai_data.get('category', 'General')}' - '{title[:40]}...'")
            
            # Sync excel file in real-time
            update_workspace_excel(db)

        # Update last searched timestamp
        topic.last_searched_at = datetime.datetime.utcnow()
        
        # If it was a point-in-time Date search, de-activate the monitor so it runs only once
        if topic.agent_mode == "historical":
            topic.is_active = False
            log_event("Date-Wise search completed. Deactivating research monitor.")
            
        db.commit()
        log_event(f"Research job complete. Added {new_results_count} new entries to Excel sheet.")

    except Exception as e:
        logger.error(f"Error executing research job for topic {topic_id}: {e}", exc_info=True)
        try:
            log_event(f"Error during execution: {str(e)}")
        except Exception:
            pass
    finally:
        db.close()

def add_topic_job(topic_id: int, interval_minutes: int):
    """Adds a scheduled job for a topic."""
    job_id = f"topic_{topic_id}"
    # Remove existing job if any
    remove_topic_job(topic_id)
    
    # Schedule new job
    scheduler.add_job(
        func=run_topic_research,
        trigger=IntervalTrigger(minutes=interval_minutes),
        args=[topic_id],
        id=job_id,
        replace_existing=True
    )
    logger.info(f"Scheduled research job {job_id} to run every {interval_minutes} minutes.")

def remove_topic_job(topic_id: int):
    """Removes a scheduled job for a topic."""
    job_id = f"topic_{topic_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed scheduled job {job_id}.")

def start_scheduler(db: Session):
    """Starts the scheduler and registers all active topics."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Background scheduler started.")
        
        # Load all active topics and register their jobs
        active_topics = db.query(ResearchTopic).filter(ResearchTopic.is_active == True).all()
        for topic in active_topics:
            add_topic_job(topic.id, topic.interval_minutes)
            
            # If it has never been searched, trigger an initial search in background
            if not topic.last_searched_at:
                scheduler.add_job(
                    func=run_topic_research,
                    args=[topic.id],
                    id=f"initial_search_{topic.id}"
                )
                logger.info(f"Scheduled initial search for Topic ID: {topic.id} immediately.")
