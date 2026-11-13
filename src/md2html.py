"""把 reports/ 里的 .md 重新转成 .html(例如手动补写「中文重点」之后)。

用法:
  python src/md2html.py              # 转今天的
  python src/md2html.py 2026-11-12   # 转指定日期
  python src/md2html.py --all        # 全部重转
  python src/md2html.py path\\to\\x.md  # 指定档案
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from report import build_index, md_to_html

REPORTS = Path(__file__).resolve().parent.parent / "reports"


def convert(md_path):
    md_path = Path(md_path)
    out = md_path.with_suffix(".html")
    out.write_text(md_to_html(md_path.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"已转换:{out}")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    if arg == "--all":
        files = sorted(REPORTS.glob("*.md"))
    elif arg.endswith(".md"):
        files = [Path(arg)]
    else:
        files = [REPORTS / f"{arg}.md"]
    missing = [f for f in files if not f.exists()]
    if missing or not files:
        sys.exit("找不到报告:" + ", ".join(str(f) for f in missing or [REPORTS]))
    for f in files:
        convert(f)
    print(f"已更新目录:{build_index(REPORTS)}")


if __name__ == "__main__":
    main()
