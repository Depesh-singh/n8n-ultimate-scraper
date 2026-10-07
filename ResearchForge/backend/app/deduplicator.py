import hashlib
from urllib.parse import urlparse, urlunparse

def clean_url(url: str) -> str:
    """
    Cleans a URL by removing common tracking parameters (utm_*, etc.)
    to ensure duplicate links with different tracking IDs are matched.
    """
    try:
        parsed = urlparse(url)
        # Keep query parameters that are not utm or generic tracking params
        if parsed.query:
            queries = [q for q in parsed.query.split("&") if not q.startswith(("utm_", "ref", "source"))]
            new_query = "&".join(queries)
            parsed = parsed._replace(query=new_query)
        # Remove fragment
        parsed = parsed._replace(fragment="")
        return urlunparse(parsed)
    except Exception:
        return url

def generate_content_hash(url: str, title: str) -> str:
    """
    Generates a unique MD5 hash for the combination of url and title.
    """
    cleaned = clean_url(url).strip().lower()
    cleaned_title = title.strip().lower()
    combined = f"{cleaned}||{cleaned_title}"
    return hashlib.md5(combined.encode("utf-8")).hexdigest()
