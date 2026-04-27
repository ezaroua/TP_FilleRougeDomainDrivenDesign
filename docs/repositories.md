# Repositories — Interfaces Conceptuelles

> Chapitre 4 — Livrable 2 : Définition conceptuelle des interfaces de repository.
> **Aucun code** — description sous forme de tableaux et narrations métier.

---

## Qu'est-ce qu'un Repository ?

Un Repository est une **abstraction de persistance** définie par la couche Application. Il représente un contrat (port) que l'infrastructure devra implémenter. Du point de vue du domaine, un Repository se comporte comme une collection en mémoire d'agrégats — on n'a pas à savoir si les données viennent d'une base SQL, d'un cache Redis ou d'un appel HTTP.

---

## Repository 1 : IReservationRepository

### Responsabilités
Permettre la persistance, la récupération et la gestion du cycle de vie des agrégats **Réservation**. Ce repository est le seul point d'accès aux données de réservation pour la couche Application du contexte Réservations.

### Opérations métier

| Opération métier | Description | Contraintes / règles métier |
|-----------------|-------------|----------------------------|
| `sauvegarder(reservation)` | Persiste une nouvelle réservation ou met à jour une réservation existante. Toute modification de l'agrégat Réservation (ajout de place, changement de statut) doit transiter par cette opération. | L'identifiant de réservation doit être unique. Une réservation ANNULÉE ne peut pas être sauvegardée avec le statut CONFIRMÉE (transition invalide). |
| `trouverParId(reservation_id)` | Récupère une réservation à partir de son identifiant unique. Retourne une réservation avec l'ensemble de ses données (places, statut, montant, expiration). | Si la réservation n'existe pas, retourner une erreur métier "Réservation introuvable". Ne jamais retourner un objet incomplet. |
| `trouverParClient(client_id)` | Récupère l'historique des réservations d'un client, triées par date décroissante. Utilisé pour l'affichage du compte client et la détection de doublons. | Inclure toutes les réservations (tous statuts). Le client doit exister dans le système. |
| `trouverRéservationsExpirées()` | Retourne toutes les réservations EN_ATTENTE dont l'`expires_at` est dépassé. Utilisé par la tâche planifiée d'expiration automatique. | Critère : statut = EN_ATTENTE ET expires_at < maintenant. Résultat trié par date d'expiration (les plus anciennes en premier). |
| `trouverPlacesRéservées(seance_id)` | Retourne la liste des identifiants de places occupées (statut CONFIRMÉE ou EN_ATTENTE) pour une séance donnée. Permet de calculer la disponibilité en temps réel. | Inclure uniquement les réservations actives (pas les ANNULÉES). Résultat critique pour éviter les doubles-réservations. |

---

## Repository 2 : IPaymentRepository

### Responsabilités
Permettre la persistance et la récupération des agrégats **Paiement**. Garantit l'unicité des paiements par réservation et maintient la traçabilité financière complète.

### Opérations métier

| Opération métier | Description | Contraintes / règles métier |
|-----------------|-------------|----------------------------|
| `sauvegarder(paiement)` | Persiste un paiement nouveau ou met à jour son statut. Toute transition de statut (PENDING → SUCCESS/FAILED) doit être persistée immédiatement pour garantir la traçabilité. | Un paiement avec statut SUCCESS ou FAILED ne peut pas être sauvegardé avec un statut différent (immuabilité du statut final). La transaction_id doit être unique si elle est renseignée. |
| `trouverParId(payment_id)` | Récupère un paiement à partir de son identifiant unique. Utilisé pour les opérations de remboursement et la réconciliation. | Si le paiement n'existe pas, retourner une erreur métier "Paiement introuvable". |
| `trouverParRéservation(reservation_id)` | Vérifie si une réservation possède déjà un paiement réussi. Utilisé pour garantir l'invariant INV-P2 (unicité du paiement). | Retourner au maximum 1 paiement avec statut SUCCESS. Si plusieurs paiements FAILED existent pour la même réservation, tous les retourner (pour audit). |
| `trouverParTransaction(transaction_id)` | Retrouve un paiement à partir de l'identifiant de transaction Stripe. Utilisé lors de la réception des webhooks Stripe pour mettre à jour le statut. | La transaction_id est unique dans le système. Utilisé pour garantir l'idempotence des webhooks. |
| `trouverPaiementsDuJour(date)` | Récupère tous les paiements SUCCESS d'une journée donnée. Utilisé pour la réconciliation comptable quotidienne. | Date au format YYYY-MM-DD. Inclure uniquement les paiements SUCCESS. Résultat trié par heure de traitement. |

---

## Repository 3 : ISeanceRepository (Catalogue Context)

### Responsabilités
Permettre la lecture des informations de séances depuis le contexte Catalogue. Ce repository est utilisé via l'Anti-Corruption Layer par le contexte Réservations.

### Opérations métier

| Opération métier | Description | Contraintes / règles métier |
|-----------------|-------------|----------------------------|
| `trouverParId(seance_id)` | Récupère les informations essentielles d'une séance (film, salle, horaire, capacité, tarif). | Retourner uniquement les informations nécessaires au contexte Réservations (pas les métadonnées complètes du film). En cas d'indisponibilité du Catalogue, une version en cache peut être utilisée. |
| `trouverSéancesDisponibles(date, film_id?)` | Liste les séances futures avec des places encore disponibles. Filtrage optionnel par film. | Ne retourner que les séances futures (heure_debut > maintenant). Séances annulées exclues. |

---

## Schéma des dépendances entre repositories

```
┌────────────────────────────────────┐
│       Application Layer            │
│                                    │
│  CréerRéservation ──────────────►  IReservationRepository
│  ConfirmerPaiement ─────────────►  IPaymentRepository
│  CréerRéservation ──────────────►  ISeanceRepository (via ACL)
│                                    │
└────────────────────────────────────┘
         │                  │
         ▼                  ▼
┌─────────────────┐  ┌─────────────────────┐
│  PostgreSQL     │  │  CatalogueHTTP      │
│  Adapter        │  │  Adapter (ACL)      │
│  (implements    │  │  (implements        │
│  Reservation +  │  │  ISeanceRepository) │
│  Payment repos) │  └─────────────────────┘
└─────────────────┘
```
