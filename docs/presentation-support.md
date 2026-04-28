---
title: "Billetterie Cinéma — Présentation TP DDD"
author: "Kevin CARTTIGUEANE"
date: "2026-04-27"
geometry: "margin=2cm"
---

# Billetterie Cinéma — TP fil rouge DDD

**Présentation orale finale — 10 minutes**

Auteur : Kevin CARTTIGUEANE — ESGI M2

---

# Slide 1 — Contexte & scénario choisi

**Domaine** : Billetterie & réservation pour un réseau de cinémas

**Acteurs principaux** :
- **Client** — réserve, paie, présente son QR code à l'entrée
- **Caissier** — vend en guichet, valide les billets
- **Gestionnaire** — programme les séances, fixe les tarifs

**Problématiques** :
1. Concurrence sur les places (zéro double-réservation)
2. Multi-canal cohérent (web, mobile, guichet)
3. Annulations / remboursements selon délai et tarif
4. Optimisation du remplissage (places isolées)
5. Tarification adaptée (plein, réduit, abonné)

**Scénario fil rouge** : Marie réserve 2 places pour Avatar 3, paie en ligne, reçoit ses billets PDF par email, et présente son QR code au caissier le soir même.

---

# Slide 2 — Bounded Contexts

| Bounded Context | Type DDD | Rôle principal |
|-----------------|----------|----------------|
| **ContexteRéservation** | **Core** | Cycle de vie réservation, places, billets |
| **ContextePaiement** | Generic | Transactions Stripe, remboursements |
| **ContexteCatalogue** | Supporting | Films, séances, tarifs, salles |
| *ContexteNotification* | Generic | Email + SMS (consommateur transverse) |

**Principe** : 1 Bounded Context = 1 modèle métier cohérent + 1 langage local.

> Dans `ContexteRéservation`, "Réservation" signifie *l'ensemble des places engagées par un client pour une séance, avec timeout 15 min*. Dans `ContextePaiement`, le mot n'apparaît même pas — on parle de `Transaction` indexée par `reservation_id`.

---

# Slide 3 — Context Map & patterns de relation

```
   ┌──────────────────┐
   │    CATALOGUE     │  Customer/Supplier (publie SéancePlanifiée)
   │   (Supporting)   │
   └────────┬─────────┘
            │ ACL (côté Réservations)
            ▼
   ┌──────────────────┐    Partnership
   │   RÉSERVATIONS   │ ◄─────────────► PAIEMENTS
   │      (Core)      │   (PaiementRequis / PaiementValidé)
   └──────────────────┘
                                │ Conformist
                                ▼
                              Stripe
```

| Source → Cible | Pattern | Justification |
|------------------|---------|---------------|
| Réservations → Catalogue | **Customer/Supplier + ACL** | Réservations dépend des séances, ACL traduit le modèle riche du Catalogue |
| Réservations ↔ Paiements | **Partnership** | Co-évolution, événements bidirectionnels |
| Paiements → Stripe | **Conformist** | On adopte le modèle Stripe sans le négocier |

---

# Slide 4 — Agrégat clé : `Réservation`

**Racine** : `Réservation`. **Frontière** : place(s), montant, statut, expiration.

**Invariants métier** :

| Invariant | Règle |
|-----------|-------|
| **INV-R1** | Max 10 places (anti-monopole) |
| **INV-R2** | Confirmation < expire_le (timeout 15 min) |
| **INV-R3** | Statut CONFIRMÉE ⇒ immuable |
| **INV-R4** | Unicité (place, séance) sur réservations actives |

**Scénario Given/When/Then** (INV-R2 sad path) :

> **Given** RES-789 EN_ATTENTE, expire à 19h45, il est 19h52.
> **When** un `PaiementValidé` arrive en retard.
> **Then** confirmation refusée, places libérées, remboursement déclenché.

---

# Slide 5 — Scénario end-to-end inter-contextes

**Marie réserve, paie, valide à l'entrée.**

```
1. Catalogue ─▶ SéancePlanifiée ─▶ Réservations (init 250 places)
2. Marie ──POST /reservations──▶ Réservations (RES-789, EN_ATTENTE)
3. Réservations ─▶ PaiementRequis ─▶ Paiements (PAY-001 PENDING)
4. Paiements ──Stripe──▶ webhook succeeded ──▶ PaiementValidé
5. Réservations consomme ─▶ confirm_payment() ─▶ CONFIRMÉE
6. Réservations ─▶ RéservationConfirmée ─▶ Notification (email + billets)
7. Caissier scan QR ─▶ BilletValidé ─▶ accès autorisé
```

**Tous les invariants vérifiés** : R1 (2 ≤ 10), R2 (19h52 < 20h01), R4 (places libres), P1 (28€ = 28€), P2 (premier paiement), P3 (SUCCESS immuable), P4 (idempotence webhook).

---

# Slide 6 — Architecture hexagonale + runtime

**Architecture hexagonale (couches)** :

```
[Client Web/App] ─HTTP─▶ [REST Adapter] ─▶ [Application Service]
                                              │
                                              ▼
                                          [Domain] (agrégats)
                                              │
                                       [Ports] (IReservationRepository, IPaymentGatewayPort)
                                              │
                                              ▼
                                       [Adapters] (PostgreSQL, Stripe, SendGrid)
```

**Runtime** : 4 services Docker autonomes, RabbitMQ pour les événements, API Gateway pour l'exposition externe, stack Prometheus/Loki/Jaeger/Grafana pour l'observabilité.

> 1 Bounded Context = 1 service = 1 base de données dédiée.

---

# Slide 7 — Observabilité & métriques

**Correlation ID** généré au gateway, propagé dans tous les logs et événements.

**3 métriques métier prioritaires** :

| Métrique | Type | Seuil |
|----------|------|-------|
| `reservations_conversion_rate` | gauge | < 60 % → Slack |
| `payments_failure_rate` | gauge | > 5 % → PagerDuty |
| `reservation_confirmation_latency_p95` | histogram | > 30 s → alerte |

**+1 métrique technique** : `http_request_duration_seconds` (P95 < 500 ms).

**Logging** : JSON structuré avec `correlation_id`, `service`, `context`, `event`, `metadata`.

---

# Conclusion

Le système :
- modélise le métier avec un **vocabulaire stable** (Ubiquitous Language)
- isole la complexité dans le **Core** (Réservations) et utilise des **Generic** pour les fonctions standard
- expose les agrégats via **REST**, communique entre BC via **événements**
- s'observe via **Correlation ID + métriques métier + logs structurés**
- évolue par **migration progressive** (versioning, ACL, feature flags)

**Aucune ligne de code applicatif** — tout est documentaire, conforme à la nature conceptuelle du TP.

> Documentation complète disponible dans `docs/` (22 fichiers).
