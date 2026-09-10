"""
Deterministic synthetic FHIR R4 population generator.

Everything derives from a single integer seed: same seed + same code version
→ byte-identical output. No real patient data ever touches this library.
"""

from __future__ import annotations

import json
import random
import uuid
from datetime import date, timedelta

from . import data as D

FHIR_PATIENT = "http://hl7.org/fhir/StructureDefinition/Patient"
LOINC = "http://loinc.org"
ICD10 = "http://hl7.org/fhir/sid/icd-10"
SNOMED = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
OBS_CATEGORY = "http://terminology.hl7.org/CodeSystem/observation-category"
ACT_CODE = "http://terminology.hl7.org/CodeSystem/v3-ActCode"

__all__ = ["generate_resources", "to_bundle", "to_ndjson"]


def _uuid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def _shift(rng: random.Random, mean: float, spread: float, lo: float, hi: float) -> float:
    """Clamped gaussian sample."""
    v = rng.gauss(mean, spread)
    return round(min(hi, max(lo, v)), 1 if spread < 3 else 0)


def generate_resources(count: int, seed: int, today: date | None = None) -> list[dict]:
    """Generate a FHIR collection of resources for `count` synthetic patients."""
    if count < 1:
        raise ValueError("count must be >= 1")
    today = today or date.today()
    rng = random.Random(seed)
    resources: list[dict] = []

    for _ in range(count):
        patient_id = _uuid(rng)
        sex = rng.choice(["female", "male"])
        age = int(min(90, max(18, rng.gauss(58, 18))))
        birth = today - timedelta(days=int(age * 365.25 + rng.randint(0, 364)))
        given = rng.choice(D.FIRST_NAMES_F if sex == "female" else D.FIRST_NAMES_M)
        family = rng.choice(D.LAST_NAMES)
        city, zip_code = rng.choice(D.CITIES)

        resources.append(
            {
                "resourceType": "Patient",
                "id": patient_id,
                "name": [{"family": family, "given": [given]}],
                "gender": sex,
                "birthDate": birth.isoformat(),
                "address": [{"city": city, "postalCode": zip_code, "line": [f"{rng.randint(1, 120)} {rng.choice(D.STREETS)}"]}],
            }
        )

        # Conditions — weighted draws, 0–4 per patient.
        chosen: list[D.Condition] = []
        for cond in rng.sample(D.CONDITION_CATALOG, k=len(D.CONDITION_CATALOG)):
            if len(chosen) >= rng.randint(0, 4):
                break
            if rng.random() < cond.prevalence * 1.6:
                chosen.append(cond)
        for cond in chosen:
            onset = today - timedelta(days=rng.randint(180, int(max(365, age - 18) * 365)))
            resources.append(
                {
                    "resourceType": "Condition",
                    "id": _uuid(rng),
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                    },
                    "code": {
                        "coding": [
                            {"system": ICD10, "code": cond.icd10},
                            {"system": SNOMED, "code": cond.snomed, "display": cond.display},
                        ],
                        "text": cond.display,
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "onsetDateTime": onset.isoformat(),
                }
            )

        # Encounters — 1–8 outpatient/short inpatient stays over 3 years.
        effects: dict[str, tuple[float, float]] = {}
        for cond in chosen:
            for key, effs in D.CONDITION_EFFECTS.items():
                if cond.icd10.startswith(key):
                    for loinc, eff in effs.items():
                        effects[loinc] = eff

        n_enc = rng.randint(1, 8)
        for _ in range(n_enc):
            enc_start = today - timedelta(days=rng.randint(1, 365 * 3))
            inpatient = rng.random() < 0.15
            enc_days = rng.randint(2, 9) if inpatient else 0
            enc_end = enc_start + timedelta(days=enc_days)
            encounter_id = _uuid(rng)
            resources.append(
                {
                    "resourceType": "Encounter",
                    "id": encounter_id,
                    "status": "finished",
                    "class": {"system": ACT_CODE, "code": "IMP" if inpatient else "AMB", "display": "inpatient encounter" if inpatient else "ambulatory"},
                    "type": [{"text": rng.choice(["General practice visit", "Specialist outpatient visit", "Ward stay"])}],
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "period": {"start": enc_start.isoformat(), "end": enc_end.isoformat()},
                }
            )

            # Vital signs at each encounter.
            for defn in D.VITALS:
                mult, extra = effects.get(defn.loinc, (1.0, 0.0))
                mean = (defn.low + defn.high) / 2
                spread = (defn.high - defn.low) / 6
                value = _shift(rng, mean * mult, spread + extra, defn.low, defn.high)
                resources.append(_observation(defn, value, patient_id, enc_start, rng))

            # Labs on ~40% of encounters.
            if rng.random() < 0.4:
                for defn in D.LABS:
                    mult, extra = effects.get(defn.loinc, (1.0, 0.0))
                    mean = (defn.low + defn.high) / 2
                    spread = (defn.high - defn.low) / 6
                    value = _shift(rng, mean * mult, spread + extra, defn.low, defn.high)
                    resources.append(_observation(defn, value, patient_id, enc_start, rng))

    return resources


def _observation(defn: D.ObservationDef, value: float, patient_id: str, when: date, rng: random.Random) -> dict:
    decimals = 1 if defn.ucum in ("Cel", "kg/m2") or defn.low < 20 else 0
    return {
        "resourceType": "Observation",
        "id": _uuid(rng),
        "status": "final",
        "category": [{"coding": [{"system": OBS_CATEGORY, "code": defn.category}]}],
        "code": {"coding": [{"system": LOINC, "code": defn.loinc, "display": defn.display}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": f"{when.isoformat()}T{rng.randint(8, 17):02d}:{rng.choice(['00', '15', '30', '45'])}:00Z",
        "valueQuantity": {"value": round(value, decimals), "unit": defn.unit, "system": UCUM, "code": defn.ucum},
    }


def to_bundle(resources: list[dict]) -> dict:
    """Wrap resources in a FHIR Bundle(type=collection)."""
    return {
        "resourceType": "Bundle",
        "id": "synthcare-population",
        "type": "collection",
        "entry": [{"fullUrl": f"urn:uuid:{r['id']}", "resource": r} for r in resources],
    }


def to_ndjson(resources: list[dict]) -> str:
    """FHIR bulk-data style NDJSON: one resource per line."""
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in resources)
