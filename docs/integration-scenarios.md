# Scénarios d'Intégration — Architecture Hexagonale

> Chapitre 4 — Livrable 4 : Scénario end-to-end traversant toutes les couches.
> **Aucun code** — flux narratif, diagramme de séquence et responsabilités par couche.

---

## Scénario : "Un client réserve et paie 2 places pour Avatar 3"

### Narration complète

Marie, cliente enregistrée (#CLI-123), souhaite voir "Avatar 3" le soir du 15 mars 2026 avec son ami. Elle ouvre l'application web de la billetterie et consulte la programmation. Elle choisit la séance de 20h15 en Salle IMAX (#SCR-456) et sélectionne les places F11 et F12.

Elle clique sur "Réserver". L'application envoie une requête `POST /api/v1/reservations` au système. L'adapter REST reçoit la requête, génère un Correlation ID unique `corr-a1b2c3d4` et la transforme en commande métier.

Le service applicatif `CréerRéservation` interroge d'abord le Catalogue (via l'ACL) pour confirmer que la séance SCR-456 existe bien et que le tarif est à 11,50€. Il vérifie ensuite dans le repository que les places F11 et F12 ne sont pas déjà occupées.

Les vérifications passées, il crée un agrégat `Réservation` dans le domaine. L'agrégat calcule le montant total (23,00€), fixe l'expiration à 20h01 (15 minutes) et émet un événement `PlacesRéservées`. La réservation est persistée via le repository (PostgreSQL).

La réponse est retournée à Marie : sa réservation #RES-789 est créée avec statut EN_ATTENTE, et elle a 15 minutes pour payer.

Marie saisit ses coordonnées bancaires. L'application envoie une requête `POST /api/v1/payments` avec `reservation_id: RES-789` et `montant: 23.00`. Le service applicatif `TraiterPaiement` vérifie la cohérence du montant (INV-P1) puis appelle le port `IPaymentGatewayPort`. L'adapter Stripe traduit l'appel en un `PaymentIntent` Stripe.

Stripe retourne immédiatement un statut `processing`. Quelques secondes plus tard, Stripe envoie un webhook `payment_intent.succeeded`. L'adapter Stripe reçoit le webhook, retrouve le paiement via son `transaction_id`, et met à jour son statut à SUCCESS.

Le service applicatif `ConfirmerRéservation` est déclenché : il charge la réservation #RES-789, appelle `confirm_payment()` sur l'agrégat (qui vérifie INV-R2 : pas encore expirée), passe le statut à CONFIRMÉE, génère 2 billets électroniques avec leurs QR codes. Une notification email est envoyée via le port `INotificationPort` (SendGrid adapter). Marie reçoit un email avec ses billets.

---

## Diagramme de séquence UML (conceptuel)

```
Marie           REST Adapter    App Service     Domaine         Repository      Stripe
  │                  │               │              │                │              │
  │ POST /reservations│               │              │                │              │
  │─────────────────►│               │              │                │              │
  │                  │ CréerRésa()   │              │                │              │
  │                  │──────────────►│              │                │              │
  │                  │               │ getCatalogue()│                │              │
  │                  │               │──────────────►              │              │
  │                  │               │◄─ SeanceInfo  │                │              │
  │                  │               │ getPlaces()   │                │              │
  │                  │               │──────────────────────────────►│              │
  │                  │               │◄─────── PlacesDisponibles      │              │
  │                  │               │ new Réservation()              │              │
  │                  │               │─────────────►│                │              │
  │                  │               │◄─ Réservation │                │              │
  │                  │               │ save(résa)   │                │              │
  │                  │               │──────────────────────────────►│              │
  │                  │               │◄─────── savedId                │              │
  │                  │◄──────────────│              │                │              │
  │◄─────────────────│ 201 RES-789   │              │                │              │
  │                  │               │              │                │              │
  │ POST /payments   │               │              │                │              │
  │─────────────────►│               │              │                │              │
  │                  │ TraiterPaie() │              │                │              │
  │                  │──────────────►│              │                │              │
  │                  │               │ createPayment │                │              │
  │                  │               │─────────────►│                │              │
  │                  │               │◄─ Payment    │                │              │
  │                  │               │ chargeStripe()│                │              │
  │                  │               │──────────────────────────────────────────────►│
  │                  │               │◄─────────────────────────────────── PaymentIntent│
  │                  │◄──────────────│              │                │              │
  │◄─────────────────│ 200 PENDING   │              │                │              │
  │                  │               │              │                │              │
  │                  │     [webhook: payment.succeeded]              │              │
  │                  │◄──────────────────────────────────────────────────────────── │
  │                  │ ConfirmerRésa()               │                │              │
  │                  │──────────────►│              │                │              │
  │                  │               │ confirm()    │                │              │
  │                  │               │─────────────►│                │              │
  │                  │               │◄─ CONFIRMÉE  │                │              │
  │                  │               │ save(résa)   │                │              │
  │                  │               │──────────────────────────────►│              │
  │                  │               │ sendEmail()  │                │              │
  │                  │               │──────────────► [SendGrid]      │              │
  │◄═══════════════ Email de confirmation avec billets ══════════════│              │
```

---

## Responsabilités par couche dans ce flux

| Couche | Responsabilité dans ce flux | Technologie conceptuelle |
|--------|-----------------------------|--------------------------|
| **Interface externe** | Présenter le formulaire de sélection et recevoir les actions utilisateur | App Web (React) |
| **REST Adapter** | Recevoir HTTP, générer Correlation ID, transformer en commande métier | FastAPI |
| **Service Applicatif** | Orchestrer CréerRéservation, TraiterPaiement, ConfirmerRéservation | Python (Application Layer) |
| **Domaine** | Appliquer les invariants, calculer le montant, émettre les events | Agrégats purs |
| **Repository Adapter** | Traduire les agrégats en SQL et persister en base | PostgreSQL |
| **Payment Gateway Adapter** | Appeler Stripe API (Conformist) | Stripe SDK (ACL) |
| **Notification Adapter** | Envoyer l'email de confirmation avec billets | SendGrid |

---

## Points de cohérence inter-contextes dans ce flux

| Étape | Context impliqué | Pattern | Donnée échangée |
|-------|-----------------|---------|----------------|
| Récupération séance | Réservations → Catalogue | ACL (Customer/Supplier) | SeanceInfo {id, tarif, salle, horaire} |
| Déclenchement paiement | Réservations → Paiements | Partnership | {reservation_id, montant_total, client_id} |
| Confirmation après paiement | Paiements → Réservations | Partnership (event) | PaiementValidé {transaction_id, reservation_id} |
| Appel Stripe | Paiements → Stripe | Conformist | PaymentIntent (format Stripe) |
