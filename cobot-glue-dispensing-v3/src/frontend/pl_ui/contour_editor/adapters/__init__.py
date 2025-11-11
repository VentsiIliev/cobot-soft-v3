"""
Adapters package for the contour editor.

This package contains adapters that bridge between domain-specific
data models (like Workpiece) and the domain-agnostic ContourEditorData.
"""

from .WorkpieceAdapter import WorkpieceAdapter

__all__ = ["WorkpieceAdapter"]