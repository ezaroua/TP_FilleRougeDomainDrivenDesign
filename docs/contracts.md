# Contrats d'Échange entre Contextes

> Chapitre 5 — Livrable 1 : Formalisation des contrats d'échange entre Bounded Contexts.
> Format : JSON Schema + description narrative.

---

## Contrat 1 — REST : Réservations → Catalogue (ACL)

### Métadonnées

| Champ | Valeur |
|-------|--------|
| **Contexte source** | Réservations |
| **Contexte cible** | Catalogue |
| **Objectif métier** | Récupérer les informations d'une séance pour créer une réservation |
| **Type** | Appel REST synchrone (GET) |
| **Pattern** | Customer/Supplier + ACL (Réservations traduit via son adapter) |

### Schéma de requête
```
GET /catalogue/api/v1/seances/{seance_id}
Accept: application/json
```

### Schéma de réponse (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SeanceInfo",
  "description": "Informations minimales d'une séance, vues par le contexte Réservations",
  "type": "object",
  "required": ["seance_id", "salle_id", "heure_debut", "capacite_totale", "tarif_plein"],
  "properties": {
    "seance_id": {
      "type": "string",
      "pattern": "^SCR-[0-9]+$",
      "description": "Identifiant unique de la séance"
    },
    "salle_id": {
      "type": "string",
      "description": "Identifiant de la salle de projection"
    },
    "heure_debut": {
      "type": "string",
      "format": "date-time",
      "description": "Heure de début de la séance (ISO 8601)"
    },
    "capacite_totale": {
      "type": "integer",
      "minimum": 1,
      "description": "Nombre total de places dans la salle"
    },
    "tarif_plein": {
      "type": "number",
      "minimum": 0,
      "multipleOf": 0.01,
      "description": "Prix plein tarif en euros"
    },
    "tarif_reduit": {
      "type": "number",
      "minimum": 0,
      "multipleOf": 0.01,
      "description": "Prix tarif réduit en euros (optionnel)"
    }
  }
}
```

### Risques / Contraintes
- Si le Catalogue est indisponible, le contexte Réservations doit gérer la dégradation (erreur métier explicite, pas de réservation silencieusement incorrecte)
- L'ACL dans Réservations traduit `SeanceInfo` en `SeanceContexte` (modèle interne) — un changement dans le schéma Catalogue ne doit pas impacter directement les agrégats Réservations
- La version du contrat doit être maintenue : utiliser `/v1/seances/` pour versionner explicitement

---

## Contrat 2 — Événement : Réservations → Paiements (Partnership)

### Métadonnées

| Champ | Valeur |
|-------|--------|
| **Contexte source** | Réservations (producteur) |
| **Contexte cible** | Paiements (consommateur) |
| **Objectif métier** | Déclencher le traitement du paiement pour une réservation validée |
| **Type** | Événement de domaine (asynchrone via message broker) |
| **Pattern** | Partnership (collaboration bidirectionnelle) |
| **Nom de l'événement** | `PaiementRequis` |

### Schéma de l'événement (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PaiementRequis",
  "description": "Événement émis par le contexte Réservations pour demander l'initiation d'un paiement",
  "type": "object",
  "required": ["event_id", "event_type", "emis_le", "correlation_id", "payload"],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "Identifiant unique de cet événement (pour idempotence)"
    },
    "event_type": {
      "type": "string",
      "const": "PaiementRequis",
      "description": "Type de l'événement"
    },
    "emis_le": {
      "type": "string",
      "format": "date-time",
      "description": "Horodatage d'émission (ISO 8601)"
    },
    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "Identifiant de corrélation de la requête originale"
    },
    "payload": {
      "type": "object",
      "required": ["reservation_id", "client_id", "montant_total", "expire_le"],
      "properties": {
        "reservation_id": {
          "type": "string",
          "pattern": "^RES-[0-9]+$"
        },
        "client_id": {
          "type": "string",
          "pattern": "^CLI-[0-9]+$"
        },
        "montant_total": {
          "type": "number",
          "minimum": 0.01,
          "multipleOf": 0.01
        },
        "expire_le": {
          "type": "string",
          "format": "date-time",
          "description": "Délai d'expiration de la réservation — le paiement doit intervenir avant cette date"
        }
      }
    }
  }
}
```

