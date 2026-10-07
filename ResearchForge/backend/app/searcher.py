import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urlparse, parse_qs, unquote, quote_plus
import json

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

def clean_ddg_url(url: str) -> str:
    """Extracts redirect URL from DuckDuckGo search result links if present."""
    if "uddg=" in url:
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            if "uddg" in qs:
                return unquote(qs["uddg"][0])
        except Exception:
            pass
    return url

def search_yahoo(query: str, max_results: int = 12) -> List[Dict]:
    """Queries Yahoo Search with clean extraction of URLs and snippets."""
    results = []
    try:
        url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for container in soup.find_all(["li", "div"], class_=lambda c: c and "algo" in c):
                h3 = container.find("h3")
                if not h3:
                    continue
                title = h3.get_text(strip=True)
                a = h3.find("a") or h3.find_parent("a") or container.find("a")
                if not a or not a.get("href"):
                    continue
                
                raw_href = a["href"]
                target_url = raw_href
                if "/RU=" in raw_href:
                    try:
                        target_url = unquote(raw_href.split("/RU=")[1].split("/")[0])
                    except Exception:
                        target_url = raw_href

                if not target_url.startswith("http"):
                    continue

                comp = container.find(["div", "p"], class_=lambda c: c and ("compText" in c or "snippet" in c or "lh-" in c))
                snippet = comp.get_text(strip=True) if comp else title

                domain = urlparse(target_url).netloc.replace("www.", "")
                results.append({
                    "title": title,
                    "url": target_url,
                    "source": domain,
                    "published_date": None,
                    "snippet": snippet,
                    "type": "web"
                })
                if len(results) >= max_results:
                    break
    except Exception as e:
        logger.warning(f"Yahoo search error: {e}")
    return results

def search_wikipedia(query: str, max_results: int = 5) -> List[Dict]:
    """Queries Wikipedia OpenSearch API for definitions, historical events, and topics."""
    results = []
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote_plus(query)}&limit={max_results}&namespace=0&format=json"
        resp = requests.get(url, headers={"User-Agent": "PersonalResearcher/2.0"}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            titles = data[1] if len(data) > 1 else []
            descriptions = data[2] if len(data) > 2 else []
            links = data[3] if len(data) > 3 else []
            
            for i in range(len(titles)):
                title = titles[i]
                link = links[i] if i < len(links) else ""
                desc = descriptions[i] if i < len(descriptions) and descriptions[i] else f"Information on {title}"
                if link:
                    results.append({
                        "title": title,
                        "url": link,
                        "source": "wikipedia.org",
                        "published_date": None,
                        "snippet": desc,
                        "type": "encyclopedia"
                    })
    except Exception as e:
        logger.warning(f"Wikipedia API error: {e}")
    return results

def search_ddg_html(query: str, max_results: int = 8) -> List[Dict]:
    """Queries DuckDuckGo HTML fallback."""
    results = []
    try:
        url = "https://html.duckduckgo.com/html/"
        response = requests.post(url, data={"q": query}, headers=HEADERS, timeout=6)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            result_divs = soup.find_all("div", class_="result__body")
            for div in result_divs[:max_results]:
                title_link = div.find("a", class_="result__a")
                snippet_elem = div.find("a", class_="result__snippet")
                if title_link and snippet_elem:
                    title = title_link.get_text().strip()
                    final_url = clean_ddg_url(title_link.get("href", ""))
                    snippet = snippet_elem.get_text().strip()
                    source = urlparse(final_url).netloc.replace("www.", "")
                    results.append({
                        "title": title,
                        "url": final_url,
                        "source": source,
                        "published_date": None,
                        "snippet": snippet,
                        "type": "web"
                    })
    except Exception as e:
        logger.warning(f"DDG HTML search error: {e}")
    return results

def perform_search(query: str, search_type: str = "both", max_results: int = 15) -> List[Dict]:
    """
    Multi-source resilient search: queries Yahoo, DDG, and Wikipedia.
    Ensures the scraper reliably discovers content without being blocked.
    """
    search_query = query
    if search_type == "news" and "news" not in query.lower():
        search_query = f"{query} news"

    logger.info(f"Performing multi-source search for query: '{search_query}'")
    all_results = []

    # 1. Primary engine: Yahoo search (highly reliable, returns LinkedIn/Indeed/job sites)
    yahoo_results = search_yahoo(search_query, max_results=max_results)
    all_results.extend(yahoo_results)
    logger.info(f"Yahoo search yielded {len(yahoo_results)} results.")

    # 2. Secondary engine: DuckDuckGo HTML
    if len(all_results) < max_results:
        ddg_results = search_ddg_html(search_query, max_results=max_results - len(all_results))
        all_results.extend(ddg_results)
        logger.info(f"DDG search yielded {len(ddg_results)} results.")

    # 3. Tertiary engine: Wikipedia (great for historical events / facts)
    if len(all_results) < 5 or any(k in query.lower() for k in ["history", "event", "what happened", "who is", "what is"]):
        wiki_results = search_wikipedia(search_query, max_results=4)
        all_results.extend(wiki_results)
        logger.info(f"Wikipedia search yielded {len(wiki_results)} results.")

    # De-duplicate results by URL
    seen_urls = set()
    unique_results = []
    for r in all_results:
        url = r.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    logger.info(f"Final compiled search count: {len(unique_results)} items.")
    return unique_results[:max_results]

