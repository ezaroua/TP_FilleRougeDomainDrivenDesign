# Agrégats et Invariants — Billetterie Cinéma

> Chapitre 3 — Livrable 2 : Identification des agrégats clés, de leurs frontières, de leurs racines et de leurs invariants métier.
> **100 % conceptuel — aucun code applicatif n'est produit.**

---

## Vue d'ensemble des agrégats

Deux agrégats portent les règles métier différenciantes du contexte **Réservations** et du contexte **Paiements** :

| Agrégat | Bounded Context | Racine d'agrégat | Rôle métier principal |
|---------|------------------|------------------|------------------------|
| **Réservation** | ContexteRéservation (Core) | `Réservation` | Coordonne le cycle de vie d'une demande de places, garantit l'unicité de chaque place, applique les règles de timeout et d'immuabilité après confirmation. |
| **Paiement** | ContextePaiement (Generic) | `Paiement` | Coordonne le cycle de vie d'une transaction financière, garantit la cohérence du montant et l'immuabilité des transactions finalisées. |

---

## Agrégat 1 — Réservation

### Racine d'agrégat
`Réservation` — Seule entrée publique de l'agrégat. Toute commande métier (ajouter une place, confirmer, annuler) passe par la racine, qui garantit la cohérence transactionnelle et la validité des invariants.

### Frontières
**Inclus dans l'agrégat (cohérence forte) :**
- Liste des `SeatId` réservés (références opaques vers les places)
- `StatutRéservation` (objet valeur : EN_ATTENTE / CONFIRMÉE / ANNULÉE)
- `Montant` total calculé
- Horodatages `cree_le` et `expire_le`
- Référence vers le `ClientId`

**Exclus de l'agrégat (cohérence éventuelle) :**
- Détails complets des `Seat` (gérés au niveau de la `Séance` côté Catalogue)
- L'agrégat `Paiement` (lien par référence d'identifiant uniquement)
- Les billets émis (générés par un service applicatif après confirmation)

### Invariants métier (≥3)

| Invariant | Description métier (3–4 phrases) | Conséquence si non respecté |
|-----------|-----------------------------------|------------------------------|
| **INV-R1 — Limite de 10 places par réservation** | Une même réservation ne peut contenir plus de 10 places. Cette règle anti-monopole vise à garantir l'équité d'accès lors des sorties très demandées et empêche un seul client d'accaparer une rangée entière. Au-delà de 10 places, la demande relève d'un acte commercial groupé géré hors-ligne. | Risque de spéculation et de revente, expérience dégradée pour les autres clients lors des sorties à forte affluence, image négative du cinéma. |
| **INV-R2 — Expiration automatique sous 15 minutes** | Toute réservation EN_ATTENTE doit être confirmée dans les 15 minutes suivant sa création, sinon elle expire et les places sont libérées. Ce timeout protège l'inventaire des places contre des blocages indéfinis et fluidifie le tunnel de vente. | Places bloquées indéfiniment, perte de chiffre d'affaires sur des sièges vides alors que d'autres clients souhaitent réserver, mauvais taux de remplissage. |
| **INV-R3 — Immuabilité après confirmation** | Une réservation au statut CONFIRMÉE ne peut plus voir ses places ni son montant modifiés. Toute modification doit obligatoirement passer par une annulation suivie d'une nouvelle réservation. | Incohérence entre les billets émis et le contenu réel de la réservation, problèmes de comptabilité, contestations clients. |
| **INV-R4 — Unicité d'une place sur une séance** | Sur une même séance, une place ne peut figurer que dans une seule réservation active (EN_ATTENTE ou CONFIRMÉE). Une place déjà bloquée n'est plus disponible pour un autre client tant qu'elle n'est pas libérée. | Double réservation, deux clients arrivent sur le même siège, conflit physique et perte de confiance. |

### Cycle de vie de l'agrégat

```
       [créer Réservation]
              │
              ▼
     ┌──────────────────┐    expire_le dépassé
     │   EN_ATTENTE     │ ────────────────────────► ANNULÉE (par timeout)
     └────────┬─────────┘
              │ paiement validé avant expiration
              ▼
     ┌──────────────────┐    annulation client / direction
     │   CONFIRMÉE      │ ────────────────────────► ANNULÉE (avec remboursement)
     └──────────────────┘
```

### Schéma UML conceptuel — Frontière de l'agrégat Réservation

