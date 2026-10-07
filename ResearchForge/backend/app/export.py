import pandas as pd
from io import BytesIO
from typing import List
import os
import logging
from sqlalchemy.orm import Session
from .models import ResearchResult, ResearchTopic

logger = logging.getLogger(__name__)

EXPORT_DIR = os.getenv("EXPORTS_DIR", "./exports")
EXPORT_PATH = os.path.join(EXPORT_DIR, "Personal_Researcher_Results.xlsx")

def export_results_to_excel(results: List[ResearchResult]) -> bytes:
    """
    Exports a list of ResearchResult objects to binary Excel (.xlsx) data.
    """
    data = []
    for r in results:
        data.append({
            "ID": r.id,
            "Topic Name": r.topic.name if r.topic else "Unknown",
            "Title": r.title,
            "Source": r.source or "N/A",
            "URL": r.url,
            "Published Date": r.published_date or "N/A",
            "Summary": r.summary or "N/A",
            "Category": r.category or "General",
            "Discovered At": r.discovered_at.strftime("%Y-%m-%d %H:%M:%S") if r.discovered_at else "N/A"
        })
        
    df = pd.DataFrame(data)
    
    # Write to a BytesIO buffer
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    return output.getvalue()

def update_workspace_excel(db: Session):
    """
    Updates the local Excel file in the shared exports folder.
    It writes each active research topic's results to a separate sheet tab.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)
        
        topics = db.query(ResearchTopic).all()
        if not topics:
            return
            
        with pd.ExcelWriter(EXPORT_PATH, engine='openpyxl') as writer:
            for topic in topics:
                # Query results for this topic
                results = db.query(ResearchResult).filter(ResearchResult.topic_id == topic.id).all()
                
                data = []
                for r in results:
                    data.append({
                        "ID": r.id,
                        "Title": r.title,
                        "Source": r.source or "N/A",
                        "URL": r.url,
                        "Published Date": r.published_date or "N/A",
                        "Summary": r.summary or "N/A",
                        "Category": r.category or "General",
                        "Discovered At": r.discovered_at.strftime("%Y-%m-%d %H:%M:%S") if r.discovered_at else "N/A"
                    })
                
                # Sheet names can't exceed 31 chars and must not contain special chars
                sheet_name = "".join(c for c in topic.name if c.isalnum() or c in " _-")[:30]
                if not sheet_name:
                    sheet_name = f"Topic_{topic.id}"
                    
                if data:
                    df = pd.DataFrame(data)
                else:
                    # Empty DataFrame with headers
                    df = pd.DataFrame(columns=["ID", "Title", "Source", "URL", "Published Date", "Summary", "Category", "Discovered At"])
                    
                df.to_excel(writer, index=False, sheet_name=sheet_name)
                
        logger.info(f"Excel file successfully synchronized at: {EXPORT_PATH}")
        
    except Exception as e:
        logger.error(f"Failed to update workspace Excel file: {e}", exc_info=True)
