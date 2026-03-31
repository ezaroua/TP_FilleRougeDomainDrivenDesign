# Invariants & Agrégats — Billetterie Cinéma

## Agrégat 1 : Réservation

### Racine d'agrégat
**Reservation** - Contrôle le cycle de vie de la réservation et garantit la cohérence des places réservées.

### Frontières
- **Inclus** : Liste des SeatId, montant total, statut, échéances
- **Exclus** : Détails complets des Seat (accès via repository si nécessaire), détails du Payment

### Invariants (≥3)

#### INV-R1 : Limite de places par réservation
**Règle** : Une réservation ne peut contenir plus de 10 places.

**Justification** : Éviter les abus et garantir l'équité d'accès (règle anti-monopole).

**Implémentation** :
```python
def add_seat(self, seat_id: UUID) -> None:
    if len(self.seats) >= 10:
        raise ValueError("Une réservation ne peut excéder 10 places")
    self.seats.append(seat_id)
```

**Test** : `test_reservation_max_10_seats_fails`

---

#### INV-R2 : Expiration automatique
**Règle** : Une réservation non confirmée expire après 15 minutes et doit être annulée.

**Justification** : Libérer les places bloquées pour d'autres clients si paiement non effectué.

**Implémentation** :
```python
def is_expired(self) -> bool:
    return datetime.now() > self.expires_at and self.status == ReservationStatus.PENDING

def confirm_payment(self) -> None:
    if self.is_expired():
        raise ValueError("Réservation expirée, confirmation impossible")
    self.status = ReservationStatus.CONFIRMED
```

**Test** : `test_reservation_expired_cannot_confirm`

---

#### INV-R3 : Immuabilité après confirmation
**Règle** : Une réservation confirmée (payée) ne peut plus être modifiée (ajout/suppression de places).

**Justification** : Garantir l'intégrité des billets émis et la traçabilité financière.

**Implémentation** :
```python
def add_seat(self, seat_id: UUID) -> None:
    if self.status == ReservationStatus.CONFIRMED:
        raise ValueError("Impossible de modifier une réservation confirmée")
    # ... reste de la logique
```

**Test** : `test_confirmed_reservation_cannot_add_seats`

---

## Agrégat 2 : Paiement

### Racine d'agrégat
**Payment** - Gère le cycle de vie du paiement et garantit la cohérence financière.

### Frontières
- **Inclus** : Montant, statut, transaction bancaire, lien vers réservation
- **Exclus** : Détails de la Reservation (sauf montant pour validation)

### Invariants (≥3)

#### INV-P1 : Montant exact
**Règle** : Le montant du paiement doit correspondre exactement au montant total de la réservation.

**Justification** : Éviter les paiements partiels ou sur-paiements qui créent des incohérences comptables.

**Implémentation** :
```python
def __init__(self, reservation_amount: Money, payment_amount: Money, ...):
    if payment_amount.euros != reservation_amount.euros:
        raise ValueError(
            f"Montant incorrect : attendu {reservation_amount}, reçu {payment_amount}"
        )
    self.amount = payment_amount
```

**Test** : `test_payment_amount_mismatch_fails`

---

#### INV-P2 : Unicité du paiement
**Règle** : Une réservation ne peut avoir qu'un seul paiement réussi.

**Justification** : Éviter les doubles-facturations et garantir l'unicité de la transaction.

**Implémentation** :
```python
# Vérifié au niveau du service applicatif
# Le repository doit rejeter la création d'un 2ème Payment pour le même reservation_id
```

**Test** : `test_duplicate_payment_rejected` (niveau service/repo)

---

#### INV-P3 : Statut final immuable
**Règle** : Un paiement avec statut SUCCESS ou FAILED ne peut plus changer de statut.

**Justification** : Garantir l'immuabilité des transactions finalisées pour l'audit et la comptabilité.

**Implémentation** :
```python
def process(self) -> None:
    if self.status in [PaymentStatus.SUCCESS, PaymentStatus.FAILED]:
        raise ValueError(f"Paiement déjà finalisé avec statut {self.status.value}")
    self.status = PaymentStatus.SUCCESS
    self.processed_at = datetime.now()

def fail(self, reason: str) -> None:
    if self.status in [PaymentStatus.SUCCESS, PaymentStatus.FAILED]:
        raise ValueError(f"Paiement déjà finalisé avec statut {self.status.value}")
    self.status = PaymentStatus.FAILED
    self.processed_at = datetime.now()
```

**Test** : `test_finalized_payment_cannot_change_status`

---

## Diagramme UML des Agrégats
```
╔═══════════════════════════════════════╗
║   Reservation (Aggregate Root)        ║
║───────────────────────────────────────║
║ Invariants:                           ║
║ - INV-R1: Max 10 places               ║
║ - INV-R2: Expiration 15min            ║
║ - INV-R3: Immuable après confirmation ║
╚═══════════════════════════════════════╝
              │
              │ 1:1 reference
              ▼
╔═══════════════════════════════════════╗
║      Payment (Aggregate Root)         ║
║───────────────────────────────────────║
║ Invariants:                           ║
║ - INV-P1: Montant exact               ║
║ - INV-P2: Unicité paiement            ║
║ - INV-P3: Statut final immuable       ║
╚═══════════════════════════════════════╝
```

### Interactions entre agrégats
```
┌──────────────┐                  ┌─────────────┐
│ Reservation  │                  │   Payment   │
│              │                  │             │
│ status:      │                  │ status:     │
│  PENDING     │───create────────►│  PENDING    │
│              │                  │             │
│              │◄──success────────│  SUCCESS    │
│ status:      │   event          │             │
│  CONFIRMED   │                  └─────────────┘
└──────────────┘
       │
       │ if expired
       ▼
   CANCELLED
```

## Matrice de validation

| Invariant | Validé à | Méthode | Test associé |
|-----------|----------|---------|--------------|
| INV-R1 | Ajout place | `add_seat()` | `test_reservation_max_10_seats_fails` |
| INV-R2 | Confirmation | `confirm_payment()` | `test_reservation_expired_cannot_confirm` |
| INV-R3 | Modification | `add_seat()` | `test_confirmed_reservation_cannot_add_seats` |
| INV-P1 | Création | `__init__()` | `test_payment_amount_mismatch_fails` |
| INV-P2 | Création | Repository check | `test_duplicate_payment_rejected` |
| INV-P3 | Changement statut | `process()`, `fail()` | `test_finalized_payment_cannot_change_status` |