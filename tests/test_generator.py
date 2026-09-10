"""Tests for the synthcare generator — determinism, FHIR validity, integrity, plausibility."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from synthcare import generate_resources, to_bundle, to_ndjson
from synthcare.cli import main

ALLOWED_TYPES = {"Patient", "Condition", "Encounter", "Observation"}

# (loinc, plausible low, plausible high)
SANITY = {
    "8867-4": (30, 200),      # heart rate
    "9279-1": (4, 60),        # respiratory rate
    "59408-5": (60, 100),     # SpO2
    "8480-6": (50, 260),      # systolic BP
    "718-7": (5, 21),         # hemoglobin
    "2345-7": (30, 1200),     # glucose
    "2160-0": (0.2, 8),       # creatinine
    "4548-4": (3.5, 16),      # HbA1c
}


class TestDeterminism(unittest.TestCase):
    def test_same_seed_produces_identical_output(self):
        a = to_ndjson(generate_resources(12, seed=42))
        b = to_ndjson(generate_resources(12, seed=42))
        self.assertEqual(a, b)

    def test_different_seed_produces_different_output(self):
        a = to_ndjson(generate_resources(12, seed=1))
        b = to_ndjson(generate_resources(12, seed=2))
        self.assertNotEqual(a, b)

    def test_fixed_today_keeps_dates_stable(self):
        a = generate_resources(5, seed=7, today=date(2026, 9, 10))
        b = generate_resources(5, seed=7, today=date(2026, 9, 10))
        self.assertEqual(a, b)


class TestFhirValidity(unittest.TestCase):
    def setUp(self):
        self.resources = generate_resources(15, seed=99)

    def test_only_valid_resource_types(self):
        for r in self.resources:
            self.assertIn(r["resourceType"], ALLOWED_TYPES)

    def test_patient_fields_are_fhir_shaped(self):
        patients = [r for r in self.resources if r["resourceType"] == "Patient"]
        self.assertEqual(len(patients), 15)
        for p in patients:
            self.assertIn(p["gender"], ("female", "male"))
            self.assertRegex(p["birthDate"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertTrue(p["name"][0]["family"])

    def test_observation_shape_and_ucum_units(self):
        obs = [r for r in self.resources if r["resourceType"] == "Observation"]
        self.assertGreater(len(obs), 50)
        for o in obs[:40]:
            self.assertEqual(o["status"], "final")
            self.assertEqual(o["code"]["coding"][0]["system"], "http://loinc.org")
            vq = o["valueQuantity"]
            self.assertEqual(vq["system"], "http://unitsofmeasure.org")
            self.assertTrue(vq["unit"])

    def test_bundle_is_valid_collection(self):
        bundle = to_bundle(self.resources)
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "collection")
        self.assertEqual(len(bundle["entry"]), len(self.resources))
        for e in bundle["entry"]:
            self.assertTrue(e["fullUrl"].startswith("urn:uuid:"))


class TestIntegrity(unittest.TestCase):
    def setUp(self):
        self.resources = generate_resources(20, seed=7)

    def test_every_subject_reference_resolves(self):
        patient_ids = {r["id"] for r in self.resources if r["resourceType"] == "Patient"}
        for r in self.resources:
            if r["resourceType"] in ("Condition", "Encounter", "Observation"):
                ref = r["subject"]["reference"]
                self.assertTrue(ref.startswith("Patient/"))
                self.assertIn(ref.split("/")[-1], patient_ids, f"dangling reference {ref}")

    def test_patient_count_is_exact(self):
        patients = [r for r in self.resources if r["resourceType"] == "Patient"]
        self.assertEqual(len(patients), 20)

    def test_conditions_reference_known_codes(self):
        for c in (r for r in self.resources if r["resourceType"] == "Condition"):
            systems = {coding["system"] for coding in c["code"]["coding"]}
            self.assertIn("http://hl7.org/fhir/sid/icd-10", systems)
            self.assertIn("http://snomed.info/sct", systems)


class TestPlausibility(unittest.TestCase):
    def setUp(self):
        self.resources = generate_resources(40, seed=3)

    def test_values_within_physiologic_bounds(self):
        for o in (r for r in self.resources if r["resourceType"] == "Observation"):
            loinc = o["code"]["coding"][0]["code"]
            if loinc in SANITY:
                lo, hi = SANITY[loinc]
                v = o["valueQuantity"]["value"]
                self.assertGreaterEqual(v, lo, f"{loinc} value {v}")
                self.assertLessEqual(v, hi, f"{loinc} value {v}")

    def test_diabetics_run_higher_glucose_than_non_diabetics(self):
        diabetics = {
            r["subject"]["reference"]
            for r in self.resources
            if r["resourceType"] == "Condition" and r["code"]["coding"][0]["code"] == "E11"
        }
        gluco = [o for o in self.resources if o["resourceType"] == "Observation" and o["code"]["coding"][0]["code"] == "2345-7"]
        dia = [o["valueQuantity"]["value"] for o in gluco if o["subject"]["reference"] in diabetics]
        healthy = [o["valueQuantity"]["value"] for o in gluco if o["subject"]["reference"] not in diabetics]
        if dia and healthy:  # with 40 patients there is almost always at least one diabetic
            self.assertGreater(sum(dia) / len(dia), sum(healthy) / len(healthy))


class TestCli(unittest.TestCase):
    def test_ndjson_output_to_temp_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = main(["--count", "3", "--seed", "5", "--format", "ndjson", "--out", tmp])
            self.assertEqual(rc, 0)
            target = Path(tmp) / "population.ndjson"
            self.assertTrue(target.exists())
            lines = target.read_text(encoding="utf-8").strip().splitlines()
            self.assertTrue(lines)
            for line in lines:
                self.assertIn("resourceType", json.loads(line))

    def test_csv_output_writes_three_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = main(["--count", "4", "--seed", "5", "--format", "csv", "--out", tmp])
            self.assertEqual(rc, 0)
            for name in ("patients.csv", "conditions.csv", "observations.csv"):
                self.assertTrue((Path(tmp) / name).exists(), name)

    def test_rejects_count_below_one(self):
        with self.assertRaises(SystemExit):
            main(["--count", "0"])


if __name__ == "__main__":
    unittest.main()
