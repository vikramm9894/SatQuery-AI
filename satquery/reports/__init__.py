"""
SatQuery AI — Multi-Format Report Generator.
Exports intelligence verdicts to JSON, GeoJSON (RFC 7946), Markdown, and ReportLab PDF.
"""

from .generator import ReportGenerator, report_generator

__all__ = ["ReportGenerator", "report_generator"]
