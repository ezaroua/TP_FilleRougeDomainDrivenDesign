# Architecture Runtime — Billetterie Cinéma

> Chapitre 6 — Livrable 2 : Schéma et description de l'architecture en exécution.

---

## Schéma de l'architecture runtime

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                          INTERNET / CLIENTS                                   ║
║          [App Web]      [App Mobile]      [Terminal Caissier]                 ║
╚══════════════════════════╤═══════════════════════════════════════════════════╝
                           │ HTTPS :443
                           ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                          API GATEWAY (nginx/Kong)                             ║
║   Route :                                                                    ║
║   /api/v1/catalogue/*   → catalogue-service:8001                            ║
║   /api/v1/reservations/* → reservations-service:8002                        ║
║   /api/v1/payments/*    → paiements-service:8003                            ║
║   Correlation-ID injecté ici si absent                                       ║
╚══╤═══════════════════════╤═══════════════════════╤════════════════════════╝
   │                       │                       │
   ▼ :8001                 ▼ :8002                 ▼ :8003
╔══════════════╗  ╔═════════════════════╗  ╔══════════════════════╗
║  CATALOGUE   ║  ║    RÉSERVATIONS     ║  ║      PAIEMENTS       ║
║   SERVICE    ║  ║      SERVICE        ║  ║       SERVICE        ║
║  (Supported) ║  ║      (Core)         ║  ║      (Generic)       ║
║              ║  ║                     ║  ║                      ║
║ Films        ║  ║ Réservation         ║  ║ Payment              ║
║ Séances      ║  ║ Seat                ║  ║ Transaction          ║
║ Salles       ║  ║ Billet              ║  ║ Remboursement        ║
╚══════╤═══════╝  ╚══════════╤══════════╝  ╚══════════╤═══════════╝
       │                     │                         │
       ▼                     ▼                         ▼
╔═════════════╗   ╔══════════════════╗    ╔════════════════════╗
║ catalogue_db║   ║ reservations_db  ║    ║   payments_db      ║
║ (PostgreSQL)║   ║  (PostgreSQL)    ║    ║   (PostgreSQL)     ║
╚═════════════╝   ╚══════════════════╝    ╚════════════════════╝

═══════════════════════════════════════════════════════════════════
                  BUS D'ÉVÉNEMENTS (RabbitMQ)
                [corr-id propagé dans chaque message]
───────────────────────────────────────────────────────────────────
  catalogue-service     → publish: SéancePlanifiée
  reservations-service  → publish: PlacesRéservées, PaiementRequis, RéservationConfirmée
  paiements-service     → publish: PaiementValidé, PaiementÉchoué

  reservations-service  ← subscribe: SéancePlanifiée, PaiementValidé
  paiements-service     ← subscribe: PaiementRequis
  notification-service  ← subscribe: RéservationConfirmée
═══════════════════════════════════════════════════════════════════

╔═══════════════════════════════════════════════════╗
║           NOTIFICATION SERVICE (Generic)           ║
║  SendGrid (email) + Twilio (SMS)                   ║
║  Consomme: RéservationConfirmée                    ║
╚═══════════════════════════════════════════════════╝

╔═════════════════════════════════════════════════════════════════╗
║               EXTERNAL SERVICES                                  ║
║   [Stripe API]         [SendGrid]         [Twilio SMS]           ║
╚═════════════════════════════════════════════════════════════════╝

╔═════════════════════════════════════════════════════════════════╗
║           OBSERVABILITY STACK                                    ║
║                                                                  ║
║  Prometheus ──► Grafana (métriques)                             ║
║  Loki       ──► Grafana (logs)                                  ║
║  Jaeger     ──► Grafana (tracing distribué)                     ║
║                                                                  ║
║  Correlation-ID traverse tous les services ──────────────────── ║
║  [catalogue] ──► [reservations] ──► [paiements] ──► [notif]    ║
╚═════════════════════════════════════════════════════════════════╝
```

---

## Description textuelle de l'architecture runtime

Le système de billetterie cinéma est déployé sous forme de **4 services métier indépendants** (Catalogue, Réservations, Paiements, Notification) exposés derrière un **API Gateway** unique. Chaque service possède sa propre base de données PostgreSQL dédiée — aucun service n'accède directement à la base d'un autre.

La **communication synchrone** (REST) est utilisée pour les opérations où le résultat est immédiatement nécessaire : consultation du catalogue par les clients web, et lecture des informations de séance par le service Réservations lors de la création d'une réservation.

La **communication asynchrone** (RabbitMQ) est utilisée pour les intégrations entre contextes métier : déclenchement du paiement, notification de confirmation, initialisation des disponibilités lors d'une nouvelle séance. Le découplage temporel permet à chaque service de fonctionner indépendamment même si un autre est temporairement indisponible.

Le **Correlation ID** est injecté au niveau de l'API Gateway et propagé dans tous les messages REST (header `X-Correlation-ID`) et événements (champ `correlation_id`). La stack d'observabilité (Prometheus + Loki + Jaeger + Grafana) agrège toutes les métriques, logs et traces en s'appuyant sur ce Correlation ID comme lien commun.

En production, l'orchestration Kubernetes garantit la haute disponibilité de chaque service (minimum 2 replicas) et assure le redémarrage automatique en cas de défaillance. Le déploiement suit une stratégie de **rolling update** pour éviter les coupures de service.

---

## Flux du Correlation ID à travers le système runtime

```
Client Web
    │ (pas de Correlation ID)
    ▼
API Gateway
    │ Génère: X-Correlation-ID: corr-a1b2c3d4
    │ Injecte dans le header HTTP
    ▼
reservations-service
    │ Lit le X-Correlation-ID
    │ Log: {"correlation_id": "corr-a1b2c3d4", ...}
    │ Publie événement PaiementRequis avec correlation_id
    ▼
RabbitMQ
    │ Message contient correlation_id
    ▼
paiements-service
    │ Récupère correlation_id du message
    │ Log: {"correlation_id": "corr-a1b2c3d4", ...}
    │ Publie PaiementValidé avec le même correlation_id
    ▼
reservations-service (handler)
    │ Même correlation_id dans les logs
    │ Publie RéservationConfirmée avec le même correlation_id
    ▼
notification-service
    │ Même correlation_id dans les logs
```

Résultat : en filtrant les logs de tous les services sur `correlation_id = "corr-a1b2c3d4"`, on reconstitue le parcours complet de la réservation de Marie.
