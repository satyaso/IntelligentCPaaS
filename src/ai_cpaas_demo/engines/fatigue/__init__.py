"""Anti-fatigue protection engines for customer communication frequency management."""

from .base import BaseFatigueProtection
from .aws_native import AWSNativeFatigueProtection

__all__ = ["BaseFatigueProtection", "AWSNativeFatigueProtection"]
