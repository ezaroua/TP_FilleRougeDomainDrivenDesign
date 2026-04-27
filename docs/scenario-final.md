# Scénario Final End-to-End — Billetterie Cinéma

> Chapitre 5 — Livrable 4 : Scénario complet impliquant au moins deux contextes.
> Narration + événements ordonnés + diagramme de séquence + invariants rappelés.

---

## Scénario : "Réservation, paiement et validation à l'entrée — Avatar 3"

### Narration complète (flux métier)

**Acteurs** : Marie (cliente), le Gestionnaire (admin cinéma), le Caissier (contrôleur d'accès)

**Étape 0 — Préparation (Catalogue BC)**
Le Gestionnaire planifie la séance "Avatar 3" du 15 mars 2026 à 20h15 en Salle IMAX (#SCR-456, 250 places, tarif plein 14,00€). L'événement `SéancePlanifiée` est publié. Le contexte Réservations le reçoit et initialise 250 places libres pour cette séance.

**Étape 1 — Consultation (Catalogue BC → Client)**
Marie consulte la programmation depuis l'app web. Elle interroge l'API du Catalogue : `GET /catalogue/seances?date=2026-03-15&film=Avatar+3`. Elle voit la séance SCR-456 avec 248 places disponibles (2 autres clients sont en cours de blocage). Elle sélectionne les places F11 et F12.

**Étape 2 — Réservation (Réservations BC)**
Marie soumet sa réservation. Le service `CréerRéservation` vérifie la disponibilité des places F11 et F12 (libres), crée l'agrégat Réservation #RES-789 avec statut EN_ATTENTE, expire_le = 20h01. Le montant total est calculé : 2 × 14,00€ = 28,00€. L'agrégat émet `PlacesRéservées`. Marie reçoit la réponse : 15 minutes pour payer.

**Étape 3 — Paiement (Paiements BC)**
Marie saisit ses coordonnées Visa. Le service `TraiterPaiement` vérifie que le montant (28,00€) correspond exactement au montant de la réservation (INV-P1). Un Payment #PAY-001 est créé en PENDING. L'adapter Stripe crée un PaymentIntent. Stripe traite la carte de Marie en 3 secondes. Un webhook `payment_intent.succeeded` est reçu. Le Payment passe à SUCCESS. L'événement `PaiementValidé` est publié avec le Correlation ID initial.

**Étape 4 — Confirmation (Réservations BC)**
Le service `ConfirmerRéservation` consomme `PaiementValidé`. Il charge la réservation #RES-789 (statut EN_ATTENTE, pas encore expirée — il est 19h52, expiration à 20h01). Il appelle `confirm_payment()` sur l'agrégat (INV-R2 vérifié). La réservation passe à CONFIRMÉE. Deux billets électroniques sont générés : BIL-001 (F11) et BIL-002 (F12) avec leurs QR codes. L'événement `RéservationConfirmée` est publié.

**Étape 5 — Notification (Generic)**
Le service de notification consomme `RéservationConfirmée` et envoie un email à Marie avec ses 2 billets PDF en pièce jointe. Elle reçoit l'email à 19h52.

**Étape 6 — Contrôle à l'entrée (Réservations BC)**
Le soir, à 20h10, Marie présente son QR code au caissier. Le Caissier scanne BIL-001. Le système `ValiderBillet` vérifie que le billet existe, appartient à la séance SCR-456 (heure de début 20h15, scan autorisé entre 20h00 et 20h30), et n'a pas déjà été utilisé. Le billet est marqué UTILISÉ. Marie entre dans la salle.

---

## Liste des événements déclenchés dans l'ordre

| # | Événement | Contexte producteur | Contexte(s) consommateur(s) | Déclencheur |
|---|-----------|--------------------|-----------------------------|-------------|
| 1 | `SéancePlanifiée` | Catalogue | Réservations | Gestionnaire planifie la séance |
| 2 | `PlacesRéservées` | Réservations | (interne, logs) | Client sélectionne les places |
| 3 | `PaiementRequis` | Réservations | Paiements | Réservation EN_ATTENTE créée |
| 4 | `PaiementValidé` | Paiements | Réservations | Stripe confirme le paiement |
| 5 | `RéservationConfirmée` | Réservations | Notification, Billetterie | Agrégat confirmé après paiement |
| 6 | `BilletsGénérés` | Réservations | Notification | Billets avec QR codes créés |
| 7 | `NotificationEnvoyée` | Notification (Generic) | (aucun) | Email envoyé au client |
| 8 | `BilletValidé` | Réservations | (logs, stats) | Caissier scanne le QR code |

---

## Diagramme de séquence final

```
Gestionnaire   Catalogue BC    Réservations BC   Paiements BC    Notification    Marie
     │               │               │                │                │           │
     │ Planifier     │               │                │                │           │
     │ séance SCR456 │               │                │                │           │
     │──────────────►│               │                │                │           │
     │               │ SéancePlanifié│                │                │           │
     │               │──────────────►│                │                │           │
     │               │               │ Init 250 places│                │           │
     │               │               │                │                │           │
     │               │               │                │                │           │
     │               │ GET /seances  │                │                │           │
     │               │◄──────────────────────────────────────────────────────────── │
     │               │────────────────────────────────────────────────────────────► │
     │               │               │                │                │           │
     │               │               │ POST /reserv.  │                │           │
     │               │               │◄───────────────────────────────────────────── │
     │               │               │ Vérifie dispo  │                │           │
     │               │               │ Crée RES-789   │                │           │
     │               │               │ PlacesRéservées│                │           │
     │               │               │ PaiementRequis │                │           │
     │               │               │───────────────►│                │           │
     │               │               │────────────────────────────────────────────► │
     │               │               │               (201 RES-789 EN_ATTENTE)       │
     │               │               │                │                │           │
     │               │               │                │ Crée PAY-001   │           │
     │               │               │ POST /payment  │                │           │
     │               │               │◄───────────────────────────────────────────── │
     │               │               │────────────────────────────────────────────► │
     │               │               │                │ (200 PENDING)              │
     │               │               │                │                │           │
     │               │               │                │ [Stripe webhook]           │
     │               │               │                │ PaiementValidé │           │
     │               │               │◄───────────────│                │           │
     │               │               │ confirm RES-789│                │           │
     │               │               │ Génère billets │                │           │
     │               │               │ RéservationConf│                │           │
     │               │               │────────────────────────────────►│           │
     │               │               │                │                │ sendEmail │
     │               │               │                │                │──────────►│
     │               │               │                │                │           │
     │               │               │                │                │  [20h10]  │
     │               │               │ Scan QR BIL-001│                │           │
     │               │               │◄─────────────────────────────────────────── │
     │               │               │ BilletValidé   │                │           │
     │               │               │ Accès autorisé │                │           │
     │               │               │────────────────────────────────────────────► │
```

---

## Rappel des invariants métier pertinents dans ce scénario

| Invariant | Moment de vérification | Résultat dans le scénario |
|-----------|------------------------|--------------------------|
| **INV-R1** : Max 10 places par réservation | Étape 2 — création de réservation | OK : 2 places < 10 |
| **INV-R2** : Confirmation avant expiration | Étape 4 — `confirm_payment()` | OK : 19h52 < 20h01 |
| **INV-R3** : Réservation confirmée immuable | Après étape 4 | OK : plus modifiable après CONFIRMÉE |
| **INV-P1** : Montant exact | Étape 3 — création du paiement | OK : 28,00€ = 28,00€ |
| **INV-P2** : Unicité du paiement | Étape 3 — vérification avant création | OK : aucun paiement SUCCESS existant pour RES-789 |
| **INV-P3** : Statut final immuable | Étape 3 — SUCCESS immuable | OK : le paiement SUCCESS ne peut plus changer |

---

## Contextes impliqués et leurs contributions

| Bounded Context | Rôle dans ce scénario | Pattern d'intégration |
|----------------|----------------------|-----------------------|
| **Catalogue** (Supporting) | Fournit les données de séance, publie SéancePlanifiée | Customer/Supplier (upstream) |
| **Réservations** (Core) | Orchestrateur central du scénario, gère places et billets | — (aggregate root du flux) |
| **Paiements** (Generic) | Traite la transaction financière, notifie le résultat | Partnership (bidirectionnel) |
| **Notification** (Generic) | Envoie l'email de confirmation avec les billets | Conformist (consomme RéservationConfirmée) |
