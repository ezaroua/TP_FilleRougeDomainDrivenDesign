# Exemples d'API REST — Billetterie Cinéma

> Chapitre 4 — Livrable 3 : Maquette conceptuelle des endpoints REST.
> **Aucune API réelle** — exemples de messages et flux métier uniquement.

---

## Contexte métier : Bounded Context Réservations

Tous les endpoints ci-dessous appartiennent au **Bounded Context Réservations**. Ils exposent les cas d'usage de ce contexte via un adapter REST (FastAPI conceptuel). Les termes utilisés dans les requêtes/réponses JSON respectent l'Ubiquitous Language défini.

---

## Endpoint 1 — Créer une réservation (POST)

### Description du flux métier
Un client sélectionne une séance et des places, et initie une réservation. Le système bloque temporairement les places (15 minutes) en attendant la confirmation du paiement. Ce flux implique une vérification de disponibilité auprès du contexte Catalogue (via ACL) puis l'application des invariants de l'agrégat Réservation.

### Requête

```
POST /api/v1/reservations
Content-Type: application/json
X-Correlation-ID: corr-uuid-a1b2c3
X-Client-ID: CLI-123
```

```json
{
  "seance_id": "SCR-456",
  "places": [
    { "rang": "F", "numero": 11 },
    { "rang": "F", "numero": 12 }
  ],
  "tarif": "plein"
}
```

### Réponse (succès — HTTP 201 Created)

```json
{
  "reservation_id": "RES-789",
  "client_id": "CLI-123",
  "seance_id": "SCR-456",
  "statut": "EN_ATTENTE",
  "places": [
    { "place_id": "SEAT-F11", "rang": "F", "numero": 11 },
    { "place_id": "SEAT-F12", "rang": "F", "numero": 12 }
  ],
  "montant_total": 23.00,
  "cree_le": "2026-03-15T19:46:23Z",
  "expire_le": "2026-03-15T20:01:23Z",
  "correlation_id": "corr-uuid-a1b2c3"
}
```

### Réponse (erreur — HTTP 409 Conflict)

```json
{
  "erreur": "PLACES_INDISPONIBLES",
  "message": "La place F12 n'est plus disponible pour cette séance",
  "places_concernees": ["F12"],
  "correlation_id": "corr-uuid-a1b2c3"
}
```

### Correspondance avec l'UL
- `seance_id` → **Séance** (UL : instance de projection identifiée)
- `places` → **Place** (UL : siège numéroté avec rang et numéro)
- `statut: EN_ATTENTE` → **Blocage** (UL : verrouillage temporaire 15min)
- `expire_le` → **Timeout** (UL : délai avant libération automatique)
- `montant_total` → **Montant** (UL : valeur monétaire calculée selon le tarif)

---

## Endpoint 2 — Consulter une réservation (GET)

### Description du flux métier
Un client (ou caissier) consulte l'état actuel d'une réservation. Ce flux est en lecture seule : aucune modification de l'agrégat. Il permet de vérifier le statut, les places réservées et les billets associés si la réservation est confirmée.

### Requête

```
GET /api/v1/reservations/RES-789
X-Correlation-ID: corr-uuid-d4e5f6
X-Client-ID: CLI-123
```

### Réponse (succès — HTTP 200 OK) — Réservation confirmée

```json
{
  "reservation_id": "RES-789",
  "client_id": "CLI-123",
  "seance": {
    "seance_id": "SCR-456",
    "film_titre": "Avatar 3",
    "date_heure": "2026-03-15T20:15:00Z",
    "salle": "Salle 2 — IMAX"
  },
  "statut": "CONFIRMÉE",
  "places": [
    { "place_id": "SEAT-F11", "rang": "F", "numero": 11 },
    { "place_id": "SEAT-F12", "rang": "F", "numero": 12 }
  ],
  "montant_total": 23.00,
  "billets": [
    { "billet_id": "BIL-001", "place_id": "SEAT-F11", "qr_code": "QR:RES789-F11" },
    { "billet_id": "BIL-002", "place_id": "SEAT-F12", "qr_code": "QR:RES789-F12" }
  ],
  "cree_le": "2026-03-15T19:46:23Z",
  "confirme_le": "2026-03-15T19:52:10Z",
  "correlation_id": "corr-uuid-d4e5f6"
}
```

### Réponse (erreur — HTTP 404 Not Found)

```json
{
  "erreur": "RESERVATION_INTROUVABLE",
  "message": "Aucune réservation trouvée avec l'identifiant RES-999",
  "correlation_id": "corr-uuid-d4e5f6"
}
```

### Correspondance avec l'UL
- `statut: CONFIRMÉE` → **Réservation** confirmée (UL : engagement client finalisé)
- `billets` → **Billet** (UL : titre d'entrée validant l'accès à la séance)
- `qr_code` → **QR Code** (UL : code-barres 2D pour validation à l'entrée)
- Les informations de séance proviennent du **Catalogue** via l'ACL (données enrichies pour l'affichage)

---

## Endpoint 3 — Annuler une réservation (DELETE)

### Description du flux métier
Un client annule sa réservation. Si la réservation est EN_ATTENTE, les places sont immédiatement libérées sans frais. Si la réservation est CONFIRMÉE et que la séance est dans plus de 2 heures, un remboursement est initié via le contexte Paiements.

### Requête

```
DELETE /api/v1/reservations/RES-789
X-Correlation-ID: corr-uuid-g7h8i9
X-Client-ID: CLI-123
```

### Réponse (succès — HTTP 200 OK)

```json
{
  "reservation_id": "RES-789",
  "statut": "ANNULÉE",
  "remboursement": {
    "montant": 23.00,
    "statut": "EN_COURS",
    "delai_estimé": "3-5 jours ouvrés"
  },
  "message": "Votre réservation a été annulée. Le remboursement de 23,00€ sera traité sous 3-5 jours ouvrés.",
  "correlation_id": "corr-uuid-g7h8i9"
}
```

---

## Flux métier complet — Correspondance entre couches

```
Client Web
    │ POST /api/v1/reservations
    ▼
FastAPI REST Adapter
    │ → CréerRéservationCommand(seance_id, places, client_id)
    ▼
Service Applicatif CréerRéservation
    │ → ICataloguePort.getSeanceInfo(seance_id)
    │ → IReservationRepository.getPlacesOccupées(seance_id)
    │ → new Réservation(client_id, seance_id, places, montant)
    │ → IReservationRepository.save(reservation)
    ▼
Agrégat Réservation (Domaine)
    │ Applique invariants (max 10 places, calcul montant)
    │ Émet PlacesRéservées event
    ▼
PostgreSQL Adapter
    │ INSERT INTO reservations ...
    ▼
FastAPI REST Adapter
    │ → HTTP 201 { reservation_id, statut, expire_le, ... }
    ▼
Client Web
```
