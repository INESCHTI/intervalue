from __future__ import annotations

from collections import defaultdict
from pathlib import Path


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def _format_metric(value: object, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    return f"{value}{suffix}"


def write_markdown_report(results: list[dict], output_path: str = "reports/benchmark/report.md") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Rapport benchmark\n", "## Comparaison par modele\n"]

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        grouped[str(item.get("model", "inconnu"))].append(item)

    for model in sorted(grouped):
        items = grouped[model]
        successes = sum(1 for item in items if isinstance(item.get("status"), int))
        successful_items = [item for item in items if isinstance(item.get("status"), int)]
        avg_latency = _average([item["latency_s"] for item in successful_items if item.get("latency_s") is not None])
        avg_tokens_per_sec = _average(
            [item["tokens_per_sec"] for item in successful_items if item.get("tokens_per_sec") is not None]
        )
        avg_quality = _average(
            [item["quality_score"] for item in successful_items if item.get("quality_score") is not None]
        )
        lines.append(
            "- "
            f"{model}: {successes}/{len(items)} reponses reussies"
            f" | latence moyenne: {_format_metric(avg_latency, 's')}"
            f" | tokens/s moyen: {_format_metric(avg_tokens_per_sec)}"
            f" | qualite moyenne: {_format_metric(avg_quality)}\n"
        )

    lines.append("\n## Meilleur modele par tache\n")
    by_task: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        if isinstance(item.get("status"), int):
            by_task[str(item.get("task", "inconnue"))].append(item)

    for task in sorted(by_task):
        candidates = by_task[task]
        best = sorted(
            candidates,
            key=lambda item: (
                item.get("quality_score") if item.get("quality_score") is not None else -1,
                item.get("tokens_per_sec") if item.get("tokens_per_sec") is not None else -1,
                -(item.get("latency_s") if item.get("latency_s") is not None else 999999),
            ),
            reverse=True,
        )[0]
        lines.append(
            f"- {task}: {best.get('model')}"
            f" | qualite: {_format_metric(best.get('quality_score'))}"
            f" | latence: {_format_metric(best.get('latency_s'), 's')}"
            f" | tokens/s: {_format_metric(best.get('tokens_per_sec'))}\n"
        )

    lines.append("\n## Details et reponses exactes\n")
    for item in results:
        line = f"- {item.get('id')} [{item.get('model')}]: {item.get('status')}"
        if item.get("error"):
            line += f" | erreur: {item.get('error')}"
        if item.get("result"):
            line += (
                f" | tache: {item.get('task')}"
                f" | latence: {_format_metric(item.get('latency_s'), 's')}"
                f" | tokens: {_format_metric(item.get('token_count'))}"
                f" | tokens/s: {_format_metric(item.get('tokens_per_sec'))}"
                f" | qualite: {_format_metric(item.get('quality_score'))}"
            )
        lines.append(line + "\n")
        if item.get("result"):
            lines.append("\n```text\n")
            lines.append(str(item["result"]).strip() + "\n")
            lines.append("```\n\n")

    path.write_text("".join(lines), encoding="utf-8")
    return str(path)
