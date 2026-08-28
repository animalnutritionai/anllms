"""
Knowledge Layer — core data model.

Every computable equation in ANLLMS is represented as a KNOWLEDGE OBJECT,
not a bare function. A knowledge object carries:

  - what it computes and why
  - exactly where it came from (publication, chapter, section, equation number)
  - the definition and units of every variable it touches
  - the assumptions baked into it
  - the conditions under which it applies (and where it does NOT apply)
  - what alternative equations exist and why this one was chosen instead
  - its known limitations / uncertainty

This module defines the shared schema. Individual equations (e.g. in
scientific/energy/) subclass KnowledgeEquation and fill this metadata in
from the published source — never from memory or convention.

No coefficient, threshold, or formula anywhere in this codebase should be
typed in without a Publication + Citation backing it. If a value is needed
and no citation is available, that is a gap to flag, not a gap to fill in.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Publication:
    """A single canonical source document."""

    short_name: str          # e.g. "NASEM Dairy 2021"
    full_title: str          # e.g. "Nutrient Requirements of Dairy Cattle: Eighth Revised Edition"
    authors: str
    year: int
    publisher: str
    edition: str
    url: str | None = None   # canonical/DOI link where available


@dataclass(frozen=True)
class Citation:
    """A pointer to a specific location within a Publication."""

    publication: Publication
    chapter: str | None = None
    section: str | None = None
    equation_number: str | None = None   # e.g. "Equation 3-13"
    table_number: str | None = None
    page_or_location: str | None = None  # page number, or stable anchor if paginated differently online

    def render(self) -> str:
        parts = [self.publication.short_name]
        if self.chapter:
            parts.append(f"Ch. {self.chapter}")
        if self.section:
            parts.append(self.section)
        if self.equation_number:
            parts.append(self.equation_number)
        if self.table_number:
            parts.append(self.table_number)
        return ", ".join(parts)


@dataclass(frozen=True)
class Variable:
    """Definition of one input or output variable used by an equation."""

    symbol: str          # short symbol as used in the publication, e.g. "BW"
    name: str            # human-readable name, e.g. "Body weight"
    unit: str            # e.g. "kg", "Mcal/d", "kg^0.75"
    description: str = ""
    valid_range: tuple[float, float] | None = None


@dataclass(frozen=True)
class SoftwareReference:
    """
    A reference software implementation of a published model — e.g. the
    University of Guelph `nasem_dairy` package, which mirrors the R code
    shipped with the official NASEM 8 software.

    ROLE (corrected Aug 2026 -- see known_discrepancies note below): a
    SoftwareReference serves THREE purposes, not two: (1) mapping/
    extracting exactly how a published equation is actually implemented,
    including any post-publication corrections the committee/maintainers
    have made; (2) cross-validating our own citation text against it in
    tests; AND (3) it IS called at runtime by every equation's
    `calculate()` method (`import nasem_dairy as nd; nd.calculate_X(...)`)
    -- this is the "wrap, don't reimplement" principle this entire
    project is built around, not an exception to it.

    Reproducibility is preserved by pinning `version_used_for_mapping`
    to a fixed, specific release (see pyproject.toml's `nasem_dairy`
    pin) rather than by avoiding runtime calls -- the printed book stays
    the citable formula source, while the pinned software version is the
    citable, fixed COMPUTATION source, not a live/continually-updated one.

    Any place our implementation and this reference disagree is a
    documented discrepancy (see `known_discrepancies` on the equation),
    not something to silently reconcile in either direction.

    (An earlier version of this docstring stated the reference was
    "NEVER called at runtime" -- that described an earlier/different
    design that was superseded once "wrap, don't reimplement" became the
    project's core principle, and was never updated to match. Flagged in
    docs/architecture.md until this fix; removed from open items once
    this correction lands.)
    """

    name: str
    repository_url: str
    version_used_for_mapping: str
    license: str
    role: str = (
        "Called at runtime for this calculation (wrap, don't reimplement); "
        "also the citation source for equation-mapping and cross-validation."
    )
    notes: str = ""


@dataclass(frozen=True)
class AlternativeEquation:
    """
    A competing/superseded equation the committee or field considered,
    recorded so the platform can explain why it was NOT used here.
    """

    citation: Citation
    coefficient_or_summary: str
    reason_not_selected: str


@dataclass
class EquationResult:
    """
    The output of a KnowledgeEquation calculation, bundled with the
    inputs used, so it is self-explaining without needing to re-run
    anything.
    """

    value: float
    unit: str
    inputs_used: dict[str, Any]
    equation: "KnowledgeEquation"

    def explain(self) -> str:
        return self.equation.explain(self.inputs_used, self.value, self.unit)


class KnowledgeEquation(ABC):
    """
    Base class for every scientific equation in the platform.

    Subclasses must define the metadata properties below and implement
    `calculate()`. They should NOT hide scientific logic behind generic
    helper math without documenting it here.
    """

    # --- required metadata (override in subclasses) ---
    name: str
    citation: Citation
    variables: list[Variable]
    assumptions: list[str]
    applicability: str
    limitations: list[str]
    alternatives_considered: list[AlternativeEquation] = []
    formula_text: str = ""   # human-readable formula, e.g. "NELmaint = 0.10 x BW^0.75"
    notes: str = ""

    # Reference software implementation used to map/verify this equation
    # (see SoftwareReference docstring — never called at runtime).
    software_reference: SoftwareReference | None = None

    # Open discrepancies or unresolved questions found either between
    # the book and its own cross-references, or between the book and
    # the reference software implementation. These must be documented,
    # not silently resolved in either direction, per project scientific
    # integrity rules.
    known_discrepancies: list[str] = []

    @abstractmethod
    def calculate(self, **inputs: float) -> EquationResult:
        """Run the calculation. Must return an EquationResult."""
        raise NotImplementedError

    def explain(self, inputs_used: dict[str, Any], value: float, unit: str) -> str:
        """
        Default human-readable explanation. Subclasses may extend this,
        but should not remove the citation/assumption/limitation sections.
        """
        lines = [
            f"Calculation: {self.name}",
            f"Formula: {self.formula_text}",
            f"Source: {self.citation.render()}",
            "",
            "Inputs used:",
        ]
        for k, v in inputs_used.items():
            lines.append(f"  - {k} = {v}")
        lines.append("")
        lines.append(f"Result: {value:.4g} {unit}")
        lines.append("")
        lines.append("Assumptions:")
        for a in self.assumptions:
            lines.append(f"  - {a}")
        lines.append("")
        lines.append(f"Applicability: {self.applicability}")
        if self.alternatives_considered:
            lines.append("")
            lines.append("Alternative equations considered and not used here:")
            for alt in self.alternatives_considered:
                lines.append(
                    f"  - {alt.citation.render()}: {alt.coefficient_or_summary} "
                    f"— not used because {alt.reason_not_selected}"
                )
        if self.limitations:
            lines.append("")
            lines.append("Limitations:")
            for lim in self.limitations:
                lines.append(f"  - {lim}")
        if self.software_reference:
            sw = self.software_reference
            lines.append("")
            lines.append(
                f"Implementation source: {sw.name} v{sw.version_used_for_mapping} "
                f"({sw.repository_url}) — {sw.role}"
            )
        if self.known_discrepancies:
            lines.append("")
            lines.append("Known open discrepancies (not silently resolved):")
            for d in self.known_discrepancies:
                lines.append(f"  - {d}")
        if self.notes:
            lines.append("")
            lines.append(f"Notes: {self.notes}")
        return "\n".join(lines)
