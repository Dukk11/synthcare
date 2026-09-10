# 🧬 synthcare

[![CI](https://github.com/Dukk11/synthcare/actions/workflows/ci.yml/badge.svg)](https://github.com/Dukk11/synthcare/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![zero dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)](pyproject.toml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

**Deterministic synthetic FHIR R4 patient populations from one integer.**
Patients, conditions (ICD-10 + SNOMED CT), encounters, vital signs and labs
(LOINC + UCUM) — clinically plausible, privacy-safe, byte-for-byte reproducible.
Zero dependencies, pure standard library.

> ⚠️ Synthetic data only. Not real patients, not clinical reference data —
> built for demos, tests, and teaching.

## Why

Every healthcare dev/demo needs patient data. Real EHR exports are a privacy
landmine; random JSON is unusable because it breaks referential integrity and
codes. synthcare emits **valid FHIR R4 resources** with consistent references,
real terminology codes, and condition-driven plausibility (diabetics run high
glucose and HbA1c, CKD patients high creatinine, anemics low hemoglobin, …).

## Quick start

```bash
pip install synthcare            # or: python -m synthcare from a clone

# 25 reproducible patients as FHIR bulk-style NDJSON
synthcare --count 25 --seed 42 --format ndjson --out ./synthetic

# One FHIR Bundle (type=collection) straight to stdout
python -m synthcare --count 5 --format bundle --stdout
```

```
synthcare ✔ 25 patients (seed 42) → synthetic/population.ndjson
  resources — Condition: 33  Encounter: 92  Observation: 1089  Patient: 25
```

Same seed → same bytes. Feed `seed` from your CI matrix and your demo dataset is
versioned forever.

## Output formats

| Format | What you get | Typical use |
|---|---|---|
| `ndjson` | one FHIR resource per line (bulk-data spec style) | FHIR servers, ETL pipelines |
| `bundle` | single `Bundle(type=collection)` JSON | Postman, HAPI, tutorials |
| `csv` | `patients.csv` + `conditions.csv` + `observations.csv` | spreadsheets, BI tools |

## Library API

```python
from synthcare import generate_resources, to_bundle, to_ndjson

resources = generate_resources(50, seed=7)
bundle = to_bundle(resources)          # dict — POST it to a FHIR server
ndjson = to_ndjson(resources)          # str — bulk format
```

## What's inside

- **15 conditions** with paired ICD-10 + SNOMED CT codes and realistic prevalence weights
- **8 vital signs + 12 labs** with LOINC codes and UCUM units
- **Condition effects:** E11 → glucose/HbA1c ↑, I10 → BP ↑, N18.9 → creatinine ↑, D64.9 → Hb ↓, J44 → SpO₂ ↓/RR ↑, …
- **Referential integrity:** every Condition/Encounter/Observation points at an existing Patient — pinned by tests
- **Deterministic:** seeded PRNG, UUIDv4 derived from the stream, pinned by byte-equality tests

## Testing

```bash
python -m unittest discover -s tests -v    # 16 tests, stdlib unittest
```

CI matrix: Python 3.10 → 3.14 on Ubuntu/macOS/Windows.

## Roadmap

- [ ] Pediatric patients + weight-based dosing scenarios
- [ ] MedicationRequest resources
- [ ] Sepsis / deterioration cohorts for alert-pipeline testing
- [ ] Optional `faker` backend for locale-rich names

---

Built by Duk · [dukdev.com](https://dukdev.com) · MIT licensed
