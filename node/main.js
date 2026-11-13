// AI 前沿论文监控(Node 版):抓取 → 去重 → 分类 → 输出 reports/YYYY-MM-DD.md
// 用法: node main.js [--top 8]
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { fetchArxiv, fetchHfDaily, fetchRss } from "./sources.js";
import { classify, render } from "./report.js";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SEEN = path.join(ROOT, "data", "seen.json");

const topIdx = process.argv.indexOf("--top");
const top = topIdx > -1 ? Number(process.argv[topIdx + 1]) : 8;

async function safe(label, fn) {
  try { return await fn(); } catch (e) { console.error(`[warn] ${label} 失败: ${e.message}`); return []; }
}

const cfg = JSON.parse(await readFile(path.join(ROOT, "config.json"), "utf8"));
let seen = new Set();
try { seen = new Set(JSON.parse(await readFile(SEEN, "utf8"))); } catch {}

let papers = [], news = [];
if (cfg.arxiv.enabled)
  papers.push(...await safe("arXiv", () => fetchArxiv(cfg.arxiv.categories, cfg.max_per_source, cfg.lookback_days)));
if (cfg.huggingface_daily.enabled)
  papers.push(...await safe("HF Daily", fetchHfDaily));
if (cfg.rss.enabled)
  for (const f of cfg.rss.feeds) news.push(...await safe(f.name, () => fetchRss(f.name, f.url)));

const ids = new Set();
const fresh = papers.filter((p) => {
  if (seen.has(p.id) || ids.has(p.id)) return false;
  ids.add(p.id);
  return true;
});
news = news.filter((n) => n.id && !seen.has(n.id));

const byTopic = Object.fromEntries(Object.keys(cfg.topics).map((t) => [t, []]));
for (const p of fresh)
  for (const [t, score] of Object.entries(classify(p, cfg.topics))) byTopic[t].push([score, p]);
for (const t of Object.keys(byTopic))
  byTopic[t] = byTopic[t].sort((a, b) => b[0] - a[0]).slice(0, top).map(([, p]) => p);

const out = path.join(ROOT, "reports", `${new Date().toISOString().slice(0, 10)}.md`);
await mkdir(path.dirname(out), { recursive: true });
await writeFile(out, render(byTopic, news.slice(0, 15)), "utf8");

await mkdir(path.dirname(SEEN), { recursive: true });
await writeFile(SEEN, JSON.stringify([...new Set([...seen, ...ids, ...news.map((n) => n.id)])].sort()), "utf8");
console.log(`完成:${out}  (论文 ${fresh.length} 篇,新闻 ${news.length} 则)`);
