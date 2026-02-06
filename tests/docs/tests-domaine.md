# Documentation Tests — Domaine Billetterie

## Stratégie de test

### Tests unitaires (≥4 requis)
- **Framework** : pytest
- **Couverture** : Value Objects + Entities (couche domaine pure)
- **Approche** : Given/When/Then pour lisibilité métier

## Tests implémentés

### 1. `test_money_creation_valid` ✅ (Happy Path)
**Objectif** : Valider la création d'un montant positif valide

**Given** : Montant de 23,50€  
**When** : Instanciation de Money  
**Then** : Valeur correcte + formatage "23.50€"

**Règle métier testée** : Les montants sont stockés avec précision décimale

---

### 2. `test_screening_reservation_success` ✅ (Happy Path)
**Objectif** : Réserver des places avec capacité suffisante

**Given** : Séance de 150 places  
**When** : Réservation de 3 places  
**Then** : 147 places restantes, séance non complète

**Règle métier testée** : La réservation décrémente correctement la disponibilité

---

### 3. `test_money_creation_negative_fails` ❌ (Error Case)
**Objectif** : Empêcher la création de montants négatifs

**Given** : Montant de -10,00€  
**When** : Tentative d'instanciation  
**Then** : ValueError levée avec message explicite

**Règle métier testée** : Invariant "montant strictement positif"

---

### 4. `test_screening_overbooking_fails` ❌ (Error Case)
**Objectif** : Empêcher le surbooking

**Given** : Séance de 50 places, 45 déjà réservées  
**When** : Tentative de réserver 10 places supplémentaires  
**Then** : ValueError levée (capacité insuffisante)

**Règle métier testée** : Invariant "nombre de réservations ≤ capacité"

---

## Tests bonus (8 tests total implémentés)

5. **Cycle de vie d'une place** : blocage → confirmation
6. **Validation SeatNumber** : format rang invalide
7. **Addition de montants** : opérateur `+` sur Money
8. **Libération de places** : annulation avec cohérence

## Exécution
```bash
# Installation dépendances
pip install pytest pydantic

# Lancer les tests
pytest tests/unit/test_domaine.py -v

# Avec couverture
pytest tests/unit/test_domaine.py --cov=domain --cov-report=term
```

## Résultats attendus
```
tests/unit/test_domaine.py::test_money_creation_valid PASSED           [ 12%]
tests/unit/test_domaine.py::test_screening_reservation_success PASSED  [ 25%]
tests/unit/test_domaine.py::test_money_creation_negative_fails PASSED  [ 37%]
tests/unit/test_domaine.py::test_screening_overbooking_fails PASSED    [ 50%]
tests/unit/test_domaine.py::test_seat_blocking_and_confirmation PASSED [ 62%]
tests/unit/test_domaine.py::test_seat_number_invalid_row_fails PASSED  [ 75%]
tests/unit/test_domaine.py::test_money_addition PASSED                 [ 87%]
tests/unit/test_domaine.py::test_screening_release_seats PASSED        [100%]

========== 8 passed in 0.12s ==========
```