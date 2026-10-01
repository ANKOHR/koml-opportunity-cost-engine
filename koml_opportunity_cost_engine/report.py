"""Reports explicitly label hypothetical figures and input provenance."""
import json


def render(result, format="md"):
    if format not in ("md", "json"):
        raise ValueError("unsupported report format")
    required = {"provenance", "figure_status", "currency", "as_of", "records", "decision_count", "dominated_count", "selected_value_total", "foregone_value_total", "avoidable_gap_total", "decisions"}
    if not isinstance(result, dict) or not required <= result.keys():
        raise ValueError("missing result fields")
    if result["figure_status"] != "HYPOTHETICAL input valuations; computed comparisons, not measured savings or predictions":
        raise ValueError("invalid figure status")
    if result["provenance"] not in ("SYNTHETIC fixtures", "REAL inputs entered by Henry", "NO INPUT RECORDS"):
        raise ValueError("invalid provenance")
    if chr(8212) in json.dumps(result, ensure_ascii=False):
        raise ValueError("forbidden punctuation U+2014")
    if format == "json":
        return json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    lines = ["# KOML Opportunity Cost Engine", "", f"Data provenance: {result['provenance']}", f"Figure status: {result['figure_status']}", "", f"Records: {result['records']}", f"Decisions: {result['decision_count']}", f"Dominated choices: {result['dominated_count']}", f"Hypothetical selected value (GBP): {result['selected_value_total']}", f"Hypothetical foregone alternative value (GBP): {result['foregone_value_total']}", f"Hypothetical avoidable gap (GBP): {result['avoidable_gap_total']}", "", "Each alternative is mutually exclusive with the chosen task in its decision.", "", "| Decision | Selected ID | Best alternative ID | Hypothetical selected GBP | Hypothetical foregone GBP | Hypothetical gap GBP |", "| --- | --- | --- | --- | --- | --- |"]
    def cell(value):
        return str(value).replace("|", "&#124;").replace("\n", " ").replace("\r", " ").replace("<", "&lt;").replace(">", "&gt;")
    for row in result["decisions"]:
        lines.append("| " + " | ".join(cell(row[k]) for k in ("decision", "selected_id", "best_alternative_id", "selected_value", "foregone_value", "avoidable_gap")) + " |")
    return "\n".join(lines) + "\n"
