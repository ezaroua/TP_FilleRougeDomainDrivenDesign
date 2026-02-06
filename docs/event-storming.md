# Event Storming — Billetterie Cinéma

## Événements métier (≥10 requis)

| # | Événement | Description | Acteur déclencheur |
|---|-----------|-------------|-------------------|
| 1 | **FilmAjoutéAuCatalogue** | Un nouveau film est ajouté au catalogue | Gestionnaire |
| 2 | **SéancePlanifiée** | Une séance est créée avec date, heure, salle, film | Gestionnaire |
| 3 | **RéservationInitiée** | Un client démarre le processus de réservation | Client |
| 4 | **PlacesSélectionnées** | Le client choisit ses places dans la salle | Client |
| 5 | **RéservationConfirmée** | La réservation est confirmée après sélection | Système |
| 6 | **PaiementValidé** | Le paiement est accepté et enregistré | Système bancaire |
| 7 | **BilletÉmis** | Le billet est généré et envoyé au client | Système |
| 8 | **RéservationAnnulée** | Une réservation est annulée par le client ou le système | Client/Système |
| 9 | **PlaceLibérée** | Une place redevient disponible suite à annulation | Système |
| 10 | **BilletValidé** | Le billet est scanné et validé à l'entrée | Caissier |
| 11 | **SéanceComplète** | Toutes les places d'une séance sont réservées | Système |
| 12 | **RemboursementEffectué** | Un remboursement est traité pour une annulation | Système |

## Commandes (≥5 requis)

| # | Commande | Description | Acteur émetteur |
|---|----------|-------------|----------------|
| 1 | **AjouterFilm** | Ajouter un nouveau film au catalogue | Gestionnaire |
| 2 | **PlanifierSéance** | Créer une séance pour un film donné | Gestionnaire |
| 3 | **RéserverPlaces** | Réserver des places pour une séance | Client/Caissier |
| 4 | **EffectuerPaiement** | Procéder au paiement de la réservation | Client |
| 5 | **AnnulerRéservation** | Annuler une réservation existante | Client |
| 6 | **ValiderBillet** | Scanner et valider un billet à l'entrée | Caissier |

## Acteurs impliqués

- **Client** : Réserve, paie, annule
- **Caissier** : Valide billets, aide à la réservation sur place
- **Gestionnaire** : Configure séances, films, salles
- **Système** : Gère automatiquement les places, notifications, validations
- **Système bancaire** (externe) : Traite les paiements

## Flux principal

1. Gestionnaire → **PlanifierSéance** → SéancePlanifiée
2. Client → **RéserverPlaces** → PlacesSélectionnées → RéservationConfirmée
3. Client → **EffectuerPaiement** → PaiementValidé → BilletÉmis
4. Caissier → **ValiderBillet** → BilletValidé