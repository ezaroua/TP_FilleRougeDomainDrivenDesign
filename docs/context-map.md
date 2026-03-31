# Context Map

## Schéma général

```
┌──────────────────┐
│    CATALOGUE     │ (Upstream)
│   (Supporting)   │
└────────┬─────────┘
         │ Customer/Supplier (Client/Fournisseur)
         │ (SéancePlanifiée)
         ▼
    ┌─────────────────────┐
    │   RÉSERVATIONS      │ (Core)
    │  ◄── ACL            │
    │  (Couche Anti-Corr.)│
    └──────┬──────────────┘
           │
           │ Partnership (Partenariat)
           │ (bidirectionnel)
           │
    ┌──────▼──────────────┐
    │    PAIEMENTS        │ (Generic)
    └──────┬──────────────┘
           │ Conformist (Conformiste)
           ▼
    ┌─────────────────────┐
    │   Stripe API        │ (Externe)
    │   (Prestataire)     │
    └─────────────────────┘
```

---

## Relations et patterns

| Contexte source | Contexte cible | Pattern de relation | Justification |
|-----------------|----------------|---------------------|---------------|
| **ContexteRéservation** | **ContextePaiement** | Partnership (Partenariat) | Collaboration étroite et bidirectionnelle : une réservation déclenche un paiement, et la validation du paiement confirme la réservation. Les deux contextes doivent rester synchronisés pour garantir qu'aucune réservation confirmée n'est impayée et qu'aucun paiement orphelin n'existe. Le succès des deux est mutuellement requis. |
| **ContexteRéservation** | **ContexteCatalogue** | Anti-Corruption Layer (Couche Anti-Corruption) | ContexteRéservation consomme les données du Catalogue (film, séance, salle) via une couche d'adaptation qui traduit le modèle riche du Catalogue vers les besoins minimaux de Réservation. Cela protège le modèle interne de Réservation des changements dans Catalogue et évite la pollution du modèle métier avec des données non pertinentes. |
| **ContexteCatalogue** | **ContexteRéservation** | Customer/Supplier (Client/Fournisseur) | Catalogue est upstream : il publie des événements (SéancePlanifiée) que Réservations consomme pour initialiser les disponibilités des places. Catalogue définit les séances de manière autoritaire et Réservations dépend de ces informations pour créer son état initial. |
| **ContextePaiement** | **Stripe API (externe)** | Conformist (Conformiste) | Stripe impose son propre modèle (PaymentIntent, charges, webhooks). ContextePaiement doit s'y conformer strictement sans possibilité de négociation. Aucune adaptation du modèle externe n'est possible, le contexte s'aligne intégralement sur le prestataire. |

---

## Intégrations techniques envisagées

### Intégration 1 — API REST entre ContexteRéservation et ContextePaiement
- **Type** : API REST synchrone
- **BCs impliqués** : ContexteRéservation (appelant) → ContextePaiement (fournisseur)
- **Cas d'usage** : Lorsqu'un client valide son panier, ContexteRéservation appelle l'endpoint de ContextePaiement pour initier une transaction. ContextePaiement répond avec le statut de la transaction (succès ou échec), ce qui permet à ContexteRéservation de confirmer ou d'annuler la réservation.

### Intégration 2 — Événements via broker entre ContexteCatalogue et ContexteRéservation
- **Type** : Événements asynchrones via message broker (ex : RabbitMQ ou Kafka)
- **BCs impliqués** : ContexteCatalogue (producteur) → ContexteRéservation (consommateur)
- **Cas d'usage** : Lorsqu'une nouvelle séance est planifiée dans le Catalogue, un événement `SéancePlanifiée` est publié sur le broker. ContexteRéservation consomme cet événement pour initialiser automatiquement la liste des places disponibles pour cette séance.

### Intégration 3 — Événements asynchrones entre ContextePaiement et ContexteRéservation
- **Type** : Événements asynchrones via message broker
- **BCs impliqués** : ContextePaiement (producteur) → ContexteRéservation (consommateur)
- **Cas d'usage** : Une fois la transaction bancaire traitée par Stripe, ContextePaiement publie un événement `PaiementValidé` ou `PaiementÉchoué`. ContexteRéservation consomme cet événement pour finaliser la confirmation de la réservation ou libérer les places bloquées.

---

## Matrice de dépendances

| Contexte | Dépend de | Type de dépendance |
|----------|-----------|--------------------|
| ContexteRéservation | ContexteCatalogue | Données via Anti-Corruption Layer (Couche Anti-Corruption) |
| ContexteRéservation | ContextePaiement | Collaboration — Partnership (Partenariat) |
| ContextePaiement | Stripe API | Conformist (Conformiste) |
| ContexteCatalogue | — | Autonome |