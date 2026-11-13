"""资料来源:arXiv API、HuggingFace Daily Papers、RSS。仅使用标准库。"""
import gzip
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

UA = {"User-Agent": "ai-paper-monitoring/0.1"}
ATOM = "{http://www.w3.org/2005/Atom}"


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        # 部分站台(如 DeepMind)即使没要求也会回传 gzip
        if r.headers.get("Content-Encoding", "").lower() == "gzip":
            data = gzip.decompress(data)
        return data


def fetch_arxiv(categories, max_results, lookback_days):
    """arXiv API:依分类抓最新投稿。找法 = search_query=cat:xxx 依提交日期排序。"""
    query = " OR ".join(f"cat:{c}" for c in categories)
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    })
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    items = []
    root = ET.fromstring(_get(url))
    for e in root.findall(f"{ATOM}entry"):
        published = datetime.fromisoformat(e.find(f"{ATOM}published").text.replace("Z", "+00:00"))
        if published < cutoff:
            continue
        items.append({
            "id": e.find(f"{ATOM}id").text.strip(),
            "title": " ".join(e.find(f"{ATOM}title").text.split()),
            "summary": " ".join(e.find(f"{ATOM}summary").text.split()),
            "url": e.find(f"{ATOM}id").text.strip(),
            "authors": [a.find(f"{ATOM}name").text for a in e.findall(f"{ATOM}author")][:5],
            "published": published.date().isoformat(),
            "source": "arXiv",
            "found_via": f"arXiv API · {query}",
        })
    return items


def fetch_hf_daily():
    """HuggingFace Daily Papers(社群每日精选)。"""
    data = json.loads(_get("https://huggingface.co/api/daily_papers"))
    items = []
    for d in data:
        p = d.get("paper", {})
        pid = p.get("id")
        if not pid:
            continue
        items.append({
            "id": f"https://arxiv.org/abs/{pid}",
            "title": p.get("title", "").strip(),
            "summary": " ".join((p.get("summary") or "").split()),
            "url": f"https://huggingface.co/papers/{pid}",
            "authors": [a.get("name", "") for a in p.get("authors", [])][:5],
            "published": (p.get("publishedAt") or "")[:10],
            "source": "HuggingFace Daily Papers",
            "found_via": f"https://huggingface.co/papers · upvotes={p.get('upvotes', '?')}",
        })
    return items


def fetch_rss(name, url, limit=15):
    """官方博客 / 新闻 RSS(支援 RSS 2.0 与 Atom)。"""
    root = ET.fromstring(_get(url))
    items = []
    for it in root.iter("item"):
        items.append({
            "id": (it.findtext("link") or "").strip(),
            "title": (it.findtext("title") or "").strip(),
            "summary": " ".join((it.findtext("description") or "").split())[:600],
            "url": (it.findtext("link") or "").strip(),
            "authors": [],
            "published": (it.findtext("pubDate") or "")[:16],
            "source": name,
            "found_via": f"RSS · {url}",
        })
    for it in root.iter(f"{ATOM}entry"):
        link = it.find(f"{ATOM}link")
        href = link.get("href") if link is not None else ""
        items.append({
            "id": href,
            "title": (it.findtext(f"{ATOM}title") or "").strip(),
            "summary": " ".join((it.findtext(f"{ATOM}summary") or "").split())[:600],
            "url": href,
            "authors": [],
            "published": (it.findtext(f"{ATOM}updated") or "")[:10],
            "source": name,
            "found_via": f"RSS · {url}",
        })
    return items[:limit]
