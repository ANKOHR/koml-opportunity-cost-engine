"""Local-only CLI; no network, predictions, or measured-savings claims."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import InputError, evaluate
from .fixtures import generate
from .report import render


def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(text)
        os.replace(temporary, path)
    except OSError as exc:
        raise InputError(f"WriteError: {path}: {exc}") from None
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field {key}")
        result[key] = value
    return result


def load(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use koce fixtures --out demo or supply an input directory")
    path = directory / "tasks.json"
    if not path.exists():
        other = sorted(p for p in directory.iterdir() if p.is_file())
        if other:
            raise InputError(f"SchemaError: {other[0]}: line 1: missing tasks.json; only the documented JSON schema is supported")
        return {"synthetic": False, "entered_by": "Henry", "as_of": "2026-09-30", "currency": "GBP", "records": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from None
    except ValueError as exc:
        raise InputError(f"ParseError: {path}: line 1: {exc}") from None
    except (UnicodeError, OSError) as exc:
        raise InputError(f"ParseError: {path}: line 1: {exc}") from None
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(prog="koce", description="Compute hypothetical opportunity cost from explicit GBP valuations.")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("fixtures", help="Generate labelled synthetic inputs", description="Generate labelled synthetic inputs. Example: koce fixtures --out demo")
    p.add_argument("--out", required=True)
    p = commands.add_parser("run", help="Compute and persist comparisons", description="Compute and persist comparisons. Example: koce run --input demo")
    p.add_argument("--input", required=True)
    p.add_argument("--state", default=".koce-results.json")
    p = commands.add_parser("report", help="Render provenance and hypothetical results", description="Render provenance and hypothetical results. Example: koce report --format md")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--state", default=".koce-results.json")
    p.add_argument("--out")
    for name, description in (("compare", "Compare selected tasks with the best alternatives"), ("audit", "Find choices with a positive hypothetical avoidable gap")):
        p = commands.add_parser(name, help=description, description=f"{description}. Example: koce {name} --input demo")
        p.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("SYNTHETIC fixtures generated; all valuations are HYPOTHETICAL.")
        elif args.command == "report":
            path = Path(args.state)
            if not path.exists():
                raise InputError(f"MissingInput: {path}; run koce run --input <dir> first")
            try:
                result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
                output = render(result, args.format)
            except json.JSONDecodeError as exc:
                raise InputError(f"ParseError: {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from None
            except (ValueError, KeyError, TypeError) as exc:
                raise InputError(f"SchemaError: {path}: invalid result state: {exc}") from None
            if args.out:
                atomic_write(args.out, output)
            else:
                sys.stdout.write(output)
        else:
            try:
                result = evaluate(load(args.input))
            except InputError as exc:
                raise InputError(f"{exc} [input: {Path(args.input) / 'tasks.json'}]") from None
            if args.command == "run":
                atomic_write(args.state, render(result, "json"))
                print(f"{result['provenance']}: computed {result['decision_count']} decisions. HYPOTHETICAL valuations, not measured savings.")
            else:
                if args.command == "audit":
                    result["audit_matches"] = [r["decision"] for r in result["decisions"] if r["dominated"]]
                sys.stdout.write(render(result, "json"))
        return 0
    except (InputError, OSError) as exc:
        message = str(exc) if isinstance(exc, InputError) else f"FileError: {exc}"
        print(message.replace(chr(8212), "[U+2014]"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
