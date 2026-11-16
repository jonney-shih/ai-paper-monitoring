"""产生每日 Markdown 报告。"""
import html
import re
from datetime import date

TOPIC_LABEL = {"model": "Model(模型)", "agentic": "Agentic Engineering", "physical_ai": "Physical AI"}


def classify(item, topics):
    text = f"{item['title']} {item['summary']}".lower()
    hits = {}
    for topic, kws in topics.items():
        n = sum(1 for k in kws if re.search(r"\b" + re.escape(k.lower()) + r"\b", text))
        if n:
            hits[topic] = n
    return hits


def short_summary(text, n=2):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:n])


_HTML_CSS = """
body{font-family:"Microsoft JhengHei","Segoe UI",sans-serif;max-width:860px;margin:2rem auto;padding:0 1rem;
line-height:1.6;color:#222;background:#fff}
h1{border-bottom:2px solid #444;padding-bottom:.3rem}
h2{margin-top:2.2rem;border-left:5px solid #2b6cb0;padding-left:.6rem}
h3{margin:1.6rem 0 .3rem;font-size:1.05rem}
ul{margin:.2rem 0 .8rem;padding-left:1.3rem}li{margin:.15rem 0}
a{color:#1a56a8;text-decoration:none}a:hover{text-decoration:underline}
em{color:#777}
@media (prefers-color-scheme:dark){body{background:#1b1b1f;color:#e6e6e6}a{color:#7db3ff}em{color:#999}
h1{border-color:#888}h2{border-color:#4a90d9}}
"""


def _inline(s):
    s = html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank">\1</a>', s)
    s = re.sub(r"(?<![\"=>])(https?://[^\s<)]+)", r'<a href="\1" target="_blank">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"(?<![\w])_([^_]+)_(?![\w])", r"<em>\1</em>", s)


def md_to_html(md):
    """把 render() 产生的简单 Markdown(标题/清单/链接/斜体)转成 HTML 页面。"""
    body, in_ul, title = [], False, "AI 前沿每日简报"
    for line in md.splitlines():
        if in_ul and not line.startswith(("- ", "  - ")):
            body.append("</ul>")
            in_ul = False
        if line.startswith("# "):
            title = line[2:]
            body.append(f"<h1>{_inline(title)}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("  - "):
            body.append(f'<li style="margin-left:1.2rem;list-style:circle">{_inline(line[4:])}</li>')
        elif line.startswith("- "):
            if not in_ul:
                body.append("<ul>")
                in_ul = True
            body.append(f"<li>{_inline(line[2:])}</li>")
        elif line.strip():
            body.append(f"<p>{_inline(line)}</p>")
    if in_ul:
        body.append("</ul>")
    return (f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{_HTML_CSS}</style></head>"
            f"<body>{chr(10).join(body)}</body></html>")


def build_index(reports_dir):
    """在 reports/ 产生 index.html:列出所有日期的报告,最新的在最上面。"""
    from pathlib import Path
    rows = []
    for md in sorted(Path(reports_dir).glob("????-??-??.md"), reverse=True):
        day = md.stem
        lines = md.read_text(encoding="utf-8").splitlines()
        papers = sum(1 for l in lines if l.startswith("### "))
        news, in_news = 0, False
        for l in lines:
            if l.startswith("## "):
                in_news = l.startswith("## 重大消息")
            elif in_news and l.startswith("- ["):
                news += 1
        link = f'<a href="{day}.html">{day}</a>' if md.with_suffix(".html").exists() else day
        rows.append(f"<li>{link}<span>论文 {papers} 篇 · 新闻 {news} 则</span>"
                    f'<a class="md" href="{day}.md">md</a></li>')
    css = _HTML_CSS + (
        "ul.idx{list-style:none;padding:0}ul.idx li{display:flex;gap:1rem;align-items:baseline;"
        "padding:.55rem .2rem;border-bottom:1px solid #8884}ul.idx li>a:first-child{font-weight:600;"
        "min-width:7.5rem}ul.idx span{color:#777;flex:1}a.md{font-size:.8rem;opacity:.7}")
    page = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>AI 前沿每日简报 · 目录</title><style>{css}</style></head><body>"
            "<h1>AI 前沿每日简报 · 目录</h1>"
            f'<ul class="idx">{"".join(rows) or "<li>还没有报告</li>"}</ul></body></html>')
    out = Path(reports_dir) / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


def _x_section(x_posts):
    """「X 动态」区块。x_posts: 每则含 topic/handle/url/summary,另有 time/likes/views/note。
    故意不用 ### 标题,以免目录页把它算成论文。"""
    out = ["## X 动态", ""]
    if not x_posts:
        return out + ["_今日尚未读取 X 动态(需请 Claude 读取,见 README)。_", ""]
    for topic in TOPIC_LABEL:
        rows = [p for p in x_posts if p.get("topic") == topic]
        if not rows:
            continue
        out += [f"**{TOPIC_LABEL[topic]}**", ""]
        for p in rows:
            meta = " · ".join(str(x) for x in (p.get("time"), p.get("likes") and f"{p['likes']} 赞",
                                               p.get("views") and f"{p['views']} 浏览") if x)
            out.append(f"- [@{p['handle']}]({p['url']}) — {p['summary']}" + (f"({meta})" if meta else ""))
            if p.get("note"):
                out.append(f"  - ⚠ {p['note']}")
        out.append("")
    return out + ["_来源:X 搜索(手动读取),未逐则查证,使用前请开原文确认。_", ""]


def render(items_by_topic, news, today=None, x_posts=None):
    today = today or date.today().isoformat()
    out = [f"# AI 前沿每日简报 · {today}", ""]
    for topic, items in items_by_topic.items():
        out += [f"## {TOPIC_LABEL.get(topic, topic)}", ""]
        if not items:
            out += ["_今日无符合条件的新论文。_", ""]
        for it in items:
            out += [
                f"### [{it['title']}]({it['url']})",
                f"- 来源:{it['source']} · 发布:{it['published']}"
                + (f" · 作者:{', '.join(it['authors'])}" if it["authors"] else ""),
                f"- 摘要(原文节选):{short_summary(it['summary'])}",
                f"- 如何找到:{it['found_via']}",
                "- 中文重点:_(待补:可交给 Claude 依摘要产生繁中重点)_",
                "",
            ]
    out += ["## 重大消息", ""]
    if not news:
        out += ["_今日无新消息。_", ""]
    for it in news:
        out += [f"- [{it['title']}]({it['url']}) — {it['source']} ({it['published']})"]
    out.append("")
    out += _x_section(x_posts)
    return "\n".join(out)
