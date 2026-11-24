"""资料来源:arXiv API、HuggingFace Daily Papers、RSS。仅使用标准库。"""
import gzip
import json
import re
import time
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


ARXIV_NS = "{http://arxiv.org/schemas/atom}"
_ACCEPT = re.compile(r"\b(accepted|to appear|camera[- ]?ready|appearing|oral|spotlight|best paper|outstanding|award|highlight)\b", re.I)
_REJECT = re.compile(r"workshop|under review|in review|submitted|submission|withdrawn|not accepted|rejected|tutorial|demo\b", re.I)
_HIGH = re.compile(r"\b(oral|spotlight|best paper|outstanding|award|highlight)\b", re.I)


def fetch_conference(name, query, lookback_days=14, per_venue=5):
    """会议论文:从 arXiv 备注栏找作者自述「已录取」的主会论文(OpenReview 有人机验证,不用)。
    过滤掉 workshop 与审稿中的;标有 oral/spotlight/best paper/award 的排前面。"""
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f'co:"{query}"', "sortBy": "submittedDate", "sortOrder": "descending", "max_results": 100})
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    rows = []
    for e in ET.fromstring(_get(url)).findall(f"{ATOM}entry"):
        published = datetime.fromisoformat(e.find(f"{ATOM}published").text.replace("Z", "+00:00"))
        comment = " ".join((e.findtext(f"{ARXIV_NS}comment") or "").split())
        if published < cutoff or not _ACCEPT.search(comment) or _REJECT.search(comment):
            continue
        link = e.find(f"{ATOM}id").text.strip()
        summary = " ".join(e.find(f"{ATOM}summary").text.split())
        rows.append((0 if _HIGH.search(comment) else 1, -published.timestamp(), {
            "id": "conf:" + link, "title": " ".join(e.find(f"{ATOM}title").text.split()),
            "summary": summary[:300], "url": link, "source": name, "published": published.date().isoformat(),
            "authors": [], "note": comment[:110], "found_via": f"arXiv 备注栏 · {query}"}))
    return [r[2] for r in sorted(rows, key=lambda r: (r[0], r[1]))[:per_venue]]


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


MEDIA = "{http://search.yahoo.com/mrss/}"


def _parse_dt(s):
    """RSS(RFC 822)或 Atom(ISO 8601)日期 → 带时区的 datetime;失败回 None。"""
    s = (s or "").strip()
    if not s:
        return None
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(s)
    except Exception:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def fetch_media(name, url, group, per_source=2, lookback_days=7):
    """YouTube 频道 / 播客 / newsletter 的 RSS(Atom):只取近 lookback_days 天、每个来源最多 per_source 则。"""
    root = ET.fromstring(_get(url))
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    items = []
    for it in root.iter("item"):
        ts = _parse_dt(it.findtext("pubDate"))
        link = (it.findtext("link") or "").strip()
        items.append((ts, link, (it.findtext("title") or "").strip(),
                      " ".join((it.findtext("description") or "").split())))
    for it in root.iter(f"{ATOM}entry"):
        link = it.find(f"{ATOM}link")
        href = link.get("href") if link is not None else ""
        ts = _parse_dt(it.findtext(f"{ATOM}published") or it.findtext(f"{ATOM}updated"))
        desc = it.findtext(f"{ATOM}summary") or it.findtext(f"{MEDIA}group/{MEDIA}description") or ""
        items.append((ts, href, (it.findtext(f"{ATOM}title") or "").strip(), " ".join(desc.split())))
    out = []
    # 略过 YouTube Shorts(几十秒的短片,信息量低,会占掉名额)
    for ts, link, title, desc in sorted((i for i in items if i[0] and i[1] and "/shorts/" not in i[1]),
                                        key=lambda i: i[0], reverse=True):
        if ts < cutoff or len(out) >= per_source:
            break
        out.append({"id": link, "title": title, "url": link, "summary": desc[:300], "source": name,
                    "group": group, "published": ts.date().isoformat(), "authors": [],
                    "found_via": f"RSS · {url}"})
    return out


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
