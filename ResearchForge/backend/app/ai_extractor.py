import os
import requests
import json
import logging
import re

logger = logging.getLogger(__name__)

OLLAMA_HOSTS = [
    os.getenv("OLLAMA_HOST", ""),
    "http://localhost:11434",
    "http://127.0.0.1:11434",
    "http://host.docker.internal:11434"
]
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")

def _smart_fallback_extraction(query: str, title: str, snippet: str) -> dict:
    """Fast, intelligent NLP fallback when Ollama LLM is unavailable or offline."""
    text_content = f"{title} {snippet}".lower()
    query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
    
    # Calculate keyword match score
    matches = sum(1 for word in query_words if word in text_content)
    relevance_score = min(0.95, max(0.5, 0.5 + (matches / (len(query_words) or 1)) * 0.45))
    
    # Categorization logic
    category = "General"
    if any(k in text_content for k in ["intern", "internship", "job", "hiring", "role", "career", "opening", "vacancy"]):
        category = "Internship"
    elif any(k in text_content for k in ["ai", "machine learning", "deep learning", "llm", "gpt", "model", "neural", "python"]):
        category = "AI & ML"
    elif any(k in text_content for k in ["tech", "software", "developer", "engineering", "code"]):
        category = "Technology"
    elif any(k in text_content for k in ["stock", "market", "finance", "crypto", "business", "economy"]):
        category = "Finance"
    elif any(k in text_content for k in ["politic", "election", "government", "minister", "president"]):
        category = "Politics"
    elif any(k in text_content for k in ["sport", "match", "game", "league", "cup"]):
        category = "Sports"
    elif any(k in text_content for k in ["news", "report", "update", "break"]):
        category = "News"

    clean_summary = snippet.strip() if snippet else title.strip()
    if len(clean_summary) > 250:
        clean_summary = clean_summary[:247] + "..."

    return {
        "title": title or "Research Finding",
        "summary": clean_summary or "No summary available.",
        "category": category,
        "relevance_score": round(relevance_score, 2)
    }

def extract_structured_data(query: str, title: str, snippet: str) -> dict:
    """
    Analyzes title and snippet to generate structured summary, category, and relevance.
    Uses local Ollama LLM if reachable, or fast smart NLP fallback.
    """
    fallback = _smart_fallback_extraction(query, title, snippet)
    
    prompt = f"""You are a research AI agent. Analyze this search result snippet for query "{query}":
Title: {title}
Snippet: {snippet}

Task:
1. Extract a concise 1-2 sentence summary.
2. Assign a specific category label (e.g. Internship, Technology, AI & ML, Finance, Politics, Sports, General).
3. Rate relevance to query "{query}" from 0.0 to 1.0.

Respond ONLY in JSON matching this schema:
{{
  "title": "{title}",
  "summary": "1-2 sentence summary",
  "category": "Category Label",
  "relevance_score": 0.9
}}
"""

    for host in OLLAMA_HOSTS:
        if not host:
            continue
        url = f"{host.rstrip('/')}/api/generate"
        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1}
            }
            response = requests.post(url, json=payload, timeout=3)
            if response.status_code == 200:
                result_text = response.json().get("response", "")
                data = json.loads(result_text)
                return {
                    "title": data.get("title", fallback["title"]),
                    "summary": data.get("summary", fallback["summary"]),
                    "category": data.get("category", fallback["category"]),
                    "relevance_score": float(data.get("relevance_score", fallback["relevance_score"]))
                }
        except Exception:
            continue

    return fallback

