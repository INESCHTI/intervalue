from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .models import EvaluationResult


class ReporterAgent:
    """Reporter Agent: write Markdown, JSON, and CSV test evidence."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def write(self, results: list[EvaluationResult]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        markdown = self.output_dir / "report.md"
        json_path = self.output_dir / "results.json"
        csv_path = self.output_dir / "results.csv"

        markdown.write_text(self._markdown(results), encoding="utf-8")
        json_path.write_text(
            json.dumps([asdict(result) for result in results], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                ["id", "channel", "intent", "status", "latency_s", "score", "hallucination", "verdict"]
            )
            for result in results:
                writer.writerow(
                    [
                        result.id,
                        result.channel,
                        result.intent,
                        result.status,
                        result.latency_s,
                        result.score,
                        result.hallucination,
                        result.verdict,
                    ]
                )
        return markdown

    def _markdown(self, results: list[EvaluationResult]) -> str:
        total = len(results)
        passed = sum(1 for result in results if result.verdict == "PASS")
        failed = sum(1 for result in results if result.verdict == "FAIL")
        warned = sum(1 for result in results if result.verdict == "WARN")
        rate = round((passed / total) * 100, 1) if total else 0

        lines = [
            "# Aurevia Agentic Testing Report\n\n",
            "## Summary\n\n",
            f"- Success rate: {rate}% ({passed}/{total})\n",
            f"- PASS: {passed}\n",
            f"- WARN: {warned}\n",
            f"- FAIL: {failed}\n\n",
            "## Results\n\n",
            "| ID | Channel | Intent | Latency | Score | Hallucination | Verdict |\n",
            "|---|---|---|---:|---:|---|---|\n",
        ]
        for result in results:
            lines.append(
                f"| {result.id} | {result.channel} | {result.intent} | "
                f"{result.latency_s}s | {result.score} | {result.hallucination} | {result.verdict} |\n"
            )

        critical = [result for result in results if result.verdict == "FAIL"][:3]
        lines.extend(["\n## Top Critical Failures\n\n"])
        if not critical:
            lines.append("- None.\n")
        for result in critical:
            lines.append(f"- {result.id}: {result.reason}\n")

        lines.extend(["\n## Evidence\n\n"])
        for result in results:
            lines.append(f"### {result.id} ({result.channel})\n\n")
            lines.append(f"- Verdict: {result.verdict}\n")
            lines.append(f"- Reason: {result.reason}\n")
            lines.append(f"- Expected keywords: {', '.join(result.expected_keywords)}\n")
            if result.screenshot:
                lines.append(f"- Screenshot: `{result.screenshot}`\n")
            if result.ocr_text:
                lines.append(f"- OCR text: {result.ocr_text[:500]}\n")
            if result.error:
                lines.append(f"- Error: {result.error}\n")
            lines.append("\n```text\n")
            lines.append((result.actual or "").strip()[:2000])
            lines.append("\n```\n\n")

        lines.extend(
            [
                "## Recommendations\n\n",
                "- Treat every FAIL as a regression candidate.\n",
                "- Run API cases before merge; run Playwright DOM/OCR cases nightly or before demos.\n",
                "- Use `AUREVIA_TARGET=minikube` to validate the Kubernetes deployment path.\n",
            ]
        )
        return "".join(lines)


