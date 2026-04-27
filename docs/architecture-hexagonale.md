# Architecture Hexagonale — Billetterie Cinéma

> Chapitre 4 — Livrable 1 : Modélisation documentaire de l'architecture hexagonale.
> **Aucun code** — description conceptuelle uniquement.

---

## 1. Description des trois couches

### Couche Domaine (Core Domain)
La couche Domaine est le cœur du système. Elle contient l'ensemble des règles métier pures, exprimées avec l'Ubiquitous Language de la billetterie cinéma. Elle est **totalement indépendante** de toute technologie (pas de base de données, pas de framework HTTP, pas d'API externe).

Elle contient :
- Les **entités** : Réservation, Séance, Paiement, Seat
- Les **objets valeur** : Money, SeatNumber, ClientId, TransactionId
- Les **agrégats** : Réservation (root), Paiement (root)
- Les **invariants** : règles qui doivent toujours rester vraies (max 10 places, expiration 15min, etc.)
- Les **domain events** : PlacesRéservées, RéservationConfirmée, PaiementValidé, SéancePlanifiée
- Les **domain services** : PlanifierRéservation, CalculerMontantTotal

Elle évolue uniquement au rythme du métier, pas des changements techniques.

---

### Couche Application
La couche Application orchestre les cas d'usage sans contenir de logique métier propre. Elle coordonne les agrégats du domaine, appelle les ports (interfaces abstraites) pour interagir avec l'extérieur, et gère les règles transverses (sécurité, logging métier, émission d'événements).

Cas d'usage principaux :
- `CréerRéservation` : Vérifier disponibilité → Bloquer places → Créer réservation → Initier paiement
- `ConfirmerPaiement` : Valider transaction → Confirmer réservation → Émettre billets → Notifier client
- `AnnulerRéservation` : Vérifier conditions → Libérer places → Initier remboursement si nécessaire
- `ExpurerRéservations` : (tâche planifiée) Libérer les réservations expirées

Ports définis par cette couche :
- `IReservationRepository` : port de persistance des réservations
- `IPaymentRepository` : port de persistance des paiements
- `ICataloguePort` : port de lecture des séances depuis le Catalogue
- `IPaymentGatewayPort` : port vers le prestataire de paiement (Stripe)
- `INotificationPort` : port d'envoi de notifications clients

---

### Couche Infrastructure / Adapters
La couche Infrastructure fournit les implémentations concrètes des ports définis par la couche Application. Elle traduit les concepts métier en appels techniques (SQL, HTTP, JSON).

Adapters prévus :
- `PostgreSQLReservationAdapter` → implémente `IReservationRepository`
- `PostgreSQLPaymentAdapter` → implémente `IPaymentRepository`
- `CatalogueHTTPAdapter` → implémente `ICataloguePort` (appel REST vers le service Catalogue)
- `StripePaymentAdapter` → implémente `IPaymentGatewayPort` (Conformist vers Stripe)
- `SendGridNotificationAdapter` → implémente `INotificationPort`
- `FastAPIRestAdapter` → traduit les requêtes HTTP en commandes métier

---

## 2. Schéma de l'architecture hexagonale

```
╔══════════════════════════════════════════════════════════════════════╗
║              INTERFACES EXTERNES                                      ║
║  [Client Web]  [App Mobile]  [Caissier Terminal]  [Tâche planifiée]  ║
╚═════════════════════════════╤════════════════════════════════════════╝
                              │ HTTP / REST
                    ┌─────────▼──────────┐
                    │  FastAPI Adapter    │ ← REST Adapter
                    │  (Incoming)        │
                    └─────────┬──────────┘
                              │ Commande métier
╔═════════════════════════════▼════════════════════════════════════════╗
║                      COUCHE APPLICATION                               ║
║                                                                       ║
║   CréerRéservation  │  ConfirmerPaiement  │  AnnulerRéservation      ║
║                                                                       ║
║   Ports (interfaces abstraites) :                                     ║
║   [IReservationRepository]  [ICataloguePort]  [IPaymentGatewayPort]  ║
║   [IPaymentRepository]      [INotificationPort]                      ║
╚══════════╤══════════════════════════════════════════╤════════════════╝
           │ appel agrégats                           │ appel ports
╔══════════▼══════════════════════╗         ╔════════▼════════════════╗
║         COUCHE DOMAINE          ║         ║   COUCHE INFRASTRUCTURE ║
║                                 ║         ║                         ║
║  Agrégats :                     ║         ║  PostgreSQL Adapter     ║
║  - Réservation (root)           ║         ║  CatalogueHTTP Adapter  ║
║  - Paiement (root)              ║         ║  Stripe Adapter         ║
║                                 ║         ║  SendGrid Adapter       ║
║  Entités :                      ║         ║                         ║
║  - Seat, Screening              ║         ╚═════════════╤═══════════╝
║                                 ║                       │
║  Value Objects :                ║         ╔═════════════▼═══════════╗
║  - Money, SeatNumber            ║         ║   SYSTÈMES EXTERNES     ║
║  - ClientId, TransactionId      ║         ║  [PostgreSQL]  [Stripe] ║
║                                 ║         ║  [Catalogue BC] [Email] ║
║  Domain Events :                ║         ╚═════════════════════════╝
║  - PlacesRéservées              ║
║  - RéservationConfirmée         ║
║  - PaiementValidé               ║
╚═════════════════════════════════╝
```

---

## 3. Narration d'un flux métier complet : "Un client réserve 2 places"

**Acteur** : Client (via application web)

**Étape 1 — Interface externe**
Le client sélectionne la séance "Avatar 3" du 15/03/2026 à 20h15 et choisit les places F11 et F12. Il clique sur "Réserver".

**Étape 2 — FastAPI REST Adapter (Infrastructure entrante)**
L'adapter reçoit la requête `POST /api/reservations`. Il extrait les paramètres (client_id, seance_id, places) et les transforme en une commande métier `CréerRéservationCommand`. Un Correlation ID (UUID) est généré à ce stade et propagé dans tout le flux.

**Étape 3 — Service Applicatif CréerRéservation**
Le service applicatif orchestre le cas d'usage :
1. Il appelle `ICataloguePort.getSeanceInfo(seance_id)` pour récupérer les informations de la séance
2. Il appelle `IReservationRepository.getAvailableSeats(seance_id)` pour vérifier la disponibilité des places F11 et F12
3. Il crée une nouvelle instance de l'agrégat `Réservation` avec les données validées

**Étape 4 — Agrégat Réservation (Domaine)**
L'agrégat `Réservation` applique ses invariants :
- Vérifie que le nombre de places (2) est dans la limite de 10
- Calcule le montant_total : 2 × 11,50€ = 23,00€
- Génère un `expires_at` = maintenant + 15 minutes
- Émet un domain event `PlacesRéservées`

**Étape 5 — Persistance (Infrastructure)**
Le service applicatif appelle `IReservationRepository.save(reservation)`. Le `PostgreSQLReservationAdapter` traduit l'agrégat en une requête SQL INSERT et persiste la réservation en base.

**Étape 6 — Réponse**
Le service applicatif retourne le résultat au FastAPI Adapter, qui le transforme en réponse JSON :
```json
{
  "reservation_id": "RES-789",
  "statut": "EN_ATTENTE",
  "expire_le": "2026-03-15T20:01:23Z",
  "montant_total": 23.00
}
```

---

## 4. Séparation métier / technique — Justification

| Bénéfice | Explication dans notre contexte |
|----------|--------------------------------|
| **Testabilité** | Les règles métier (invariants) peuvent être vérifiées sans base de données |
| **Évolutivité** | On peut remplacer PostgreSQL par MongoDB sans toucher au domaine |
| **Lisibilité** | Le domaine exprime uniquement les règles de la billetterie, sans bruit technique |
| **Flexibilité** | Le même domaine peut être exposé via REST, CLI ou une interface caissier physique |