```
╔══════════════════════════════════════════════════════════╗
║              AGRÉGAT « Réservation »                      ║
║                                                            ║
║       ┌────────────────────────────────────┐              ║
║       │   Réservation  (RACINE)            │              ║
║       │────────────────────────────────────│              ║
║       │  reservation_id : ReservationId    │              ║
║       │  client_id      : ClientId         │              ║
║       │  seance_id      : SeanceId         │              ║
║       │  statut         : StatutRéservation│              ║
║       │  montant_total  : Montant          │              ║
║       │  cree_le        : Horodatage       │              ║
║       │  expire_le      : Horodatage       │              ║
║       └────────────────────────────────────┘              ║
║              │                  │                          ║
║              ▼  contient        ▼  composé de              ║
║   ┌────────────────────┐  ┌────────────────────┐          ║
║   │  Liste<SeatId>     │  │  StatutRéservation │          ║
║   │  (1..10)           │  │  ENUM (VO)         │          ║
║   └────────────────────┘  └────────────────────┘          ║
║                                                            ║
║   Invariants gardés par la racine :                        ║
║   • INV-R1 : taille(places) ≤ 10                           ║
║   • INV-R2 : confirmation < expire_le                      ║
║   • INV-R3 : pas de mutation si statut = CONFIRMÉE         ║
║   • INV-R4 : unicité (place, séance) côté repository       ║
╚══════════════════════════════════════════════════════════╝
                       │ référence (identifiant uniquement)
                       ▼
            ┌────────────────────────┐
            │   Paiement (autre BC)  │
            └────────────────────────┘
```

---

## Agrégat 2 — Paiement

### Racine d'agrégat
`Paiement` — Coordonne la transaction financière associée à une réservation. C'est l'unique point d'entrée pour modifier le statut du paiement et publier les événements de domaine vers les autres contextes.

### Frontières
**Inclus dans l'agrégat (cohérence forte) :**
- `Montant` débité
- `StatutPaiement` (PENDING / SUCCESS / FAILED / REFUNDED)
- `TransactionId` (objet valeur — identifiant Stripe)
- Horodatages `initie_le` et `traite_le`
- Référence vers le `ReservationId` associé

**Exclus de l'agrégat :**
- Les détails de la `Réservation` (autre agrégat, autre BC)
- Les données bancaires sensibles (jamais persistées — Stripe est PCI-DSS)
- Les remboursements ultérieurs (modélisés comme une nouvelle entité `Remboursement` liée par référence)

### Invariants métier (≥3)

| Invariant | Description métier (3–4 phrases) | Conséquence si non respecté |
|-----------|-----------------------------------|------------------------------|
| **INV-P1 — Montant exact requis** | Le montant du paiement doit correspondre exactement au montant total de la réservation associée, au centime près. Tout écart (paiement partiel ou sur-paiement) est rejeté à la création. Cette règle évite les incohérences comptables et les contestations clients. | Litiges financiers, incohérences avec la réservation, perte de revenus, problèmes de réconciliation comptable. |
| **INV-P2 — Unicité du paiement réussi par réservation** | Une réservation ne peut être associée qu'à un seul paiement avec statut SUCCESS. Toute tentative de créer un second paiement réussi pour la même réservation est rejetée par l'agrégat et le repository. | Double facturation du client, fraude, problème comptable critique, atteinte à la réputation. |
| **INV-P3 — Immuabilité du statut final (SUCCESS / FAILED)** | Une fois un paiement passé au statut SUCCESS ou FAILED, ce statut ne peut plus jamais être modifié. Un retraitement nécessite obligatoirement la création d'un nouveau paiement avec un nouvel identifiant. Cette règle garantit l'auditabilité et la traçabilité financière exigée par la comptabilité. | Risque de fraude par modification a posteriori, perte d'auditabilité, non-conformité réglementaire (PCI-DSS, comptabilité). |
| **INV-P4 — Idempotence des webhooks** | Un même événement `payment_intent.succeeded` reçu plusieurs fois de Stripe (pour cause de retry) ne doit produire qu'une seule transition d'état. La clé `event_id` est utilisée pour déduplicaer. | Doubles transitions d'état, événements `PaiementValidé` émis plusieurs fois, confirmations en double dans Réservations. |

### Cycle de vie de l'agrégat

