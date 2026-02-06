"""
Tests unitaires — Domain Layer
4 tests minimum : 2 cas heureux + 2 cas d'erreur.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from domain.value_objects import Money, SeatNumber
from domain.entities import Seat, Screening, SeatStatus


# ============= CAS HEUREUX (Happy Path) =============

def test_money_creation_valid():
    """Test 1 (Happy) : Création d'un montant valide."""
    # Given
    montant = Decimal("23.50")
    
    # When
    money = Money(euros=montant)
    
    # Then
    assert money.euros == Decimal("23.50")
    assert str(money) == "23.50€"


def test_screening_reservation_success():
    """Test 2 (Happy) : Réservation de places avec capacité suffisante."""
    # Given
    screening = Screening(
        film_id="FILM-001",
        room_id="SALLE-1",
        start_time=datetime(2026, 2, 10, 20, 15),
        capacity=150
    )
    assert screening.available_seats == 150
    
    # When
    screening.reserve_seats(3)
    
    # Then
    assert screening.available_seats == 147
    assert not screening.is_full


# ============= CAS D'ERREUR (Error Cases) =============

def test_money_creation_negative_fails():
    """Test 3 (Error) : Création d'un montant négatif doit échouer."""
    # Given
    montant_negatif = Decimal("-10.00")
    
    # When / Then
    with pytest.raises(ValueError, match="strictement positif"):
        Money(euros=montant_negatif)


def test_screening_overbooking_fails():
    """Test 4 (Error) : Réservation au-delà de la capacité doit échouer."""
    # Given
    screening = Screening(
        film_id="FILM-002",
        room_id="SALLE-2",
        start_time=datetime(2026, 2, 11, 18, 30),
        capacity=50
    )
    screening.reserve_seats(45)  # 45/50 places réservées
    
    # When / Then
    with pytest.raises(ValueError, match="Capacité insuffisante"):
        screening.reserve_seats(10)  # Demande 10 places alors que seulement 5 disponibles


# ============= TESTS BONUS (Validation robuste) =============

def test_seat_blocking_and_confirmation():
    """Test 5 (Bonus) : Cycle de vie complet d'une place."""
    # Given
    seat = Seat(seat_number=SeatNumber(row="F", number=12))
    client_id = "CLI-123"
    block_until = datetime.now() + timedelta(minutes=15)
    
    # When - Blocage
    seat.block(until=block_until, client_id=client_id)
    
    # Then
    assert seat.status == SeatStatus.BLOCKED
    assert seat.reserved_by == client_id
    
    # When - Confirmation
    seat.confirm_reservation()
    
    # Then
    assert seat.status == SeatStatus.RESERVED
    assert seat.blocked_until is None


def test_seat_number_invalid_row_fails():
    """Test 6 (Bonus Error) : Numéro de place avec rang invalide."""
    # When / Then
    with pytest.raises(ValueError, match="lettre majuscule"):
        SeatNumber(row="1", number=12)  # Rang numérique invalide
    
    with pytest.raises(ValueError, match="lettre majuscule"):
        SeatNumber(row="f", number=12)  # Rang minuscule invalide


def test_money_addition():
    """Test 7 (Bonus) : Addition de deux montants."""
    # Given
    price1 = Money(euros=Decimal("11.50"))
    price2 = Money(euros=Decimal("8.00"))
    
    # When
    total = price1 + price2
    
    # Then
    assert total.euros == Decimal("19.50")
    assert str(total) == "19.50€"


def test_screening_release_seats():
    """Test 8 (Bonus) : Libération de places après annulation."""
    # Given
    screening = Screening(
        film_id="FILM-003",
        room_id="SALLE-1",
        start_time=datetime(2026, 2, 12, 21, 0),
        capacity=100
    )
    screening.reserve_seats(20)  # 80 places disponibles
    
    # When
    screening.release_seats(5)
    
    # Then
    assert screening.available_seats == 85