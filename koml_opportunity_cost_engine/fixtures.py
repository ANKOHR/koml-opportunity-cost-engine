"""Synthetic deterministic fixtures, no randomness or seed required."""
import json
from pathlib import Path


def fixture_data():
    records = []
    for group in range(40):
        values = [100, 150 if group % 2 == 0 else 80, 60, 40, 20]
        for candidate, value in enumerate(values):
            records.append({"id": f"task-{group:02}-{candidate}", "decision": f"decision-{group:02}", "title": f"Synthetic task {group}/{candidate}", "date": "2026-09-30", "selected": candidate == 0, "value": f"{value}.00", "synthetic": True})
    return {"synthetic": True, "entered_by": "fixture generator", "as_of": "2026-09-30", "currency": "GBP", "records": records}


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    data = fixture_data()
    for name, records in (("tasks.json", data["records"]), ("tiny/tasks.json", data["records"][:5])):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(data, records=records), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    expected = {"synthetic": True, "records": 200, "decision_count": 40, "dominated_count": 20, "selected_value_total": "4000.00", "foregone_value_total": "4600.00", "avoidable_gap_total": "1000.00", "dominated_decisions": [f"decision-{g:02}" for g in range(0, 40, 2)]}
    (out / "expectations.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    (out / "SYNTHETIC.md").write_text("<!-- SYNTHETIC fixtures -->\n# Synthetic data\nNo real observations. Hand calculation: 40 * 100 = 4000; 20 * 150 + 20 * 80 = 4600; 20 * 50 = 1000. Exactly the 20 even-numbered decisions are dominated. JSON cannot carry header comments; all JSON files carry synthetic: true.\n", encoding="utf-8")
