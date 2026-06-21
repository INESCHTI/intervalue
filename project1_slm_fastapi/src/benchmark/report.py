from __future__ import annotations

from pathlib import Path


def write_markdown_report(results: list[dict], output_path: str = "reports/benchmark/report.md") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Rapport benchmark\n"]
    for item in results:
        lines.append(f"- {item.get('id')}: {item.get('status')}\n")
    path.write_text("".join(lines), encoding="utf-8")
    return str(path)