### Exemple de message

```json
{
  "event_id": "evt-550e8400-e29b-41d4-a716-446655440000",
  "event_type": "PaiementRequis",
  "emis_le": "2026-03-15T19:46:23Z",
  "correlation_id": "corr-a1b2c3d4",
  "payload": {
    "reservation_id": "RES-789",
    "client_id": "CLI-123",
    "montant_total": 23.00,
    "expire_le": "2026-03-15T20:01:23Z"
  }
}
```

---

## Contrat 3 — Événement : Paiements → Réservations (Partnership)

### Métadonnées

| Champ | Valeur |
|-------|--------|
| **Contexte source** | Paiements (producteur) |
| **Contexte cible** | Réservations (consommateur) |
| **Objectif métier** | Notifier le résultat d'un paiement pour confirmer ou annuler la réservation |
| **Type** | Événement de domaine (asynchrone) |
| **Pattern** | Partnership |
| **Noms des événements** | `PaiementValidé`, `PaiementÉchoué` |

### Schéma de l'événement PaiementValidé (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PaiementValidé",
  "type": "object",
  "required": ["event_id", "event_type", "emis_le", "correlation_id", "payload"],
  "properties": {
    "event_id": { "type": "string", "format": "uuid" },
    "event_type": { "type": "string", "const": "PaiementValidé" },
    "emis_le": { "type": "string", "format": "date-time" },
    "correlation_id": { "type": "string", "format": "uuid" },
    "payload": {
      "type": "object",
      "required": ["reservation_id", "payment_id", "transaction_id", "montant"],
      "properties": {
        "reservation_id": { "type": "string" },
        "payment_id": { "type": "string" },
        "transaction_id": {
          "type": "string",
          "description": "Identifiant de transaction Stripe"
        },
        "montant": { "type": "number", "minimum": 0.01 }
      }
    }
  }
}
```

### Risques / Contraintes
- **Idempotence** : Le contexte Réservations doit tolérer la réception en double d'un `PaiementValidé` (utiliser `event_id` comme clé de déduplication)
- **Délai** : Si `PaiementValidé` arrive après l'expiration de la réservation, le contexte Réservations doit refuser la confirmation et le contexte Paiements doit initier un remboursement automatique
- **Compatibilité ascendante** : Ne jamais supprimer de champs dans ces événements — uniquement en ajouter

---

## Contrat 4 — Événement : Catalogue → Réservations (Customer/Supplier)

### Métadonnées

| Champ | Valeur |
|-------|--------|
| **Contexte source** | Catalogue (producteur upstream) |
| **Contexte cible** | Réservations (consommateur downstream) |
| **Objectif métier** | Notifier la création d'une nouvelle séance pour initialiser les disponibilités |
| **Type** | Événement de domaine (asynchrone) |
| **Pattern** | Customer/Supplier |
| **Nom de l'événement** | `SéancePlanifiée` |

### Schéma de l'événement (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SéancePlanifiée",
  "type": "object",
  "required": ["event_id", "event_type", "emis_le", "payload"],
  "properties": {
    "event_id": { "type": "string", "format": "uuid" },
    "event_type": { "type": "string", "const": "SéancePlanifiée" },
    "emis_le": { "type": "string", "format": "date-time" },
    "payload": {
      "type": "object",
      "required": ["seance_id", "salle_id", "capacite", "heure_debut", "tarif_plein"],
      "properties": {
        "seance_id": { "type": "string" },
        "salle_id": { "type": "string" },
        "capacite": { "type": "integer", "minimum": 1 },
        "heure_debut": { "type": "string", "format": "date-time" },
        "tarif_plein": { "type": "number", "minimum": 0 },
        "tarif_reduit": { "type": "number", "minimum": 0 }
      }
    }
  }
}
```
