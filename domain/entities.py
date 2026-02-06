"""
Entities — Billetterie Cinéma
Objets avec identité persistante et cycle de vie.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from domain.value_objects import SeatNumber


class SeatStatus(str, Enum):
    """Statut d'une place dans le système de réservation."""
    AVAILABLE = "disponible"
    BLOCKED = "bloquée"
    RESERVED = "réservée"
    OCCUPIED = "occupée"


class Seat(BaseModel):
    """
    Entité Place — Représente un siège physique dans une salle.
    Identité : seat_id (unique et persistant).
    """
    seat_id: UUID = Field(default_factory=uuid4)
    seat_number: SeatNumber
    status: SeatStatus = SeatStatus.AVAILABLE
    blocked_until: Optional[datetime] = None
    reserved_by: Optional[str] = None  # client_id
    
    def block(self, until: datetime, client_id: str) -> None:
        """Bloque temporairement la place pour un client."""
        if self.status != SeatStatus.AVAILABLE:
            raise ValueError(f"Place {self.seat_number} non disponible (statut: {self.status})")
        
        self.status = SeatStatus.BLOCKED
        self.blocked_until = until
        self.reserved_by = client_id
    
    def confirm_reservation(self) -> None:
        """Confirme la réservation après paiement validé."""
        if self.status != SeatStatus.BLOCKED:
            raise ValueError(f"Place {self.seat_number} non bloquée (statut: {self.status})")
        
        self.status = SeatStatus.RESERVED
        self.blocked_until = None
    
    def release(self) -> None:
        """Libère la place (annulation ou timeout)."""
        self.status = SeatStatus.AVAILABLE
        self.blocked_until = None
        self.reserved_by = None
    
    def __str__(self) -> str:
        return f"Seat({self.seat_number}, {self.status.value})"


class Screening(BaseModel):
    """
    Entité Séance — Représente une projection de film.
    Identité : screening_id (unique et persistant).
    """
    screening_id: UUID = Field(default_factory=uuid4)
    film_id: str
    room_id: str
    start_time: datetime
    capacity: int = Field(ge=1)
    available_seats: int = Field(ge=0)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Initialisation : toutes les places disponibles
        if self.available_seats == 0:
            self.available_seats = self.capacity
    
    @property
    def is_full(self) -> bool:
        """Vérifie si la séance est complète."""
        return self.available_seats == 0
    
    def reserve_seats(self, count: int) -> None:
        """
        Réserve un nombre de places.
        Règle métier : impossible si capacité insuffisante.
        """
        if count <= 0:
            raise ValueError(f"Le nombre de places doit être positif, reçu : {count}")
        
        if count > self.available_seats:
            raise ValueError(
                f"Capacité insuffisante : {count} places demandées, "
                f"{self.available_seats} disponibles"
            )
        
        self.available_seats -= count
    
    def release_seats(self, count: int) -> None:
        """Libère des places suite à annulation."""
        if count <= 0:
            raise ValueError(f"Le nombre de places doit être positif, reçu : {count}")
        
        new_available = self.available_seats + count
        if new_available > self.capacity:
            raise ValueError(
                f"Incohérence : libération de {count} places dépasserait "
                f"la capacité ({self.capacity})"
            )
        
        self.available_seats = new_available
    
    def __str__(self) -> str:
        return (
            f"Screening(film={self.film_id}, room={self.room_id}, "
            f"time={self.start_time.isoformat()}, seats={self.available_seats}/{self.capacity})"
        )