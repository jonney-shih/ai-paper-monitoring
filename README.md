# AI advanced paper monitoring

每天找出网路上有关 AI(model、agentic engineering、physical AI)最前沿的论文与重大消息,
附摘要与「如何找到」的来源说明。

## 结构
- `config.json` — 主题关键字、arXiv 分类、RSS 清单、回溯天数
- `src/sources.py` — arXiv API / HuggingFace Daily Papers / RSS 抓取
- `src/report.py` — 分类与 Markdown 报告产生
- `src/main.py` — 主程式入口
- `reports/` — 每日报告 `YYYY-MM-DD.md`
- `data/seen.json` — 已处理项目(去重用)
- `node/` — Node.js 版(功能与 Python 版相同,共用 `config.json`、`reports/`、`data/`)

## 执行
```
python src/main.py --top 8
```
仅需 Python 3.9+,无第三方套件。单一来源失败会略过并在 stderr 提示。

### Node.js 版
```
node node/main.js --top 8
```
需 Node 18+,无第三方套件。两个版本共用同一份 `data/seen.json`,同一天先后执行会互相去重。

## 后续可扩充
- 把报告交给 Claude 产生繁体中文摘要与重点(报告内已预留栏位)
- 用排程(Windows Task Scheduler 或 Claude 排程任务)每天自动执行
- 加入 GitHub Trending / Papers with Code / 会议(NeurIPS、ICLR、CoRL)来源