```
   [Réservations publie PaiementRequis]
              │
              ▼
     ┌──────────────────┐
     │     PENDING      │
     └────────┬─────────┘
        │              │
        │ Stripe OK    │ Stripe KO
        ▼              ▼
     SUCCESS        FAILED
     (immuable)    (immuable)
        │
        │ remboursement → nouvelle entité Remboursement liée
        ▼
    REFUNDED (statut secondaire — n'altère pas SUCCESS)
```

### Schéma UML conceptuel — Frontière de l'agrégat Paiement

```
╔════════════════════════════════════════════════════════════╗
║                AGRÉGAT « Paiement »                        ║
║                                                              ║
║       ┌────────────────────────────────────┐                ║
║       │   Paiement  (RACINE)               │                ║
║       │────────────────────────────────────│                ║
║       │  payment_id     : PaymentId        │                ║
║       │  reservation_id : ReservationId    │                ║
║       │  montant        : Montant          │                ║
║       │  statut         : StatutPaiement   │                ║
║       │  transaction_id : TransactionId    │                ║
║       │  initie_le      : Horodatage       │                ║
║       │  traite_le      : Horodatage?      │                ║
║       └────────────────────────────────────┘                ║
║              │                  │                            ║
║              ▼  composé de      ▼  composé de                ║
║   ┌────────────────────┐  ┌────────────────────┐            ║
║   │   Montant (VO)     │  │ StatutPaiement (VO)│            ║
║   │   euros: Decimal   │  │ ENUM 4 valeurs     │            ║
║   └────────────────────┘  └────────────────────┘            ║
║                                                              ║
║   Invariants gardés par la racine :                          ║
║   • INV-P1 : montant == reservation.montant_total            ║
║   • INV-P2 : pas d'autre Paiement SUCCESS pour la même résa  ║
║   • INV-P3 : statut SUCCESS / FAILED non modifiable          ║
║   • INV-P4 : idempotence par event_id Stripe                 ║
╚════════════════════════════════════════════════════════════╝
```

---

## Schéma UML global des agrégats et de leurs interactions

```
╔════════════════════════════════════════════════════════════════════╗
║                    BILLETTERIE — VUE AGRÉGATS                       ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║   ┌──────────────────────────┐         ┌──────────────────────────┐║
║   │   AGRÉGAT Réservation    │         │    AGRÉGAT Paiement      │║
║   │   (Core — ContexteRésa)  │◄────────│  (Generic — ContextePay) │║
║   │                          │  réf    │                          │║
║   │   - reservation_id       │  par id │   - payment_id           │║
║   │   - statut               │         │   - reservation_id ──────┘║
║   │   - List<SeatId> (1..10) │         │   - montant              ║
║   │   - montant_total        │         │   - statut               ║
║   │   - expire_le            │         │   - transaction_id       ║
║   │                          │         │                          ║
║   │  INV-R1, R2, R3, R4      │         │   INV-P1, P2, P3, P4     ║
║   └──────────────────────────┘         └──────────────────────────┘║
║              │                                     ▲                ║
║              │ Pub: PaiementRequis                 │                ║
║              └─────────────────────────────────────┘                ║
║              ▲                                     │                ║
║              │ Sub: PaiementValidé/Échoué          │                ║
║              └─────────────────────────────────────┘                ║
║                                                                     ║
║   ┌──────────────────────────────────────────────────────────────┐ ║
║   │   AGRÉGAT externe : Séance (ContexteCatalogue, Supporting)   │ ║
║   │   Référencée par seance_id depuis Réservation (ACL)          │ ║
║   └──────────────────────────────────────────────────────────────┘ ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## Récapitulatif des invariants

| # | Invariant | Agrégat | Type de garantie |
|---|-----------|---------|-------------------|
| INV-R1 | Max 10 places | Réservation | Garantie locale (taille de la collection) |
| INV-R2 | Confirmation avant expiration | Réservation | Garantie temporelle |
| INV-R3 | Immuabilité après confirmation | Réservation | Garantie d'état terminal |
| INV-R4 | Unicité (place, séance) | Réservation + Repository | Garantie de cohérence inter-agrégats |
| INV-P1 | Montant exact | Paiement | Garantie de cohérence avec Réservation |
| INV-P2 | Unicité du paiement réussi | Paiement + Repository | Garantie d'unicité |
| INV-P3 | Statut final immuable | Paiement | Garantie d'auditabilité |
| INV-P4 | Idempotence des webhooks | Paiement | Garantie d'idempotence |

> Tous ces invariants sont validés par les scénarios Given/When/Then dans `tests-domaine.md`.
