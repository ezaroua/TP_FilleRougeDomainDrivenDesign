# Observabilité — Billetterie Cinéma

> Chapitre 5 — Livrable 3 : Stratégie d'observabilité dans un système multi-contextes.
> Correlation ID, métriques métier, logging structuré, tracing distribué.

---

## 1. Correlation ID

### Définition
Le Correlation ID est un identifiant unique (UUID v4) attaché à chaque requête ou événement entrant dans le système. Il permet de reconstituer le flux complet d'une opération à travers les différents Bounded Contexts, même lorsque ceux-ci communiquent de manière asynchrone.

### Où est-il généré ?
Le Correlation ID est généré **à l'entrée du système**, dans le REST Adapter (FastAPI) lors de la réception d'une requête HTTP. Si le client fournit déjà un `X-Correlation-ID` dans ses headers (ex. application mobile), ce dernier est conservé. Sinon, le système en génère un nouveau.

### Comment circule-t-il entre contextes ?

```
Client Web
    │ X-Correlation-ID: corr-a1b2c3d4 (ou vide → généré par le REST Adapter)
    ▼
REST Adapter (Réservations)
    │ Génère / conserve corr-a1b2c3d4
    │ Injecte dans tous les logs
    │ Passe dans les commandes applicatives
    ▼
Service Applicatif
    │ Propagé dans chaque appel de port
    ▼
Événement PaiementRequis
    │ payload contient correlation_id: "corr-a1b2c3d4"
    ▼
Service Applicatif Paiements
    │ Récupère le correlation_id de l'événement
    │ L'injecte dans ses propres logs
    ▼
Événement PaiementValidé
    │ payload contient correlation_id: "corr-a1b2c3d4"
    ▼
Service Applicatif Réservations (confirmation)
    │ Même correlation_id dans les logs
```

Ainsi, en cherchant `corr-a1b2c3d4` dans tous les logs du système, on peut reconstituer l'intégralité du parcours d'une réservation depuis la requête HTTP initiale jusqu'à la confirmation finale.

### Exemple de log structuré contenant le Correlation ID

```json
{
  "timestamp": "2026-03-15T19:46:23.847Z",
  "level": "INFO",
  "service": "reservations-service",
  "context": "ReservationsBC",
  "correlation_id": "corr-a1b2c3d4",
  "client_id": "CLI-123",
  "reservation_id": "RES-789",
  "event": "ReservationCreated",
  "message": "Réservation RES-789 créée pour la séance SCR-456 — 2 places, montant 23,00€",
  "metadata": {
    "seance_id": "SCR-456",
    "nb_places": 2,
    "montant_total": 23.00,
    "expire_le": "2026-03-15T20:01:23Z"
  }
}
```

```json
{
  "timestamp": "2026-03-15T19:47:12.204Z",
  "level": "INFO",
  "service": "paiements-service",
  "context": "PaiementsBC",
  "correlation_id": "corr-a1b2c3d4",
  "reservation_id": "RES-789",
  "payment_id": "PAY-001",
  "event": "PaymentInitiated",
  "message": "Paiement PAY-001 initié via Stripe pour la réservation RES-789 — 23,00€",
  "metadata": {
    "stripe_intent_id": "pi_3OxK2L2eZvKYlo2C1hBw5h3M",
    "montant": 23.00
  }
}
```

---

## 2. Métriques métier

### Métrique 1 : Taux de conversion réservation → paiement

| Champ | Valeur |
|-------|--------|
| **Nom** | `reservations_conversion_rate` |
| **Description** | Pourcentage de réservations EN_ATTENTE qui aboutissent à un paiement confirmé (vs expirées ou annulées) |
| **Utilité** | Identifier les problèmes dans le tunnel de conversion (ex. délai de 15min trop court, problèmes de paiement fréquents) |
| **Type** | gauge (valeur instantanée en pourcentage) |
| **Calcul** | (réservations CONFIRMÉES / réservations créées) × 100, fenêtre glissante 1h |

---

### Métrique 2 : Nombre de réservations créées par heure

| Champ | Valeur |
|-------|--------|
| **Nom** | `reservations_created_per_hour` |
| **Description** | Nombre de nouvelles réservations initiées par tranche horaire |
| **Utilité** | Détecter les pics d'activité (sorties de blockbusters), dimensionner l'infrastructure, monitorer les anomalies (chute soudaine = incident technique) |
| **Type** | counter (valeur cumulée, réinitialisée toutes les heures) |
| **Labels** | `seance_id`, `film_titre` |

---

### Métrique 3 : Taux d'échec de paiement

