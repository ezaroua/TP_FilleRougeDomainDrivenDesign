# Bounded Contexts

## Tableau récapitulatif

| Bounded Context | Type | Rôle / Responsabilité principale |
|-----------------|------|----------------------------------|
| **ContexteRéservation** | Core | Gère le cycle de vie complet des réservations : sélection de places, blocage temporaire, confirmation et annulation. C'est le cœur métier différenciant qui implémente les règles complexes de disponibilité temps-réel et de cohérence des réservations concurrentes. Garantit l'absence de double-réservation et applique le timeout de libération automatique des places. |
| **ContextePaiement** | Generic | Orchestre les transactions financières via un prestataire externe (Stripe/PayPal). Assure la traçabilité des paiements, remboursements et réconciliation avec les réservations sans exposer les détails bancaires. Garantit l'idempotence des transactions et émet les événements de confirmation ou d'échec vers les autres contextes. |
| **ContexteCatalogue** | Supporting | Maintient le référentiel des films avec leurs métadonnées (titre, durée, genre, affiche) et gère la programmation des séances. Fournit les informations de consultation en lecture seule pour les autres contextes sans gérer la disponibilité des places ni le processus de vente. |

---

## Détail des Bounded Contexts

### 1. ContexteRéservation (Core Domain)

**Description**
Gère le cycle de vie complet des réservations : sélection de places, blocage temporaire, confirmation et annulation. C'est le cœur métier différenciant qui implémente les règles complexes de disponibilité temps-réel et de cohérence des réservations concurrentes.

**Limites**
- **Inclut** : Gestion des places (statuts libre/réservée/occupée), règles de réservation (timeout, places adjacentes), contraintes d'intégrité des sièges
- **Exclut** : Le traitement financier (délégué à ContextePaiement), les détails du film (fournis par ContexteCatalogue), l'impression physique des billets

**Responsabilités**
- Vérifier la disponibilité des places en temps réel
- Appliquer le timeout de réservation (libération automatique)
- Garantir l'absence de double-réservation
- Émettre les événements : PlacesRéservées, RéservationConfirmée, PlacesLibérées

---

### 2. ContextePaiement (Generic Domain)

**Description**
Orchestre les transactions financières via un prestataire externe (Stripe/PayPal). Assure la traçabilité des paiements, remboursements et réconciliation avec les réservations sans exposer les détails bancaires.

**Limites**
- **Inclut** : Gestion des transactions, réconciliation, remboursements, génération de factures
- **Exclut** : Le traitement bancaire réel (API externe), la logique de réservation, la génération de billets

**Responsabilités**
- Valider les montants et méthodes de paiement
- Communiquer avec le prestataire bancaire (Anti-Corruption Layer)
- Émettre les événements : PaiementValidé, PaiementÉchoué, RemboursementEffectué
- Garantir l'idempotence des transactions

---

### 3. ContexteCatalogue (Supporting Domain)

**Description**
Maintient le référentiel des films avec métadonnées (titre, durée, genre, affiche) et gère la programmation des séances. Fournit les informations de consultation pour les autres contextes sans gérer la disponibilité des places.

**Limites**
- **Inclut** : CRUD des films, planification des séances, configuration des salles, métadonnées (affiches, synopsis)
- **Exclut** : La disponibilité des places (ContexteRéservation), le processus de vente, les statistiques de fréquentation

**Responsabilités**
- Gérer le catalogue de films actifs
- Planifier les séances en évitant les conflits
- Fournir les informations de consultation (API read-only pour autres contextes)
- Émettre les événements : FilmAjouté, SéancePlanifiée, SéanceAnnulée