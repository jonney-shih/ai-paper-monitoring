"""AI 前沿论文监控:抓取 → 去重 → 分类 → 输出 reports/YYYY-MM-DD.md

用法:  python src/main.py [--top 8]
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import sources
from report import build_index, classify, md_to_html, render

ROOT = Path(__file__).resolve().parent.parent
SEEN = ROOT / "data" / "seen.json"
NEWS_PER_SOURCE = 4
DAILY = ROOT / "data" / "daily"  # 当天已抓内容的暂存,供同日重跑合并


def load_seen():
    try:
        return set(json.loads(SEEN.read_text(encoding="utf-8")))
    except Exception:
        return set()


def safe(label, fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except Exception as e:  # 单一来源失败不影响其他来源
        print(f"[warn] {label} 失败: {e}", file=sys.stderr)
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=8, help="每个主题最多列出几篇")
    args = ap.parse_args()

    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    papers, news = [], []

    if cfg["arxiv"]["enabled"]:
        papers += safe("arXiv", sources.fetch_arxiv, cfg["arxiv"]["categories"],
                       cfg["max_per_source"], cfg["lookback_days"])
    if cfg["huggingface_daily"]["enabled"]:
        papers += safe("HF Daily", sources.fetch_hf_daily)
    if cfg["rss"]["enabled"]:
        for f in cfg["rss"]["feeds"]:
            news += safe(f["name"], sources.fetch_rss, f["name"], f["url"])

    seen = load_seen()
    fresh, ids = [], set()
    for p in papers:
        if p["id"] in seen or p["id"] in ids:
            continue
        ids.add(p["id"])
        fresh.append(p)
    news = [n for n in news if n["id"] and n["id"] not in seen]

    # 同一天重跑:合并当天已抓到的内容,避免覆盖掉先前的报告
    today = date.today().isoformat()
    cache = DAILY / f"{today}.json"
    try:
        prev = json.loads(cache.read_text(encoding="utf-8"))
    except Exception:
        prev = {"papers": [], "news": []}
    have_p = {p["id"] for p in fresh}
    have_n = {n["id"] for n in news}
    fresh = fresh + [p for p in prev["papers"] if p["id"] not in have_p]
    news = news + [n for n in prev["news"] if n["id"] not in have_n]
    ids = {p["id"] for p in fresh}
    DAILY.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"papers": fresh, "news": news}, ensure_ascii=False), encoding="utf-8")

    by_topic = {t: [] for t in cfg["topics"]}
    for p in fresh:
        hits = classify(p, cfg["topics"])
        for t, score in hits.items():
            by_topic[t].append((score, p))
    for t in by_topic:
        by_topic[t] = [p for _, p in sorted(by_topic[t], key=lambda x: -x[0])][: args.top]

    out = ROOT / "reports" / f"{date.today().isoformat()}.md"
    # 重大消息:每个来源各列 NEWS_PER_SOURCE 则,避免被前面的来源占满
    counts, picked = {}, []
    for n in news:
        if counts.get(n["source"], 0) < NEWS_PER_SOURCE:
            counts[n["source"]] = counts.get(n["source"], 0) + 1
            picked.append(n)
    md = render(by_topic, picked)
    out.parent.mkdir(exist_ok=True)  # 新环境(例如刚 clone 下来)可能还没有 reports/
    out.write_text(md, encoding="utf-8")
    out.with_suffix(".html").write_text(md_to_html(md), encoding="utf-8")
    build_index(out.parent)

    SEEN.parent.mkdir(exist_ok=True)
    SEEN.write_text(json.dumps(sorted(seen | ids | {n["id"] for n in news})), encoding="utf-8")
    print(f"完成:{out}  (论文 {len(fresh)} 篇,新闻 {len(news)} 则)")


if __name__ == "__main__":
    main()
