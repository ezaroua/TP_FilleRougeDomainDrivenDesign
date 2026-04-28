# Concepts de Domaine — Billetterie Cinéma

> Chapitre 2 — Livrable 4 : Formalisation des éléments métier clés alignés avec les Bounded Contexts.
> **Aucun code** — description purement conceptuelle.

---

## Entité 1 : Réservation (Contexte : Réservations)

### Description métier
La Réservation représente l'engagement d'un client sur un ensemble de places pour une séance donnée. Elle est identifiée de manière unique par un identifiant de réservation et traverse plusieurs états au cours de son cycle de vie : en attente de paiement, confirmée, ou annulée. Son existence est temporellement limitée : si aucun paiement n'intervient dans les 15 minutes suivant sa création, elle est automatiquement annulée et les places sont libérées.

### Attributs métier

| Attribut | Type métier | Description |
|----------|-------------|-------------|
| `reservation_id` | Identifiant (UUID) | Clé unique immuable de la réservation |
| `client_id` | Référence Client | Identifiant du client à l'origine de la réservation |
| `seance_id` | Référence Séance | Séance pour laquelle les places sont réservées |
| `places` | Liste de SeatId | Références vers les places sélectionnées |
| `statut` | Énumération | EN_ATTENTE / CONFIRMÉE / ANNULÉE |
| `cree_le` | Horodatage | Date et heure de création de la réservation |
| `expire_le` | Horodatage | Délai d'expiration (cree_le + 15 min) |
| `montant_total` | Montant (Money) | Somme des tarifs des places sélectionnées |

### Invariant métier principal
> Une réservation ne peut pas être confirmée si son délai d'expiration est dépassé.
> Une réservation confirmée ne peut plus voir ses places modifiées.
> Le nombre de places par réservation est limité à 10 (règle anti-monopole).

---

## Entité 2 : Séance (Contexte : Catalogue)

### Description métier
La Séance représente une instance de projection d'un film à une date et heure précises dans une salle déterminée. Elle est l'élément central autour duquel s'organisent les réservations. Le Catalogue est responsable de sa création, de sa planification et de sa diffusion vers les autres contextes. La Séance définit la capacité maximale disponible (nombre de places dans la salle) et l'horaire de la projection.

### Attributs métier

| Attribut | Type métier | Description |
|----------|-------------|-------------|
| `seance_id` | Identifiant (UUID) | Clé unique immuable de la séance |
| `film_id` | Référence Film | Film projeté lors de cette séance |
| `salle_id` | Référence Salle | Salle dans laquelle se tient la séance |
| `heure_debut` | Horodatage | Heure de début de la projection |
| `heure_fin` | Horodatage | Heure de fin calculée (début + durée film) |
| `capacite` | Entier | Nombre total de places disponibles dans la salle |
| `tarif_base` | Montant (Money) | Prix de base de la place pour cette séance |

### Invariant métier principal
> Une séance ne peut pas être planifiée dans une salle déjà occupée sur le même créneau horaire.
> Une séance ne peut pas démarrer si une autre séance se termine moins de 20 minutes avant (temps de nettoyage).

---

## Objet Valeur : Montant (Money)

### Description métier
Le Montant représente une valeur monétaire exprimée en euros, avec une précision de deux décimales. Il est utilisé pour exprimer le prix d'une place, le total d'une réservation ou le montant d'une transaction. Un Montant est immuable : on ne modifie pas un montant existant, on en crée un nouveau.

### Propriétés

| Propriété | Type | Contrainte |
|-----------|------|-----------|
| `euros` | Décimal | Valeur positive ou nulle, 2 décimales max |

### Justification de l'immuabilité
Un Montant n'a pas d'identité propre : deux montants de `11,50€` sont parfaitement interchangeables. Modifier un Montant n'aurait pas de sens métier — si un tarif change, on ne "modifie" pas l'ancien montant, on remplace l'objet par un nouveau. Cette immuabilité garantit la cohérence des calculs financiers : le montant_total d'une réservation ne change pas une fois calculé, car il est basé sur des Montants figés au moment de la réservation. Toute opération (addition, comparaison) retourne un nouveau Montant.

### Exemples d'opérations conceptuelles
- `Montant(11.50) + Montant(8.00)` → `Montant(19.50)` (nouveau objet)
- `Montant(11.50) == Montant(11.50)` → `true` (égalité par valeur)
- `Montant(-5.00)` → invalide (le montant doit être positif)

---

## Récapitulatif des concepts clés par contexte

| Concept | Type DDD | Contexte | Rôle |
|---------|----------|----------|------|
| Réservation | Entité (Racine d'agrégat) | Réservations | Coordonne places, statut, paiement |
| Séance | Entité (Racine d'agrégat) | Catalogue | Définit le cadre de la projection |
| Paiement | Entité (Racine d'agrégat) | Paiements | Gère la transaction financière |
| Montant | Objet Valeur | Paiements, Réservations | Valeur monétaire immuable |
| SeatNumber | Objet Valeur | Réservations | Coordonnées rang/siège immuables |
| ClientId | Objet Valeur | Réservations, Paiements | Référence client opaque et immuable |
| TransactionId | Objet Valeur | Paiements | Identifiant bancaire externe immuable |
