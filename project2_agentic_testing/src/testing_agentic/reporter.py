from __future__ import annotations

import csv
from pathlib import Path

from .models import TestResult


def write_report(results: list[TestResult], output_dir: str = "reports") -> str:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    markdown_path = output_path / "report.md"
    csv_path = output_path / "report.csv"

    markdown_lines = ["# Rapport de testing\n"]
    for result in results:
        markdown_lines.append(f"- {result.id} | {result.canal} | {result.verdict} | {result.score}\n")
    markdown_path.write_text("".join(markdown_lines), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["id", "canal", "status", "score", "verdict"])
        for result in results:
            writer.writerow([result.id, result.canal, result.status, result.score, result.verdict])

    return str(markdown_path)
