import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from .ai_extractor import extract_structured_data

logger = logging.getLogger(__name__)

def scrape_specific_url(url: str, filter_query: str, log_event) -> list:
    """
    Crawls a specific URL, parses out text segments and links,
    filters them based on keywords, and uses Ollama to extract
    structured item results.
    """
    log_event(f"Starting specific website crawler on target URL: {url}")
    results = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Parse domain name for search fallbacks
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or url
    if "www." in domain:
        domain = domain.replace("www.", "")

    try:
        log_event(f"HTTP GET requesting URL...")
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            log_event(f"Direct request failed (Status: {response.status_code}). Site likely protected.")
            log_event(f"Invoking search fallback for: site:{domain}...")
            try:
                from .searcher import perform_search
                found_items = perform_search(f"site:{domain} {filter_query}", "web", max_results=8)
                if found_items:
                    log_event(f"Discovered {len(found_items)} items on {domain} via search fallback.")
                    for item in found_items:
                        results.append({
                            "title": item["title"],
                            "source": domain,
                            "url": item["url"],
                            "published_date": None,
                            "snippet": item["snippet"],
                            "category": "Target Scrape (Fallback)"
                        })
                    return results
            except Exception as search_err:
                log_event(f"Search fallback also failed: {str(search_err)}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        log_event("HTML successfully parsed. Analyzing anchors and text blocks...")

        # Find all <a> tags with hrefs
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(strip=True)
            
            # Resolve relative URLs
            absolute_url = urljoin(url, href)
            
            # Basic validation
            if absolute_url.startswith("http"):
                links.append({
                    "text": text,
                    "url": absolute_url
                })

        log_event(f"Discovered {len(links)} links on the page. Filtering for keywords matching: '{filter_query}'...")

        # Filter links and parents for matching keyword cues
        # Keywords could be from filter_query, split into tokens, e.g. "ai", "internship", "job"
        query_words = [w.lower() for w in filter_query.split() if len(w) > 2]
        if not query_words:
            query_words = ["intern", "job", "career", "hiring", "opening", "ai"]

        candidates = []
        seen_urls = set()
        
        for item in links:
            url_lower = item["url"].lower()
            text_lower = item["text"].lower()
            
            # Check if any query word matches the link text or URL path
            matches = any(word in text_lower or word in url_lower for word in query_words)
            
            if matches and item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                candidates.append(item)

        log_event(f"Filtered down to {len(candidates)} relevant candidate links.")

        if not candidates:
            log_event("No static HTML links matching keywords found (target may be a JavaScript/SPA app).")
            log_event(f"Invoking search indexing fallback for: '{domain} {filter_query}'...")
            try:
                from .searcher import perform_search
                found_items = perform_search(f"{domain} {filter_query}", "web", max_results=10)
                if not found_items:
                    found_items = perform_search(f"{filter_query}", "web", max_results=8)
                if found_items:
                    log_event(f"Discovered {len(found_items)} items via search indexing engine.")
                    for item in found_items:
                        results.append({
                            "title": item["title"],
                            "source": item.get("source", domain),
                            "url": item["url"],
                            "published_date": None,
                            "snippet": item["snippet"],
                            "category": "Target Scrape (Discovered)"
                        })
                    return results
            except Exception as search_err:
                log_event(f"Search fallback encountered: {search_err}")

            # Fallback: take first few paragraphs if available
            paragraphs = [p.get_text(strip=True) for p in soup.find_all(["p", "li"]) if len(p.get_text(strip=True)) > 20]
            log_event(f"Extracted {len(paragraphs)} text paragraphs for analysis.")
            for p in paragraphs[:5]:
                candidates.append({
                    "text": p[:200],
                    "url": url
                })

        # Process candidates using Ollama
        max_items = min(len(candidates), 8) # process top 8 candidates to avoid CPU overload
        log_event(f"Processing top {max_items} candidates through Ollama Qwen extractor...")
        
        for idx, cand in enumerate(candidates[:max_items]):
            log_event(f"[{idx+1}/{max_items}] Analyzing candidate: '{cand['text'][:50]}...' ({cand['url']})")
            
            # Call our AI extractor
            # We construct a mock snippet
            mock_snippet = f"Source Page Link: {cand['url']}\nLink Text: {cand['text']}"
            ai_data = extract_structured_data(filter_query, cand["text"] or "Web listing", mock_snippet)
            
            if ai_data and ai_data.get("relevance_score", 0) >= 0.3:
                item_title = ai_data.get("title") or cand["text"] or "Web Listing"
                results.append({
                    "title": item_title[:100],
                    "source": urlparse(url).netloc,
                    "url": cand["url"],
                    "published_date": None,
                    "snippet": ai_data.get("summary") or cand["text"],
                    "category": ai_data.get("category") or "Job Listing"
                })
                log_event(f"-> Saved: '{item_title[:40]}...' [Relevance: {ai_data.get('relevance_score')}]")
            else:
                log_event(f"-> Skipped candidate (low relevance score).")
                
        log_event(f"Crawler run complete. Extracted {len(results)} structured items.")
        return results

    except Exception as e:
        log_event(f"Direct crawler request failed: {str(e)}")
        log_event(f"Invoking search fallback for: site:{domain}...")
        try:
            from .searcher import perform_search
            found_items = perform_search(f"site:{domain} {filter_query}", "web", max_results=8)
            if found_items:
                log_event(f"Discovered {len(found_items)} items on {domain} via search fallback.")
                for item in found_items:
                    results.append({
                        "title": item["title"],
                        "source": domain,
                        "url": item["url"],
                        "published_date": None,
                        "snippet": item["snippet"],
                        "category": "Target Scrape (Fallback)"
                    })
                return results
        except Exception as search_err:
            log_event(f"Search fallback also failed: {str(search_err)}")
            
        logger.error(f"Error scraping specific URL: {e}", exc_info=True)
        return []
