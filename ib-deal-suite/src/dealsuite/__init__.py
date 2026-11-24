"""dealsuite: LBO, merger accretion/dilution, precedent transactions, Excel export and dashboards."""

from .excel import write_workbook
from .lbo import LBOInputs, LBOResult, SourcesUses, returns_sensitivity, run, sources_and_uses
from .merger import MergerInputs, MergerResult, accretion_by_synergies, analyse
from .precedents import ImpliedValue, MultipleStats, implied_value, summarise
from .report import build_dashboard

__version__ = "0.1.0"

__all__ = [
    "LBOInputs",
    "LBOResult",
    "SourcesUses",
    "run",
    "sources_and_uses",
    "returns_sensitivity",
    "MergerInputs",
    "MergerResult",
    "analyse",
    "accretion_by_synergies",
    "MultipleStats",
    "ImpliedValue",
    "summarise",
    "implied_value",
    "write_workbook",
    "build_dashboard",
]
