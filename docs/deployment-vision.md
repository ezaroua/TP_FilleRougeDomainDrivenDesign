# Vision de déploiement — Billetterie Cinéma

> Chapitre 6 — Livrable 1 : Description conceptuelle de la mise en production avec une vision Docker.
> **Aucun Dockerfile ni docker-compose réel — uniquement du pseudo-code annoté.**

---

## 1. Description du déploiement conceptuel

Dans une mise en production réelle, **chaque Bounded Context devient un service autonome**, packagé dans un conteneur Docker indépendant. Cette correspondance 1:1 entre BC et service applique le principe DDD selon lequel les frontières contextuelles guident les frontières de déploiement.

Le système complet comprendrait **4 services métier**, **3 bases de données**, **un bus d'événements**, **une stack d'observabilité** et **une passerelle d'API** pour exposer le tout à l'extérieur.

### Services métier (un par Bounded Context)

| Service | Bounded Context | Type DDD | Image conceptuelle | Port interne |
|---------|------------------|----------|---------------------|---------------|
| `catalogue-service` | ContexteCatalogue | Supporting | `cinema/catalogue:1.0.0` | 8001 |
| `reservations-service` | ContexteRéservation | **Core** | `cinema/reservations:1.0.0` | 8002 |
| `paiements-service` | ContextePaiement | Generic | `cinema/paiements:1.0.0` | 8003 |
| `notification-service` | (Generic transverse) | Generic | `cinema/notifications:1.0.0` | 8004 |

### Bases de données (isolation par contexte)

| Base | Service consommateur | Image | Justification |
|------|----------------------|-------|----------------|
| `catalogue_db` | catalogue-service | `postgres:16` | Données du catalogue, lecture intensive |
| `reservations_db` | reservations-service | `postgres:16` | Cohérence transactionnelle des réservations |
| `payments_db` | paiements-service | `postgres:16` | Auditabilité financière, isolement PCI-DSS |

> **Principe d'isolation strict** : aucun service n'accède directement à une base d'un autre service. Toute donnée transverse passe par les APIs REST ou par le bus d'événements.

### Infrastructure transverse

| Composant | Image conceptuelle | Rôle |
|-----------|---------------------|------|
| `message-broker` | `rabbitmq:3.13` | Bus d'événements (PaiementRequis, PaiementValidé, SéancePlanifiée…) |
| `api-gateway` | `kong:3` ou `nginx:alpine` | Routing, TLS, rate-limiting, génération du Correlation ID |
| `prometheus` | `prom/prometheus:latest` | Collecte des métriques |
| `loki` | `grafana/loki:latest` | Agrégation des logs structurés |
| `jaeger` | `jaegertracing/all-in-one` | Tracing distribué |
| `grafana` | `grafana/grafana:latest` | Visualisation des dashboards |

---

## 2. Communications REST vs Événements

### Synchrone (REST)

| Source | Cible | Endpoint | Pattern |
|--------|-------|----------|---------|
| Client (Web/App) | api-gateway → reservations-service | `POST /api/v1/reservations` | (entrée externe) |
| Client (Web/App) | api-gateway → catalogue-service | `GET /api/v1/seances` | (entrée externe) |
| reservations-service | catalogue-service | `GET /catalogue/seances/{id}` | Customer/Supplier + ACL |
| paiements-service | Stripe (externe) | `POST /v1/payment_intents` | Conformist |

### Asynchrone (RabbitMQ)

| Producteur | Topic / Queue | Consommateur(s) | Pattern |
|-------------|--------------|----------------|---------|
| catalogue-service | `cinema.seances.planned` | reservations-service | Customer/Supplier |
| reservations-service | `cinema.paiements.required` | paiements-service | Partnership |
| paiements-service | `cinema.paiements.validated` | reservations-service | Partnership |
| reservations-service | `cinema.reservations.confirmed` | notification-service | Conformist (downstream) |

---

## 3. Exemple annoté de Dockerfile fictif (pseudo-code)

```dockerfile
# ==============================================================
# PSEUDO-DOCKERFILE — illustratif uniquement
# Service : reservations-service (ContexteRéservation - Core)
# ==============================================================
FROM python:3.12-slim

# --- Métadonnées DDD ---
LABEL bounded_context="ContexteRéservation"
LABEL domain_type="core"
LABEL contract_version="v1"

# --- Sécurité : utilisateur non-root ---
RUN useradd -m -u 1001 appuser
USER appuser
WORKDIR /app

# --- Dépendances applicatives (couches Application + Infra) ---
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Code source organisé par couches hexagonales ---
COPY --chown=appuser:appuser ./domain/        ./domain/
COPY --chown=appuser:appuser ./application/   ./application/
COPY --chown=appuser:appuser ./adapters/      ./adapters/

# --- Port applicatif (l'api-gateway expose vers l'externe) ---
EXPOSE 8002

# --- Healthcheck métier ---
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

# --- Démarrage : ASGI server avec adapter REST ---
CMD ["uvicorn", "adapters.rest_api.main:app", \
     "--host", "0.0.0.0", "--port", "8002"]

# --- Variables d'environnement attendues à l'exécution ---
# DATABASE_URL=postgresql://user:***@reservations-db:5432/reservations_db
# BROKER_URL=amqp://guest:***@message-broker:5672/
# CATALOGUE_SERVICE_URL=http://catalogue-service:8001
# OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
# LOG_LEVEL=INFO
```

