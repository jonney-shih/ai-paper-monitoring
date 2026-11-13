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

## 每天自动执行(Windows)
每台电脑设定一次即可,之后每天 08:00 自动跑(电脑当时关机则开机后补跑):
```
powershell -ExecutionPolicy Bypass -File .\setup_schedule.ps1            # 预设 08:00
powershell -ExecutionPolicy Bypass -File .\setup_schedule.ps1 -Time 07:30
powershell -ExecutionPolicy Bypass -File .\setup_schedule.ps1 -Remove    # 取消
```
流程:`run_daily.vbs`(静默)→ `run_daily.bat`(自动找 Python、执行 `main.py`、记录到 `data/run.log`)
→ `notify.vbs`/`notify.ps1`(跑完弹出对话框,按「确定」用 Chrome 开 `reports/index.html` 目录页)。

注意:`run_daily.vbs`、`run_daily.bat`、`notify.vbs` 不要写中文(Windows 会读错行);`notify.ps1` 需保留 UTF-8 BOM。

## 在另一台电脑上使用
1. 安装 Git、GitHub CLI 与 Python 3.9+(`winget install Git.Git GitHub.cli Python.Python.3.12`)。
2. `gh auth login`,再 `gh repo clone jonney-shih/ai-paper-monitoring`。
3. 进入资料夹,执行上面的 `setup_schedule.ps1`。
4. 可立即试跑:`Start-ScheduledTask AI-Paper-Monitoring-Daily`。

`data/` 与 `reports/` 不会上传 GitHub,每台电脑各自记录「已看过」与产生报告,
因此两台电脑的报告内容可能略有不同;之后更新程序只需 `git pull`。

## 后续可扩充
- 把报告交给 Claude 产生繁体中文摘要与重点(报告内已预留栏位)
- 加入 X(Twitter)动态:官方 API 按量计费,或先用手动「收件匣」方式
- 加入 GitHub Trending / Papers with Code / 会议(NeurIPS、ICLR、CoRL)来源
