// 资料来源:arXiv API、HuggingFace Daily Papers、RSS。使用 Node 内建 fetch,无第三方依赖。
const UA = { "User-Agent": "ai-paper-monitoring/0.1" };

async function get(url) {
  const res = await fetch(url, { headers: UA, signal: AbortSignal.timeout(30000) });
  if (!res.ok) throw new Error(`HTTP ${res.status} ${url}`);
  return res.text();
}

const decode = (s = "") =>
  s.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'").replace(/&amp;/g, "&")
    .replace(/\s+/g, " ").trim();

const tag = (block, name) => {
  const m = block.match(new RegExp(`<${name}[^>]*>([\\s\\S]*?)</${name}>`));
  return m ? decode(m[1]) : "";
};
const blocks = (xml, name) =>
  [...xml.matchAll(new RegExp(`<${name}[ >][\\s\\S]*?</${name}>`, "g"))].map((m) => m[0]);

// arXiv API:依分类抓最新投稿。找法 = search_query=cat:xxx 依提交日期排序。
export async function fetchArxiv(categories, maxResults, lookbackDays) {
  const query = categories.map((c) => `cat:${c}`).join(" OR ");
  const params = new URLSearchParams({
    search_query: query, sortBy: "submittedDate", sortOrder: "descending", max_results: String(maxResults),
  });
  const xml = await get(`http://export.arxiv.org/api/query?${params}`);
  const cutoff = Date.now() - lookbackDays * 86400000;
  const items = [];
  for (const e of blocks(xml, "entry")) {
    const published = tag(e, "published");
    if (new Date(published).getTime() < cutoff) continue;
    const id = tag(e, "id");
    items.push({
      id, title: tag(e, "title"), summary: tag(e, "summary"), url: id,
      authors: blocks(e, "author").map((a) => tag(a, "name")).slice(0, 5),
      published: published.slice(0, 10), source: "arXiv", foundVia: `arXiv API · ${query}`,
    });
  }
  return items;
}

// HuggingFace Daily Papers(社群每日精选)
export async function fetchHfDaily() {
  const data = JSON.parse(await get("https://huggingface.co/api/daily_papers"));
  return data.filter((d) => d.paper?.id).map((d) => {
    const p = d.paper;
    return {
      id: `https://arxiv.org/abs/${p.id}`, title: (p.title || "").trim(),
      summary: (p.summary || "").replace(/\s+/g, " ").trim(),
      url: `https://huggingface.co/papers/${p.id}`,
      authors: (p.authors || []).map((a) => a.name || "").slice(0, 5),
      published: (p.publishedAt || "").slice(0, 10),
      source: "HuggingFace Daily Papers",
      foundVia: `https://huggingface.co/papers · upvotes=${p.upvotes ?? "?"}`,
    };
  });
}

// 官方博客 / 新闻 RSS(RSS 2.0 与 Atom)
export async function fetchRss(name, url, limit = 15) {
  const xml = await get(url);
  const items = blocks(xml, "item").map((it) => ({
    id: tag(it, "link"), title: tag(it, "title"), summary: tag(it, "description").slice(0, 600),
    url: tag(it, "link"), authors: [], published: tag(it, "pubDate").slice(0, 16),
    source: name, foundVia: `RSS · ${url}`,
  }));
  for (const it of blocks(xml, "entry")) {
    const href = (it.match(/<link[^>]*href="([^"]+)"/) || [])[1] || "";
    items.push({
      id: href, title: tag(it, "title"), summary: tag(it, "summary").slice(0, 600), url: href,
      authors: [], published: tag(it, "updated").slice(0, 10), source: name, foundVia: `RSS · ${url}`,
    });
  }
  return items.slice(0, limit);
}
