# Context Map — Relations entre Bounded Contexts

## Relations identifiées

| Relation | Contexts | Direction | Justification |
|----------|----------|-----------|---------------|
| **Partnership** | Réservations ↔ Paiements | Bidirectionnelle | Collaboration étroite : une réservation déclenche un paiement, la validation du paiement confirme la réservation. Succès mutuel requis. |
| **Anti-Corruption Layer (ACL)** | Réservations → Catalogue | Unidirectionnelle | Réservations consomme les données du Catalogue (film, séance, salle) via une couche d'adaptation pour protéger son modèle interne. |
| **Conformist** | Paiements → Stripe API (externe) | Unidirectionnelle | Paiements se conforme strictement au modèle imposé par l'API bancaire externe sans négociation possible. |
| **Customer/Supplier** | Catalogue → Réservations | Unidirectionnelle (upstream/downstream) | Catalogue est upstream : il publie des événements (SéancePlanifiée) que Réservations consomme pour initialiser les disponibilités. |

## Schéma des relations
```
┌──────────────────┐
│    CATALOGUE     │ (Upstream)
│   (Supporting)   │
└────────┬─────────┘
         │ Customer/Supplier
         │ (SéancePlanifiée)
         ▼
    ┌─────────────────────┐
    │   RÉSERVATIONS      │ (Core)
    │    ◄──── ACL        │
    └──────┬──────────────┘
           │
           │ Partnership
           │ (bidirectionnel)
           │
    ┌──────▼──────────────┐
    │    PAIEMENTS        │ (Generic)
    └──────┬──────────────┘
           │ Conformist
           ▼
    ┌─────────────────────┐
    │   Stripe API        │ (Externe)
    │   (Prestataire)     │
    └─────────────────────┘
```

## Détails des relations

### 1. Partnership : Réservations ↔ Paiements

**Nature de la collaboration :**
- **Réservations → Paiements** : Envoie une commande de paiement avec montant total
- **Paiements → Réservations** : Notifie le succès/échec pour confirmation finale

**Contrat d'échange :**
```json
// Réservations → Paiements
{
  "reservation_id": "RES-123",
  "montant_total": 34.50,
  "client_id": "CLI-456"
}

// Paiements → Réservations
{
  "transaction_id": "TXN-789",
  "reservation_id": "RES-123",
  "statut": "success"
}
```

**Justification :** Les deux contexts doivent rester synchronisés pour garantir qu'aucune réservation confirmée n'est impayée, et aucun paiement orphelin n'existe.

---

### 2. Anti-Corruption Layer : Réservations → Catalogue

**Problématique :**
Le Catalogue expose un modèle riche (Film avec multiples attributs) mais Réservations n'a besoin que d'informations minimales (ID séance, heure, salle).

**Solution ACL :**
```python
# adapters/catalogue_adapter.py
class CatalogueAdapter:
    def get_seance_info(self, seance_id: str) -> SeanceInfo:
        # Appel API Catalogue
        raw_data = catalogue_api.get_seance(seance_id)
        # Transformation vers modèle Réservations
        return SeanceInfo(
            seance_id=raw_data["id"],
            heure_debut=raw_data["horaire"]["debut"],
            salle_id=raw_data["salle"]["id"]
        )
```

**Justification :** Protège Réservations des changements dans Catalogue et évite la pollution du modèle métier avec des données non pertinentes.

---

### 3. Conformist : Paiements → Stripe API

**Contrainte :**
Stripe impose son modèle (PaymentIntent, charges, webhooks). Paiements doit s'y conformer sans pouvoir le modifier.

**Adaptation :**
```python
# adapters/stripe_adapter.py
class StripeAdapter:
    def process_payment(self, montant: Money, metadata: dict) -> Transaction:
        # Conversion vers format Stripe
        stripe_intent = stripe.PaymentIntent.create(
            amount=int(montant.euros * 100),  # centimes
            currency="eur",
            metadata=metadata
        )
        # Retour vers domaine Paiements
        return Transaction(
            id=stripe_intent.id,
            montant=montant,
            statut=self._map_status(stripe_intent.status)
        )
```

**Justification :** Aucune négociation possible avec un prestataire externe, le context s'adapte intégralement.

---

### 4. Customer/Supplier : Catalogue → Réservations

**Flux d'événements :**
```
Catalogue (Upstream)
    │ publish: SéancePlanifiée
    │          {seance_id, salle_id, capacité, horaire}
    ▼
Réservations (Downstream)
    │ consumes & reacts:
    └──> Initialiser la disponibilité des N places
```

**Justification :** Catalogue définit les séances de manière autoritaire. Réservations dépend de ces informations pour créer son état initial (liste des places disponibles).

---

## Matrice de dépendances

| Context | Dépend de | Type de dépendance |
|---------|-----------|-------------------|
| Réservations | Catalogue | Données (ACL) |
| Réservations | Paiements | Collaboration (Partnership) |
| Paiements | Stripe API | Conformité stricte (Conformist) |
| Catalogue | - | Autonome |