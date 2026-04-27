# Scénarios de test de domaine — Given / When / Then

> Chapitre 3 — Livrable 3 : Pour chaque invariant défini dans `invariants.md`, un scénario *happy path* (invariant respecté) et un scénario *sad path* (invariant violé), au format Given / When / Then **textuel**.
> **Aucun code** — uniquement des phrases métier en français.

---

## Agrégat Réservation

### Invariant R1 — Limite de 10 places par réservation

#### Scénario 1 — Happy path (ajout dans la limite)
- **Given** une réservation `RES-789` en statut EN_ATTENTE pour la séance `SCR-456`, contenant 8 places sélectionnées (F03 → F10).
- **When** Marie tente d'ajouter 2 places supplémentaires (F11, F12).
- **Then** les deux places sont ajoutées, la réservation contient désormais 10 places, le `montant_total` est recalculé (10 × 14,00€ = 140,00€) et la réservation reste en EN_ATTENTE.

#### Scénario 2 — Sad path (dépassement de la limite)
- **Given** une réservation `RES-789` en statut EN_ATTENTE contenant déjà 10 places.
- **When** le client tente d'ajouter une 11ᵉ place (G01).
- **Then** l'agrégat refuse l'opération avec le message « Une réservation ne peut pas contenir plus de 10 places », la réservation conserve ses 10 places, la place G01 reste libre pour les autres clients, aucun événement n'est émis.

---

### Invariant R2 — Expiration automatique sous 15 minutes

#### Scénario 1 — Happy path (confirmation dans les délais)
- **Given** une réservation `RES-789` créée à 19h30, `expire_le = 19h45`, statut EN_ATTENTE.
- **When** un événement `PaiementValidé` est consommé à 19h42 pour cette réservation.
- **Then** la réservation passe à CONFIRMÉE, les billets BIL-001 et BIL-002 sont générés avec leurs QR codes, l'événement `RéservationConfirmée` est publié sur le bus.

#### Scénario 2 — Sad path (confirmation après expiration)
- **Given** une réservation `RES-789` créée à 19h30, `expire_le = 19h45`, il est maintenant 19h52, le statut est toujours EN_ATTENTE.
- **When** un événement `PaiementValidé` arrive en retard (réseau saturé) pour cette réservation.
- **Then** l'agrégat refuse la confirmation avec le message « Réservation expirée, confirmation impossible », le statut passe à ANNULÉE, les places sont libérées, un remboursement automatique est déclenché côté ContextePaiement (`RemboursementAutomatique` requis).

---

### Invariant R3 — Immuabilité après confirmation

#### Scénario 1 — Happy path (consultation seule)
- **Given** une réservation `RES-789` au statut CONFIRMÉE, contenant les places F11 et F12.
- **When** le client consulte les détails de sa réservation via `GET /api/v1/reservations/RES-789`.
- **Then** le système retourne la réservation en lecture seule, sans aucun bouton de modification, avec les billets BIL-001 et BIL-002 et leurs QR codes.

#### Scénario 2 — Sad path (tentative de modification après confirmation)
- **Given** une réservation `RES-789` au statut CONFIRMÉE, contenant les places F11 et F12.
- **When** le client (ou un caissier) tente d'ajouter la place F13 à cette réservation.
- **Then** l'agrégat refuse l'opération avec le message « Une réservation confirmée ne peut plus être modifiée — annulez puis recréez », aucune modification n'est persistée, le client est invité à passer par la procédure d'annulation.

---

### Invariant R4 — Unicité d'une place sur une séance

#### Scénario 1 — Happy path (place encore libre)
- **Given** la séance `SCR-456`, la place F11 n'est référencée dans aucune réservation active (aucune EN_ATTENTE ni CONFIRMÉE).
- **When** Marie crée une nouvelle réservation incluant F11.
- **Then** la place est attribuée à `RES-789`, le repository persiste le lien (place, séance) → réservation, l'événement `PlacesRéservées` est publié.

#### Scénario 2 — Sad path (place déjà bloquée par un autre client)
- **Given** la séance `SCR-456`, la place F11 est déjà incluse dans la réservation `RES-700` au statut EN_ATTENTE (créée 30 secondes plus tôt par un autre client).
- **When** Marie tente de créer une réservation incluant F11.
- **Then** le système répond `HTTP 409 Conflict` avec le message « La place F11 n'est plus disponible — choisissez une autre place », aucune réservation n'est créée pour Marie, F11 reste attribuée à `RES-700`.

---

## Agrégat Paiement

### Invariant P1 — Montant exact requis

#### Scénario 1 — Happy path (montants identiques)
- **Given** une réservation `RES-789` avec `montant_total = 28,00€`, l'événement `PaiementRequis` est publié.
- **When** le ContextePaiement crée un paiement `PAY-001` avec `montant = 28,00€` et appelle Stripe.
- **Then** Stripe accepte le PaymentIntent, le statut passe à PENDING, après webhook le statut devient SUCCESS et l'événement `PaiementValidé` est publié.