### Annotations clés

| Section | Pourquoi c'est important |
|---------|---------------------------|
| `LABEL bounded_context` | Permet de filtrer rapidement les conteneurs par BC dans Kubernetes/Docker. Très utile pour la gouvernance et l'observabilité (groupage par contexte). |
| Utilisateur non-root | Surface d'attaque réduite, contrainte standard en production. |
| Dépendances séparées des sources | Optimise la mise en cache des layers Docker — on ne réinstalle pas les libs à chaque changement de code. |
| Healthcheck métier | Permet à l'orchestrateur de redémarrer le conteneur s'il devient malsain (ex. perte de connexion DB persistante). |
| Variables d'env | Aucune URL en dur, configuration externalisée — principe 12-Factor App. |

---

## 4. Schéma de déploiement (vue logique)

```
                                   ┌─────────────────────────────┐
                                   │   Internet / Clients         │
                                   │  Web · App · Caissier        │
                                   └──────────────┬──────────────┘
                                                  │ HTTPS :443
                                                  ▼
                                  ┌─────────────────────────────┐
                                  │       API GATEWAY            │
                                  │ - TLS termination            │
                                  │ - Routing par BC             │
                                  │ - Génération X-Correlation-ID│
                                  └──┬──────────┬──────────┬─────┘
                                     │          │          │
                       ┌─────────────┘          │          └─────────────┐
                       ▼ :8001                  ▼ :8002                  ▼ :8003
            ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
            │ catalogue-service│      │ reservations-svc │      │ paiements-service│
            │  (Supporting)    │      │  (Core)          │      │  (Generic)       │
            └────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
                     │                         │                         │
                     ▼                         ▼                         ▼
              [catalogue_db]           [reservations_db]           [payments_db]

      ────────────────────────────────────────────────────────────────────────
                                  RABBITMQ (bus d'événements)
                  publish/subscribe avec correlation_id propagé partout
      ────────────────────────────────────────────────────────────────────────

                        ┌──────────────────────┐         ┌──────────────────┐
                        │ notification-service │         │  Stripe / Twilio │
                        │     (Generic)        │ ──HTTP──▶│     (externes)   │
                        └──────────────────────┘         └──────────────────┘

      ┌─────────────────────────────────────────────────────────────────────┐
      │ OBSERVABILITY STACK : Prometheus · Loki · Jaeger · Grafana          │
      └─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Stratégies d'évolution sans casser l'existant

### a) Refactoring continu du modèle
- Renommage interne libre tant que les contrats publics restent stables.
- Versionner les agrégats internes ne demande **aucun** déploiement coordonné si les schémas externes ne bougent pas.

### b) Compatibilité ascendante des APIs
- Ne **jamais** supprimer un champ d'une API REST ou d'un événement publié.
- Ajouter de nouveaux champs comme **optionnels** uniquement.
- Versionner explicitement (`/api/v1` → `/api/v2`) pour les changements *breaking*.
- Maintenir 3 mois de chevauchement avant dépréciation.

### c) Migration progressive (introduction d'un nouveau BC)
Exemple : ajout d'un `ContexteFidélité` (programme de points).
1. Déployer le `fidelite-service` indépendamment.
2. Le brancher en consommateur des événements `RéservationConfirmée` (zéro impact sur Réservations).
3. Activer un *feature flag* dans l'application web pour exposer la fonctionnalité à 10 % des clients.
4. Monter en charge progressivement après validation des métriques.
5. Pas une seule ligne modifiée dans Réservations / Paiements / Catalogue.

### d) Event Sourcing (vision long terme)
Si Réservations devient extrêmement complexe, on peut envisager de migrer vers du Event Sourcing :
- Conserver l'historique exhaustif des faits métier (`PlacesRéservées`, `RéservationConfirmée`, `RéservationAnnulée`).
- Reconstruire l'état courant par rejeu.
- Permet d'auditer rétroactivement et de répondre à des questions « ce qui se serait passé si… ».

> Cette technique n'est pas requise pour ce TP, mais constitue un cap d'évolution pertinent pour la richesse fonctionnelle attendue.

---

## 6. Récapitulatif

| Aspect | Choix conceptuel | Justification |
|--------|-------------------|---------------|
| Découpage en services | 1 service par Bounded Context | Aligne la frontière de déploiement sur la frontière métier |
| Bases de données | Une par service | Isolement des cycles de vie, indépendance des migrations |
| Communication interne | REST (synchrone) + RabbitMQ (asynchrone) | REST pour les lectures rapides, événements pour les flux découplés |
| Exposition externe | API Gateway | Sécurité, observabilité, routage centralisé |
| Observabilité | Prometheus + Loki + Jaeger + Grafana | Métriques + logs + traces, tous corrélés via `correlation_id` |
| Évolution | Versionning + ACL + feature flags | Migration progressive sans rupture |
