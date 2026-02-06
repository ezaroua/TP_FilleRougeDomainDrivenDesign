# Bounded Contexts — Billetterie Cinéma

## 1. Réservations Context (Core Domain)

### Description
Gère le cycle de vie complet des réservations : sélection de places, blocage temporaire, confirmation et annulation. C'est le cœur métier différenciant qui implémente les règles complexes de disponibilité temps-réel et de cohérence des réservations concurrentes.

### Limites
- **Inclut** : Gestion des places (statuts libre/réservée/occupée), règles de réservation (timeout, places adjacentes), contraintes d'intégrité des sièges
- **Exclut** : Le traitement financier (délégué à Paiements), les détails du film (fournis par Catalogue), l'impression physique des billets

### Ubiquitous Language spécifique
1. **Réservation** : Engagement sur des places avec statut (en-cours/confirmée/annulée)
2. **Place** : Siège identifié par rang/numéro avec état de disponibilité
3. **Blocage** : Verrouillage temporaire de places (15min timeout)
4. **Séance** : Instance de projection avec capacité et horaire fixe
5. **Attribution** : Assignation définitive d'une place à un client

### Responsabilités
- Vérifier la disponibilité des places en temps réel
- Appliquer le timeout de réservation (libération automatique)
- Garantir l'absence de double-réservation
- Émettre les événements : PlacesRéservées, RéservationConfirmée, PlacesLibérées

---

## 2. Paiements Context (Generic Domain)

### Description
Orchestre les transactions financières via un prestataire externe (Stripe/PayPal). Assure la traçabilité des paiements, remboursements et réconciliation avec les réservations sans exposer les détails bancaires.

### Limites
- **Inclut** : Gestion des transactions, réconciliation, remboursements, génération de factures
- **Exclut** : Le traitement bancaire réel (API externe), la logique de réservation, la génération de billets

### Ubiquitous Language spécifique
1. **Transaction** : Opération financière identifiée avec statut (pending/success/failed)
2. **Montant** : Valeur monétaire en euros avec 2 décimales
3. **Remboursement** : Restitution partielle ou totale d'un paiement
4. **Facture** : Document fiscal associé à une transaction réussie
5. **Réconciliation** : Vérification de cohérence paiement ↔ réservation

### Responsabilités
- Valider les montants et méthodes de paiement
- Communiquer avec le prestataire bancaire (Anti-Corruption Layer)
- Émettre les événements : PaiementValidé, PaiementÉchoué, RemboursementEffectué
- Garantir l'idempotence des transactions

---

## 3. Catalogue Context (Supporting Domain)

### Description
Maintient le référentiel des films avec métadonnées (titre, durée, genre, affiche) et gère la programmation des séances. Fournit les informations de consultation pour les autres contexts sans gérer la disponibilité des places.

### Limites
- **Inclut** : CRUD des films, planification des séances, configuration des salles, métadonnées (affiches, synopsis)
- **Exclut** : La disponibilité des places (Réservations), le processus de vente, les statistiques de fréquentation

### Ubiquitous Language spécifique
1. **Film** : Œuvre cinématographique avec titre, durée, classification
2. **Programmation** : Planning des séances sur une période donnée
3. **Salle** : Espace physique avec capacité et configuration de sièges
4. **Horaire** : Créneau de diffusion d'une séance
5. **Métadonnées** : Informations descriptives du film (synopsis, réalisateur, bande-annonce)

### Responsabilités
- Gérer le catalogue de films actifs
- Planifier les séances en évitant les conflits
- Fournir les informations de consultation (API read-only pour autres contexts)
- Émettre les événements : FilmAjouté, SéancePlanifiée, SéanceAnnulée