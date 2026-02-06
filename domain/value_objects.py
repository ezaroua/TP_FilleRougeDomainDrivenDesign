"""
Value Objects — Billetterie Cinéma
Objets immuables représentant des concepts métier sans identité propre.
"""

from decimal import Decimal
from typing import Self
from pydantic import BaseModel, field_validator, Field


class Money(BaseModel):
    """
    Représente un montant monétaire en euros.
    Règles métier : montant strictement positif, précision 2 décimales.
    """
    euros: Decimal = Field(ge=0, decimal_places=2)
    
    class Config:
        frozen = True  # Immuabilité
    
    @field_validator('euros')
    @classmethod
    def validate_positive(cls, value: Decimal) -> Decimal:
        """Valide que le montant est strictement positif."""
        if value <= 0:
            raise ValueError(f"Le montant doit être strictement positif, reçu : {value}€")
        return value
    
    def __add__(self, other: "Money") -> "Money":
        """Addition de deux montants."""
        if not isinstance(other, Money):
            raise TypeError("Seuls des objets Money peuvent être additionnés")
        return Money(euros=self.euros + other.euros)
    
    def __str__(self) -> str:
        return f"{self.euros:.2f}€"


class SeatNumber(BaseModel):
    """
    Représente l'identifiant d'une place (Rang + Numéro).
    Format : Lettre (A-Z) + Numéro (1-99).
    """
    row: str = Field(min_length=1, max_length=1)
    number: int = Field(ge=1, le=99)
    
    class Config:
        frozen = True
    
    @field_validator('row')
    @classmethod
    def validate_row_letter(cls, value: str) -> str:
        """Valide que le rang est une lettre majuscule."""
        if not value.isupper() or not value.isalpha():
            raise ValueError(f"Le rang doit être une lettre majuscule (A-Z), reçu : {value}")
        return value
    
    def __str__(self) -> str:
        return f"{self.row}{self.number}"
    
    def __hash__(self) -> int:
        return hash((self.row, self.number))