| Champ | Valeur |
|-------|--------|
| **Nom** | `payments_failure_rate` |
| **Description** | Pourcentage de tentatives de paiement ayant abouti à un statut FAILED |
| **Utilité** | Détecter les problèmes avec le prestataire Stripe, identifier les tarifs incorrects ou les doublons, surveiller les fraudes potentielles |
| **Type** | gauge (pourcentage sur fenêtre glissante 15min) |
| **Seuil d'alerte** | > 5% déclenche une alerte PagerDuty |

---

### Métrique 4 : Latence de confirmation de réservation

| Champ | Valeur |
|-------|--------|
| **Nom** | `reservation_confirmation_latency_seconds` |
| **Description** | Temps écoulé entre la création de la réservation et sa confirmation (POST /reservations → statut CONFIRMÉE) |
| **Utilité** | Mesurer la fluidité du parcours client, détecter des lenteurs dans la communication avec Stripe ou le bus d'événements |
| **Type** | histogram (buckets : 5s, 15s, 30s, 60s, 120s, +inf) |
| **P95 cible** | < 30 secondes |

---

### Métrique 5 : Places expirées libérées par heure

| Champ | Valeur |
|-------|--------|
| **Nom** | `expired_reservations_released_per_hour` |
| **Description** | Nombre de réservations expirées automatiquement (places libérées faute de paiement dans les 15min) |
| **Utilité** | Évaluer le taux d'abandon, optimiser potentiellement le délai d'expiration (trop court = trop d'abandons, trop long = places bloquées inutilement) |
| **Type** | counter |

---

## 3. Logging structuré — Niveaux et formats

### Convention de nommage des événements métier dans les logs

| Niveau | Usage dans notre domaine |
|--------|--------------------------|
| `INFO` | Transitions de statut métier normales (réservation créée, paiement validé, billet généré) |
| `WARN` | Situations anormales mais non bloquantes (réservation expirée, tentative de modification de réservation confirmée) |
| `ERROR` | Échecs techniques ou violations d'invariants inattendues (Stripe indisponible, doublon de paiement détecté) |

### Champs obligatoires dans chaque log

```json
{
  "timestamp": "[ISO 8601]",
  "level": "[INFO|WARN|ERROR]",
  "service": "[reservations-service|paiements-service|catalogue-service]",
  "context": "[ReservationsBC|PaiementsBC|CatalogueBC]",
  "correlation_id": "[UUID]",
  "event": "[NomÉvénementMétier]",
  "message": "[Description lisible en français]",
  "metadata": { "[données contextuelles métier]" }
}
```

---

## 4. Tracing distribué — Flux conceptuel

### Description conceptuelle
Dans notre système, une requête de réservation traverse potentiellement 3 Bounded Contexts (Réservations, Catalogue, Paiements) et plusieurs composants techniques (REST Adapter, services applicatifs, broker, base de données). Le tracing distribué permet de visualiser ce chemin sous forme de **spans** imbriquées.

### Flux de tracing pour une réservation complète

```
[Span racine] POST /api/v1/reservations — durée totale : ~28s
  │
  ├── [Span] REST Adapter : validation de la requête — 5ms
  │
  ├── [Span] Service CréerRéservation — 150ms
  │       ├── [Span] CatalogueACL.getSeanceInfo() — 45ms
  │       │       └── [Span] HTTP GET /catalogue/seances/SCR-456 — 40ms
  │       │
  │       ├── [Span] ReservationRepository.getPlacesOccupées() — 12ms
  │       │       └── [Span] PostgreSQL SELECT — 10ms
  │       │
  │       └── [Span] ReservationRepository.save() — 8ms
  │               └── [Span] PostgreSQL INSERT — 6ms
  │
  ├── [Span] Publish PaiementRequis → Bus — 3ms
  │
  │   [asynchrone — corrélé via correlation_id]
  │
  ├── [Span] Service TraiterPaiement (Paiements BC) — 4.2s
  │       ├── [Span] StripeAdapter.createPaymentIntent() — 4.1s
  │       └── [Span] PaymentRepository.save() — 8ms
  │
  └── [Span] Service ConfirmerRéservation (après webhook Stripe) — ~23s
          ├── [Span] ReservationRepository.load() — 5ms
          ├── [Span] Reservation.confirm_payment() — 0.1ms
          ├── [Span] ReservationRepository.save() — 7ms
          └── [Span] NotificationAdapter.sendEmail() — 200ms
```

Dans un outil de tracing comme **Jaeger** ou **Zipkin**, ce flux serait visualisé comme une cascade de spans. Le Correlation ID est utilisé comme `trace_id` pour relier toutes les spans appartenant au même flux.
