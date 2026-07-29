# anllms

An explainable, citation-backed nutrient modeling layer for the NASEM
(2021) dairy cattle model.

## What this is

`anllms` wraps the University of Guelph's [`nasem_dairy`](https://github.com/CNM-University-of-Guelph/NASEM-Model-Python)
reference implementation of the NASEM (2021) *Nutrient Requirements of
Dairy Cattle* model. It does **not** reimplement any of the underlying
science -- every calculation calls the real `nasem_dairy` functions
directly. What this package adds is a layer of structured, machine- and
human-readable explanation around those calculations: every result
carries its book citation (chapter, equation number), stated assumptions,
known limitations, alternative equations considered and why they weren't
used, and any discrepancies found between the book and the reference
software.

The long-term goal is a natural-language assistant that can answer
dairy nutrition questions while showing exactly which equation, which
page, and which assumptions produced every number -- not a black box.

## Relationship to nasem_dairy

`nasem_dairy` is a normal pinned dependency (see `pyproject.toml`), not
vendored or modified code. This keeps the boundary clear: their code is
the trusted calculation engine; this repo is the explanation and
orchestration layer on top of it. Upgrading `nasem_dairy` is just a
version bump here, not a merge.

## Structure

- `anllms/knowledge/` -- the shared schema every equation wrapper is
  built from (`KnowledgeEquation`, `Publication`, `Citation`, etc.). No
  science here, just the template.
- `anllms/scientific/` -- one file per equation (or small family of
  equations), each wrapping a real `nasem_dairy` function and adding
  citation/assumption/limitation metadata. Organized by nutrient
  (`energy/`, `protein/`).
- `anllms/feed_library/` -- wraps `nasem_dairy`'s real 284-ingredient
  feed composition table (not reimplemented data).
- `anllms/simulation/` -- data containers (`AnimalState`, `MilkTarget`)
  and `RequirementsReport`, which composes multiple cited equations plus
  the reference model's own official totals into one explainable report.
- `docs/architecture.md` -- design notes and open scope decisions.
- `tests/` -- every test validates against real fixture data or the
  reference software's own output, not invented numbers.

## Installation

```bash
pip install -e .
```

## Running tests

```bash
pytest tests/
```

## Status

Early stage. Currently covers lactating dairy cows only: DMI prediction
(2 equations), energy requirements (maintenance + lactation), and
protein requirements/supply (maintenance, milk MP, microbial + RUP
supply). See `docs/architecture.md` for known gaps and next steps.
