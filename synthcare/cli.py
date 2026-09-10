"""synthcare CLI.

Examples:
    python -m synthcare --count 25 --seed 42 --format ndjson --out ./synthetic
    python -m synthcare --count 5 --format bundle --stdout
    synthcare --count 100 --format csv --out ./demo
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .generator import generate_resources, to_bundle, to_ndjson


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="synthcare",
        description="Generate deterministic synthetic FHIR R4 patient populations (education & testing, not real data).",
    )
    parser.add_argument("--count", type=int, default=10, help="number of patients (default 10)")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility (default 42)")
    parser.add_argument("--format", choices=["ndjson", "bundle", "csv"], default="ndjson", dest="format")
    parser.add_argument("--out", type=Path, default=None, help="output directory (created if missing)")
    parser.add_argument("--stdout", action="store_true", help="print to stdout instead of writing files")
    args = parser.parse_args(argv)

    if args.count < 1:
        parser.error("--count must be >= 1")

    resources = generate_resources(args.count, seed=args.seed)
    patients = sum(1 for r in resources if r["resourceType"] == "Patient")

    if args.stdout:
        if args.format == "bundle":
            print(json.dumps(to_bundle(resources), ensure_ascii=False, indent=2))
        else:
            print(to_ndjson(resources))
        return 0

    out: Path = args.out or Path(f"synthcare-out-{args.seed}")
    out.mkdir(parents=True, exist_ok=True)

    if args.format == "bundle":
        target = out / "population-bundle.json"
        target.write_text(json.dumps(to_bundle(resources), ensure_ascii=False, indent=2), encoding="utf-8")
    elif args.format == "ndjson":
        target = out / "population.ndjson"
        target.write_text(to_ndjson(resources) + "\n", encoding="utf-8")
    else:
        _write_csv(out, resources)
        target = out / "patients.csv"

    by_type: dict[str, int] = {}
    for r in resources:
        by_type[r["resourceType"]] = by_type.get(r["resourceType"], 0) + 1
    summary = "  ".join(f"{k}: {v}" for k, v in sorted(by_type.items()))
    print(f"synthcare ✔ {patients} patients (seed {args.seed}) → {target}")
    print(f"  resources — {summary}")
    return 0


def _write_csv(out: Path, resources: list[dict]) -> None:
    import csv

    by_type: dict[str, list[dict]] = {}
    for r in resources:
        by_type.setdefault(r["resourceType"], []).append(r)

    with (out / "patients.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "family", "given", "gender", "birthDate", "city"])
        for p in by_type.get("Patient", []):
            w.writerow(
                [
                    p["id"],
                    p["name"][0].get("family", ""),
                    p["name"][0].get("given", [""])[0],
                    p["gender"],
                    p["birthDate"],
                    p.get("address", [{}])[0].get("city", ""),
                ]
            )

    with (out / "conditions.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "patient", "icd10", "snomed", "display", "onset"])
        for c in by_type.get("Condition", []):
            cod = c["code"]["coding"]
            w.writerow(
                [
                    c["id"],
                    c["subject"]["reference"].split("/")[-1],
                    cod[0]["code"],
                    cod[1]["code"],
                    c["code"]["text"],
                    c["onsetDateTime"],
                ]
            )

    with (out / "observations.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "patient", "loinc", "display", "category", "value", "unit", "effective"])
        for o in by_type.get("Observation", []):
            vq = o.get("valueQuantity", {})
            w.writerow(
                [
                    o["id"],
                    o["subject"]["reference"].split("/")[-1],
                    o["code"]["coding"][0]["code"],
                    o["code"]["coding"][0]["display"],
                    o["category"][0]["coding"][0]["code"],
                    vq.get("value"),
                    vq.get("unit"),
                    o["effectiveDateTime"],
                ]
            )


if __name__ == "__main__":
    sys.exit(main())
