"""synthcare — deterministic synthetic FHIR R4 patient data. Zero dependencies."""

from .generator import generate_resources, to_bundle, to_ndjson

__version__ = "1.0.0"
__all__ = ["generate_resources", "to_bundle", "to_ndjson", "__version__"]