#### Scénario 2 — Sad path (montants différents)
- **Given** une réservation `RES-789` avec `montant_total = 28,00€`, un message altéré ou un bug applicatif tente de créer un paiement avec `montant = 25,00€`.
- **When** le ContextePaiement valide la création de l'agrégat Paiement.
- **Then** la création est refusée avec le message « Montant incorrect : attendu 28,00€, reçu 25,00€ », aucun PaymentIntent n'est créé chez Stripe, un log ERROR est émis avec le `correlation_id`, l'événement `PaiementÉchoué` est publié pour libérer la réservation.

---

### Invariant P2 — Unicité du paiement réussi par réservation

#### Scénario 1 — Happy path (premier paiement)
- **Given** la réservation `RES-789` n'a aucun paiement existant.
- **When** le ContextePaiement crée le paiement `PAY-001` pour cette réservation.
- **Then** la création est acceptée, le paiement est persisté, Stripe est appelé, en cas de SUCCESS la réservation est confirmée.

#### Scénario 2 — Sad path (double paiement)
- **Given** la réservation `RES-789` possède déjà un paiement `PAY-001` au statut SUCCESS.
- **When** un message dupliqué (à cause d'un retry de bus) demande la création d'un second paiement `PAY-002` pour la même réservation.
- **Then** le repository refuse la création avec le message « La réservation RES-789 a déjà un paiement SUCCESS (PAY-001) », aucun second appel à Stripe n'est effectué, le client n'est jamais débité deux fois, un log WARN est émis pour audit.

---

### Invariant P3 — Immuabilité du statut final (SUCCESS / FAILED)

#### Scénario 1 — Happy path (consultation d'un paiement finalisé)
- **Given** un paiement `PAY-001` au statut SUCCESS, traité le 15/03/2026 à 19h45.
- **When** le caissier consulte le paiement pour préparer un remboursement.
- **Then** le statut SUCCESS est lisible, mais le système refuse toute mutation directe ; il propose à la place de créer une nouvelle entité `Remboursement` liée à PAY-001, sans toucher au statut original.

#### Scénario 2 — Sad path (tentative de re-traitement)
- **Given** un paiement `PAY-002` au statut FAILED (carte refusée).
- **When** un opérateur tente de relancer le même paiement (set status = PENDING).
- **Then** l'agrégat refuse avec le message « Paiement PAY-002 déjà finalisé avec statut FAILED — créez un nouveau paiement pour réessayer », l'opérateur est invité à initier `PAY-003` avec un nouveau moyen de paiement.

---

### Invariant P4 — Idempotence des webhooks Stripe

#### Scénario 1 — Happy path (premier reçu d'un événement)
- **Given** Stripe envoie un webhook `payment_intent.succeeded` avec `event_id = evt_001` pour le paiement `PAY-001` (statut PENDING).
- **When** le ContextePaiement reçoit l'événement pour la première fois.
- **Then** `evt_001` est enregistré dans la table de déduplication, le statut passe à SUCCESS, l'événement `PaiementValidé` est publié sur le bus une seule fois.

#### Scénario 2 — Sad path (réception en doublon)
- **Given** Stripe a envoyé `evt_001` une première fois, le système l'a traité avec succès. Suite à un timeout réseau, Stripe renvoie le même `evt_001` 30 secondes plus tard.
- **When** le ContextePaiement reçoit `evt_001` une seconde fois.
- **Then** la table de déduplication est consultée, `evt_001` y figure déjà, le système ignore l'événement, ne modifie pas le statut, ne republie pas `PaiementValidé`, retourne HTTP 200 à Stripe pour stopper les retries.

---

## Récapitulatif des scénarios

| Invariant | Happy Path (résumé) | Sad Path (résumé) |
|-----------|---------------------|---------------------|
| **INV-R1** Max 10 places | 8 + 2 = 10 places acceptées | 11ᵉ place refusée |
| **INV-R2** Timeout 15 min | Confirmation à 19h42 (avant 19h45) → CONFIRMÉE | Confirmation à 19h52 → ANNULÉE + remboursement |
| **INV-R3** Immuabilité après confirmation | Lecture seule autorisée | Modification refusée — annulation requise |
| **INV-R4** Unicité place/séance | Place libre → réservée | Place déjà bloquée → 409 Conflict |
| **INV-P1** Montant exact | 28,00€ = 28,00€ → accepté | 25,00€ ≠ 28,00€ → refusé |
| **INV-P2** Unicité paiement réussi | Premier PAY-001 → créé | PAY-002 dupliqué → rejeté |
| **INV-P3** Statut final immuable | Consultation OK | Re-traitement FAILED → refusé |
| **INV-P4** Idempotence webhook | Premier evt_001 → traité | evt_001 dupliqué → ignoré |

Au total : **8 invariants × 2 scénarios = 16 scénarios Given/When/Then** couvrant l'intégralité des règles métier des deux agrégats principaux.
