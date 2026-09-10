"""
Clinical content catalog for synthetic populations.

Coding honesty: every ICD-10 and SNOMED CT code below is a well-established
code for the named concept. LOINC codes follow the standard vital-signs and
common-lab panels. Plausibility of ranges targets adult education demos —
synthcare is a test-data tool, not a clinical reference.
"""

from dataclasses import dataclass

FIRST_NAMES_F = [
    "Anna", "Maria", "Sofia", "Elena", "Julia", "Laura", "Emma", "Hannah",
    "Clara", "Ingrid", "Petra", "Sabine", "Nadia", "Yara", "Lena", "Monika",
]
FIRST_NAMES_M = [
    "Lukas", "Jonas", "Felix", "David", "Thomas", "Michael", "Stefan",
    "Daniel", "Marco", "Ivan", "Peter", "Klaus", "Omar", "Victor", "Paul",
]
LAST_NAMES = [
    "Müller", "Schmidt", "Weber", "Fischer", "Wagner", "Becker", "Hoffmann",
    "Schäfer", "Koch", "Richter", "Klein", "Wolf", "Neumann", "Schwarz",
    "Zimmermann", "Braun", "Krüger", "Hartmann", "Lange", "Weiss",
]

STREETS = [
    "Birkenweg", "Hauptstraße", "Lindenstraße", "Am Sportplatz",
    "Rosenweg", "Kirchplatz", "Seestraße", "Ahornallee",
]
CITIES = [
    ("Berlin", "10115"), ("München", "80331"), ("Hamburg", "20095"),
    ("Wien", "1010"), ("Zürich", "8001"), ("Leipzig", "04103"),
]


@dataclass(frozen=True)
class Condition:
    icd10: str
    snomed: str
    display: str
    prevalence: float  # rough adult prevalence in a general ward-ish population


CONDITION_CATALOG = [
    Condition("I10", "38341003", "Essential (primary) hypertension", 0.30),
    Condition("E11", "44054006", "Type 2 diabetes mellitus", 0.12),
    Condition("E78.5", "55822004", "Hyperlipidemia, unspecified", 0.18),
    Condition("J45", "195967001", "Asthma", 0.08),
    Condition("J44", "13645005", "Chronic obstructive pulmonary disease", 0.06),
    Condition("I48", "49436004", "Atrial fibrillation", 0.05),
    Condition("F32.9", "370143000", "Depressive episode, unspecified", 0.08),
    Condition("E66.9", "162864005", "Obesity, unspecified", 0.16),
    Condition("E03.9", "40930008", "Hypothyroidism, unspecified", 0.05),
    Condition("N18.9", "90688005", "Chronic renal insufficiency", 0.04),
    Condition("I25.9", "53741008", "Chronic ischemic heart disease", 0.06),
    Condition("K21.9", "235595009", "Gastro-esophageal reflux disease", 0.10),
    Condition("M19.90", "396275006", "Osteoarthritis, unspecified", 0.14),
    Condition("G47.33", "73430006", "Obstructive sleep apnea", 0.06),
    Condition("D64.9", "271737000", "Anemia, unspecified", 0.07),
]


@dataclass(frozen=True)
class ObservationDef:
    loinc: str
    display: str
    unit: str
    ucum: str
    low: float
    high: float
    category: str  # 'vital-signs' | 'laboratory'


VITALS = [
    ObservationDef("8867-4", "Heart rate", "beats/minute", "{beats}/min", 45, 130, "vital-signs"),
    ObservationDef("9279-1", "Respiratory rate", "breaths/minute", "{breaths}/min", 10, 26, "vital-signs"),
    ObservationDef("59408-5", "Oxygen saturation", "%", "%", 88, 100, "vital-signs"),
    ObservationDef("8480-6", "Systolic blood pressure", "mmHg", "mm[Hg]", 95, 185, "vital-signs"),
    ObservationDef("8462-4", "Diastolic blood pressure", "mmHg", "mm[Hg]", 55, 110, "vital-signs"),
    ObservationDef("8310-5", "Body temperature", "Cel", "Cel", 35.8, 39.2, "vital-signs"),
    ObservationDef("29463-7", "Body weight", "kg", "kg", 48, 140, "vital-signs"),
    ObservationDef("39156-5", "Body mass index", "kg/m2", "kg/m2", 17, 45, "vital-signs"),
]

LABS = [
    ObservationDef("2345-7", "Glucose [Mass/volume] in Serum or Plasma", "mg/dL", "mg/dL", 65, 320, "laboratory"),
    ObservationDef("718-7", "Hemoglobin [Mass/volume] in Blood", "g/dL", "g/dL", 7.5, 18.5, "laboratory"),
    ObservationDef("4544-3", "Hematocrit [Volume Fraction] of Blood", "%", "%", 24, 52, "laboratory"),
    ObservationDef("6690-2", "Leukocytes [#/volume] in Blood", "10*3/uL", "10*3/uL", 3.0, 16.0, "laboratory"),
    ObservationDef("777-3", "Platelets [#/volume] in Blood", "10*3/uL", "10*3/uL", 120, 420, "laboratory"),
    ObservationDef("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", "mg/dL", "mg/dL", 0.5, 3.5, "laboratory"),
    ObservationDef("2951-2", "Sodium [Moles/volume] in Serum or Plasma", "mmol/L", "mmol/L", 130, 148, "laboratory"),
    ObservationDef("2823-3", "Potassium [Moles/volume] in Serum or Plasma", "mmol/L", "mmol/L", 3.2, 5.6, "laboratory"),
    ObservationDef("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "mg/dL", "mg/dL", 120, 320, "laboratory"),
    ObservationDef("4548-4", "Hemoglobin A1c", "%", "%", 4.8, 11.0, "laboratory"),
    ObservationDef("1742-6", "Alanine aminotransferase [Enzymatic activity/volume]", "U/L", "U/L", 8, 90, "laboratory"),
    ObservationDef("3016-3", "Thyrotropin [Units/volume] in Serum or Plasma", "mIU/L", "m[iU]/L", 0.3, 7.0, "laboratory"),
]

# Condition → observation modifiers: (multiplicative mean shift, extra spread)
CONDITION_EFFECTS = {
    "E11": {"2345-7": (1.45, 25), "4548-4": (1.5, 0.6)},
    "I10": {"8480-6": (1.18, 10), "8462-4": (1.14, 6)},
    "N18.9": {"2160-0": (2.0, 0.5)},
    "D64.9": {"718-7": (0.75, 0.8), "4544-3": (0.78, 3)},
    "E66.9": {"39156-5": (1.35, 2), "29463-7": (1.25, 8)},
    "J44": {"59408-5": (0.955, 1.5), "9279-1": (1.2, 2)},
    "E78.5": {"2093-3": (1.3, 25)},
    "I48": {"8867-4": (1.25, 8)},
}

FEMALE_ONLY = set()
MALE_ONLY = set()
