# Design des Intégrations entre Contextes

> Chapitre 5 — Livrable 2 : Modélisation des intégrations REST et événementielles.
> Tout est conceptuel — aucun broker ni service réel.

---

## Intégration 1 — REST synchrone : Réservations → Catalogue

### Contexte métier
Lorsqu'un client initie une réservation, le contexte Réservations doit récupérer les informations de la séance (tarif, capacité, horaire) depuis le contexte Catalogue. Il s'agit d'une lecture synchrone : le résultat est immédiatement nécessaire pour valider la demande de réservation.

### Pattern choisi : Customer/Supplier + ACL

Le contexte Réservations (Customer/downstream) dépend du Catalogue (Supplier/upstream) pour les informations de séance. Une couche ACL dans Réservations traduit le modèle "riche" du Catalogue en un modèle "minimal" adapté au contexte Réservations.

### Schéma de séquence

```
Service Applicatif     CatalogueACL        CatalogueHTTP          Catalogue API
CréerRéservation       (Adapter)           Adapter                 (External)
       │                    │                    │                      │
       │ getSeanceInfo()    │                    │                      │
       │───────────────────►│                    │                      │
       │                    │ GET /seances/{id}  │                      │
       │                    │───────────────────►│                      │
       │                    │                    │ GET /seances/{id}    │
       │                    │                    │─────────────────────►│
       │                    │                    │◄─── SeanceRiche {}   │
       │                    │◄── SeanceRiche {}  │                      │
       │                    │ translate()        │                      │
       │◄── SeanceContexte  │                    │                      │
       │   (modèle interne) │                    │                      │
```

### Explication métier
L'ACL transforme le `SeanceRiche` du Catalogue (qui contient : film_id, métadonnées, affiche, synopsis, équipe technique, configuration de salle détaillée) en un `SeanceContexte` minimaliste (seance_id, heure_debut, tarif, capacite). Cela protège le modèle métier de Réservations des évolutions internes du Catalogue.

---

## Intégration 2 — Événementielle : Réservations ↔ Paiements

### Contexte métier
La relation entre Réservations et Paiements est un **Partnership** bidirectionnel. Réservations déclenche un paiement via un événement, et Paiements notifie le résultat via un autre événement. Les deux contextes sont couplés par le cycle de vie de la réservation.

### Diagramme publish → subscribe

```
╔═══════════════════════════════════════════════════════════╗
║              Bus d'événements (RabbitMQ / Kafka)           ║
╚═══════════════════════════════════════════════════════════╝
        ▲              │              ▲               │
        │ publish      │ subscribe    │ publish       │ subscribe
        │              ▼              │               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Réservations  │ │   Paiements   │ │   Paiements   │ │ Réservations  │
│  (Producteur) │ │ (Consommateur)│ │  (Producteur) │ │ (Consommateur)│
│               │ │               │ │               │ │               │
│ PaiementRequis│ │ PaiementRequis│ │ PaiementValidé│ │ PaiementValidé│
│  {résa_id,    │ │ → initier     │ │  {résa_id,    │ │ → confirmer   │
│   montant,    │ │   transaction │ │   txn_id,     │ │   réservation │
│   client_id}  │ │   Stripe      │ │   montant}    │ │               │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
```

### Flux narratif détaillé

1. **Réservations** crée une réservation EN_ATTENTE et publie l'événement `PaiementRequis` sur le bus avec `{reservation_id, montant_total, client_id, expire_le}`

2. **Paiements** consomme `PaiementRequis`, crée un agrégat Payment en PENDING, et appelle Stripe pour initier un PaymentIntent

3. Stripe traite la transaction et envoie un webhook `payment_intent.succeeded` à l'adapter Stripe de Paiements

4. **Paiements** met à jour son Payment à SUCCESS et publie `PaiementValidé` sur le bus avec `{reservation_id, payment_id, transaction_id, montant}`

5. **Réservations** consomme `PaiementValidé`, charge la réservation #RES-789, appelle `confirm_payment()` sur l'agrégat (vérifie qu'elle n'est pas expirée), génère les billets, émet `RéservationConfirmée`

6. Un service de Notification consomme `RéservationConfirmée` et envoie l'email client

### Justification du choix événementiel
L'intégration par événements offre un **découplage fort** entre les deux contextes : Réservations ne connaît pas l'implémentation de Paiements et vice-versa. En cas de défaillance de Paiements, la réservation reste EN_ATTENTE jusqu'à son expiration sans bloquer le système. La résilience est garantie par le mécanisme de rejeu du broker.

---

## Intégration 3 — Événementielle : Catalogue → Réservations

### Contexte métier
Lorsque le Gestionnaire planifie une nouvelle séance dans le Catalogue, le contexte Réservations doit être notifié pour initialiser la liste des places disponibles (N places libres correspondant à la capacité de la salle).

### Diagramme publish → subscribe

```
╔═════════════════════════════════════════════════╗
║           Bus d'événements                       ║
╚═════════════════════════════════════════════════╝
        ▲                              │
        │ publish                      │ subscribe
        │                              ▼
┌───────────────┐               ┌───────────────────────┐
│   Catalogue   │               │     Réservations      │
│  (Upstream)   │               │     (Downstream)      │
│               │               │                       │
│ SéancePlanifié│               │ SéancePlanifiée       │
│  {seance_id,  │               │ → créer N places      │
│   salle_id,   │               │   libres dans le      │
│   capacite,   │               │   repository          │
│   heure_debut}│               │                       │
└───────────────┘               └───────────────────────┘
```

### Justification du choix événementiel
Catalogue est le contexte autoritaire (upstream) sur les séances. Il n'a pas à connaître Réservations ni à lui notifier directement. La publication d'un événement permet à Réservations d'initialiser ses propres données (disponibilités) de manière autonome. Si d'autres contextes consommaient aussi `SéancePlanifiée` (ex. un système de recommandation), ils pourraient le faire sans modification du Catalogue.

---

## Tableau récapitulatif des intégrations

| # | Source | Cible | Type | Pattern | Événement / Endpoint |
|---|--------|-------|------|---------|---------------------|
| 1 | Réservations | Catalogue | REST synchrone | Customer/Supplier + ACL | GET /seances/{id} |
| 2 | Réservations | Paiements | Événement async | Partnership | PaiementRequis |
| 3 | Paiements | Réservations | Événement async | Partnership | PaiementValidé / PaiementÉchoué |
| 4 | Catalogue | Réservations | Événement async | Customer/Supplier | SéancePlanifiée |
| 5 | Paiements | Stripe | REST synchrone | Conformist | POST /v1/payment_intents |
