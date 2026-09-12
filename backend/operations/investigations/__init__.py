"""Investigações derivadas que organizam evidências sem usar IA."""

from .service import (
    InvestigationNotFound,
    build_delivery_delay_investigation,
    list_investigations,
)

__all__ = [
    "InvestigationNotFound",
    "build_delivery_delay_investigation",
    "list_investigations",
]
