"""Pure deterministic arithmetic. Values are hypothetical, never measured savings."""
from datetime import date
from decimal import Decimal, InvalidOperation


class InputError(ValueError):
    """Named input validation failure."""


def validate(data):
    if not isinstance(data, dict):
        raise InputError("SchemaError: root must be an object")
    required = {"synthetic", "entered_by", "as_of", "currency", "records"}
    if set(data) != required:
        raise InputError(f"SchemaError: root fields: {sorted(set(data) ^ required)}")
    if not isinstance(data["entered_by"], str) or not 1 <= len(data["entered_by"]) <= 10000 or chr(8212) in data["entered_by"]:
        raise InputError("SchemaError: entered_by must contain 1..10000 characters without U+2014")
    if type(data["synthetic"]) is not bool:
        raise InputError("SchemaError: synthetic must be boolean")
    if not data["synthetic"] and data["entered_by"] != "Henry":
        raise InputError("SchemaError: real data must be entered_by Henry")
    if data["currency"] != "GBP":
        raise InputError("SchemaError: currency must be GBP")
    try:
        cutoff = date.fromisoformat(data["as_of"])
    except (TypeError, ValueError):
        raise InputError("SchemaError: as_of must be an ISO date") from None
    if not isinstance(data["records"], list):
        raise InputError("SchemaError: records must be a list")
    seen = set()
    groups = {}
    fields = {"id", "decision", "title", "date", "selected", "value", "synthetic"}
    for index, row in enumerate(data["records"], 1):
        prefix = f"SchemaError: record {index}"
        if not isinstance(row, dict) or set(row) != fields:
            raise InputError(f"{prefix}: offending fields {sorted(set(row) ^ fields) if isinstance(row, dict) else 'record'}")
        for key in ("id", "decision", "title"):
            if not isinstance(row[key], str) or not 1 <= len(row[key]) <= 10000:
                raise InputError(f"{prefix}: {key} must contain 1..10000 characters")
            if chr(8212) in row[key]:
                raise InputError(f"{prefix}: {key} contains forbidden punctuation U+2014")
        if row["id"] in seen:
            raise InputError(f"{prefix}: duplicate id {row['id']}")
        seen.add(row["id"])
        if type(row["selected"]) is not bool or type(row["synthetic"]) is not bool or row["synthetic"] != data["synthetic"]:
            raise InputError(f"{prefix}: selected/synthetic invalid or provenance mismatch")
        try:
            when = date.fromisoformat(row["date"])
            if when > cutoff:
                raise ValueError()
        except (TypeError, ValueError):
            raise InputError(f"{prefix}: date invalid or future relative to as_of") from None
        try:
            if not isinstance(row["value"], str):
                raise ValueError()
            value = Decimal(row["value"])
            if not value.is_finite() or value < 0 or value > 1000000000 or value != value.quantize(Decimal('.01')):
                raise ValueError()
        except (InvalidOperation, ValueError):
            raise InputError(f"{prefix}: value must be a nonnegative decimal string with at most two fractional digits, <= 1000000000") from None
        groups.setdefault(row["decision"], []).append((row, value))
    for key, rows in groups.items():
        if len({r["date"] for r, _ in rows}) != 1:
            raise InputError(f"SchemaError: decision {key} requires a shared date")
        if sum(r["selected"] for r, _ in rows) != 1 or len(rows) < 2:
            raise InputError(f"SchemaError: decision {key} requires one selected task and at least one alternative")
    return groups


def money(value):
    return format(value, '.2f')


def evaluate(data):
    groups = validate(data)
    decisions = []
    chosen_total = Decimal(0)
    alternative_total = Decimal(0)
    regret_total = Decimal(0)
    for key, rows in sorted(groups.items()):
        chosen, value = next((r, v) for r, v in rows if r["selected"])
        alternative, other = sorted(((r, v) for r, v in rows if not r["selected"]), key=lambda pair: (-pair[1], pair[0]["id"]))[0]
        regret = max(Decimal(0), other - value)
        chosen_total += value
        alternative_total += other
        regret_total += regret
        decisions.append({"decision": key, "selected_id": chosen["id"], "best_alternative_id": alternative["id"], "selected_value": money(value), "foregone_value": money(other), "avoidable_gap": money(regret), "dominated": regret > 0})
    return {"provenance": ("NO INPUT RECORDS" if not data["records"] else "SYNTHETIC fixtures" if data["synthetic"] else "REAL inputs entered by Henry"), "as_of": data["as_of"], "figure_status": "HYPOTHETICAL input valuations; computed comparisons, not measured savings or predictions", "currency": "GBP", "records": len(data["records"]), "decision_count": len(decisions), "dominated_count": sum(d["dominated"] for d in decisions), "selected_value_total": money(chosen_total), "foregone_value_total": money(alternative_total), "avoidable_gap_total": money(regret_total), "decisions": decisions}
