# Ubiquitous Language — Billetterie Cinéma (v2)

## Glossaire métier enrichi par contexte (≥25 termes)

| Terme | Contexte | Définition | Exemple |
|-------|----------|------------|---------|
| **Séance** | Catalogue, Réservations | Projection d'un film à une date/heure précises dans une salle donnée | "Séance #S123 : Avatar 2, 20h15, Salle 3" |
| **Place** | Réservations | Siège numéroté avec état (libre/bloquée/réservée/occupée) | "Place F12 (Rang F, Siège 12) - statut: libre" |
| **Réservation** | Réservations, Paiements | Engagement sur des places avec statut de cycle de vie | "Réservation #RES-456 : 3 places, statut: confirmée" |
| **Blocage** | Réservations | Verrouillage temporaire de places (15min) avant confirmation | "Blocage actif jusqu'à 19h45" |
| **Billet** | Réservations | Titre d'entrée validant l'accès à une séance | "Billet e-ticket #BIL-789 avec QR code" |
| **Salle** | Catalogue | Espace de projection avec capacité et configuration | "Salle 1 : 200 places, écran IMAX" |
| **Transaction** | Paiements | Opération financière avec statut (pending/success/failed) | "Transaction #TXN-321 : 34,50€, statut: success" |
| **Montant** | Paiements | Valeur monétaire en euros (2 décimales) | "Montant: 34,50€" |
| **Remboursement** | Paiements | Restitution partielle/totale d'un paiement validé | "Remboursement de 23,00€ traité" |
| **Facture** | Paiements | Document fiscal émis après transaction réussie | "Facture #FAC-555 du 15/02/2026" |
| **Film** | Catalogue | Œuvre cinématographique avec métadonnées | "Film : Dune 2, durée 166min, PG-13" |
| **Programmation** | Catalogue | Planning des séances sur une période | "Programmation semaine 12 : 45 séances" |
| **Tarif** | Paiements, Réservations | Prix selon catégorie (plein/réduit/abonné) | "Tarif plein : 11,50€, réduit : 8,00€" |
| **Client** | Réservations, Paiements | Utilisateur final réservant/achetant des places | "Client #CLI-123, membre depuis 2024" |
| **Caissier** | Réservations | Employé gérant les ventes sur place | "Caissier poste 2" |
| **Gestionnaire** | Catalogue | Administrateur gérant films et programmation | "Gestionnaire multi-salles" |
| **Disponibilité** | Réservations | Nombre de places libres pour une séance | "43/150 places disponibles" |
| **Configuration** | Catalogue | Disposition physique des sièges dans une salle | "Configuration : 12 rangs × 18 sièges" |
| **QR Code** | Réservations | Code-barres 2D sur le billet électronique | "QR: eyJhbGc...XY123" |
| **Validation** | Réservations | Contrôle du billet à l'entrée via scan | "Validation à 19h58 - accès autorisé" |
| **Notification** | Réservations, Paiements | Message automatique envoyé au client | "Email de confirmation envoyé à 19h30" |
| **Horaire** | Catalogue | Créneau de diffusion d'une séance | "Horaire : 20h15 - 22h21" |
| **Capacité** | Catalogue, Réservations | Nombre total de places dans une salle | "Capacité : 150 places" |
| **Annulation** | Réservations, Paiements | Action de libérer une réservation avec/sans remboursement | "Annulation avec remboursement (-2h avant séance)" |
| **Réconciliation** | Paiements | Vérification de cohérence paiement ↔ réservation | "Réconciliation quotidienne OK" |
| **Métadonnées** | Catalogue | Informations descriptives du film | "Réalisateur : Denis Villeneuve, genre : Sci-Fi" |
| **Attribution** | Réservations | Assignation définitive d'une place à un client | "Attribution place F12 → Client #CLI-123" |
| **Timeout** | Réservations | Délai avant libération automatique d'un blocage | "Timeout réservation : 15 minutes" |
| **Idempotence** | Paiements | Garantie qu'une transaction n'est traitée qu'une fois | "Clé idempotence : idem_RES-456_retry3" |

## Notes de cohérence

- **Contexte Réservations** : Focus sur les statuts et cycles de vie des places
- **Contexte Paiements** : Vocabulaire financier strict (Transaction, pas "Achat")
- **Contexte Catalogue** : Termes descriptifs et informationnels
- **Termes partagés** : Séance, Tarif (avec définitions légèrement adaptées par contexte)