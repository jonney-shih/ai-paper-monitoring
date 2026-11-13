// 分类与每日 Markdown 报告产生
const TOPIC_LABEL = { model: "Model(模型)", agentic: "Agentic Engineering", physical_ai: "Physical AI" };
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function classify(item, topics) {
  const text = `${item.title} ${item.summary}`.toLowerCase();
  const hits = {};
  for (const [topic, kws] of Object.entries(topics)) {
    const n = kws.filter((k) => new RegExp(`\\b${esc(k.toLowerCase())}\\b`).test(text)).length;
    if (n) hits[topic] = n;
  }
  return hits;
}

const shortSummary = (t, n = 2) => t.trim().split(/(?<=[.!?])\s+/).slice(0, n).join(" ");

export function render(byTopic, news, today = new Date().toISOString().slice(0, 10)) {
  const out = [`# AI 前沿每日简报 · ${today}`, ""];
  for (const [topic, items] of Object.entries(byTopic)) {
    out.push(`## ${TOPIC_LABEL[topic] ?? topic}`, "");
    if (!items.length) out.push("_今日无符合条件的新论文。_", "");
    for (const it of items) {
      out.push(
        `### [${it.title}](${it.url})`,
        `- 来源:${it.source} · 发布:${it.published}` + (it.authors.length ? ` · 作者:${it.authors.join(", ")}` : ""),
        `- 摘要(原文节选):${shortSummary(it.summary)}`,
        `- 如何找到:${it.foundVia}`,
        "- 中文重点:_(待补:可交给 Claude 依摘要产生繁中重点)_",
        "",
      );
    }
  }
  out.push("## 重大消息", "");
  if (!news.length) out.push("_今日无新消息。_", "");
  for (const n of news) out.push(`- [${n.title}](${n.url}) — ${n.source} (${n.published})`);
  out.push("");
  return out.join("\n");
}
