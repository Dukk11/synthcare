# Contributing to synthcare

## Ground rules

1. **Zero dependencies.** Standard library only — the value proposition is
   "pip install nothing, run anywhere".
2. **Determinism is sacred.** Any change must keep `same seed → byte-identical
   output` true (there is a test for exactly that). Never use `random.random()`
   module-level state; always draw from the passed `rng`.
3. **Codes must be real.** New ICD-10 / SNOMED CT / LOINC codes need a source
   you can link (WHO ICD browser, LOINC search, Snowmed browser). No invented
   codes — this dataset models correct terminology so it can validate real
   pipelines.
4. **Plausibility needs a test.** A new condition-effect pairing (e.g. "COPD
   lowers SpO₂") gets a statistical assertion like `test_diabetics_run_higher_…`.
5. **Keep it synthetic.** Name/address pools are fictional; don't wire in
   identity-like data.

## Workflow

```bash
python -m unittest discover -s tests -v
python -m synthcare --count 50 --seed 1 --format csv --out /tmp/check   # eyeball the output
```

## License

By contributing you agree your contributions are licensed under the MIT License.
