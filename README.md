# TP fil rouge — Domain-Driven Design

**Scénario** : Billetterie & réservation — réseau de cinémas
**Auteur** : Kevin CARTTIGUEANE EZAROUALI Abdelkader — ESGI M2
**Date** : 2026-04-27

> TP **100 % conceptuel** — modélisation, documentation et schémas. **Aucun code applicatif** n'est requis.

---

## Vision rapide

Un système de billetterie cinéma multi-canaux, modélisé selon les principes DDD :

- **3 Bounded Contexts** : Réservations (Core), Paiements (Generic), Catalogue (Supporting).
- **2 agrégats clés** : `Réservation` et `Paiement` avec 8 invariants validés par scénarios Given/When/Then.
- **Architecture hexagonale** isolant le domaine pur des adapters techniques.
- **Intégrations** REST (synchrone) + RabbitMQ (asynchrone) + contrats versionnés.
- **Observabilité** complète : Correlation ID, métriques métier, logs structurés, tracing distribué.

---

## Carte des livrables (par chapitre)

### Partie 1 — Découverte du domaine (chap. 1)

| Livrable | Fichier | Contenu |
|----------|---------|---------|
| Description du domaine | [`docs/domaine.md`](docs/domaine.md) | Scénario, 3 rôles, 5 problématiques, fil rouge narratif |
| Event Storming | [`docs/event-storming.md`](docs/event-storming.md) + [`docs/event-storming.png`](docs/event-storming.png) | 12 événements, 7 commandes, 5 acteurs |
| Ubiquitous Language v1 + v2 | [`docs/ubiquitous-language.md`](docs/ubiquitous-language.md) | 30+ termes, contexte principal indiqué |
| Vue d'ensemble + sous-domaines | [`docs/domain-overview.md`](docs/domain-overview.md) | 8 fonctionnalités classées Core/Supporting/Generic |

### Partie 2 — Bounded Contexts & Context Map (chap. 2)

| Livrable | Fichier | Contenu |
|----------|---------|---------|
| Bounded Contexts | [`docs/bounded-contexts.md`](docs/bounded-contexts.md) | 3 BCs détaillés (rôle, frontières, responsabilités) |
| Context Map | [`docs/context-map.md`](docs/context-map.md) | Schéma + tableau des patterns + 3 intégrations techniques |
| Concepts métier | [`docs/domain-concepts.md`](docs/domain-concepts.md) | 2 entités + 1 objet valeur formalisés |

### Partie 3 — Modélisation tactique (chap. 3)

| Livrable | Fichier | Contenu |
|----------|---------|---------|
| Modèle de domaine | [`docs/domain-model.md`](docs/domain-model.md) + [`docs/images/domain-model.png`](docs/images/domain-model.png) | 3 entités, 4 objets valeur, diagramme UML (Mermaid + ASCII + PNG) |
| Agrégats & invariants | [`docs/invariants.md`](docs/invariants.md) | 2 agrégats, 8 invariants, schémas UML |
| Tests de domaine | [`docs/tests-domaine.md`](docs/tests-domaine.md) | 16 scénarios Given/When/Then (8 happy + 8 sad) |

### Partie 4 — Architecture hexagonale (chap. 4)

| Livrable | Fichier | Contenu |
|----------|---------|---------|
| Architecture hexagonale | [`docs/architecture-hexagonale.md`](docs/architecture-hexagonale.md) | 3 couches + ports/adapters + flux narratif |
| Repositories | [`docs/repositories.md`](docs/repositories.md) | 3 repositories conceptuels avec opérations métier |
| Exemples API REST | [`docs/api-examples.md`](docs/api-examples.md) | 3 endpoints (POST, GET, DELETE) avec mapping UL |
| Scénarios d'intégration | [`docs/integration-scenarios.md`](docs/integration-scenarios.md) | E2E narratif + diagramme de séquence |

### Partie 5 — Intégration entre contextes & qualité (chap. 5)

| Livrable | Fichier | Contenu |
|----------|---------|---------|
| Contrats d'échange | [`docs/contracts.md`](docs/contracts.md) | 4 contrats (REST + événements) en JSON Schema |
| Design des intégrations | [`docs/integration-design.md`](docs/integration-design.md) | REST synchrone + 2 intégrations événementielles |
| Observabilité | [`docs/observability.md`](docs/observability.md) | Correlation ID + 5 métriques + logs JSON + tracing |
| Scénario final | [`docs/scenario-final.md`](docs/scenario-final.md) | E2E inter-contextes complet avec invariants rappelés |

### Partie 6 — Mise en production & présentation (chap. 6)

| Livrable | Fichier | Contenu |
|----------|---------|---------|
| Vision de déploiement | [`docs/deployment-vision.md`](docs/deployment-vision.md) | Découpage Docker + pseudo Dockerfile annoté |
| Architecture runtime | [`docs/architecture-runtime.md`](docs/architecture-runtime.md) | Schéma services + bus + flux Correlation ID |
| Dashboard Grafana | [`docs/dashboard-grafana.md`](docs/dashboard-grafana.md) + [`docs/dashboard-grafana.png`](docs/dashboard-grafana.png) | Maquette annotée — KPIs, courbes, logs |
| Support de présentation | [`docs/presentation-support.md`](docs/presentation-support.md) + [`docs/presentation-support.pptx`](docs/presentation-support.pptx) | 7 slides couvrant toutes les parties |

---

## Vérification de conformité au TP

| Exigence du TP | Statut | Référence |
|----------------|--------|-----------|
| `domaine.md` avec scénario, 3 rôles, 3-5 problématiques, fil rouge 10-20 lignes | ✅ | `docs/domaine.md` |
| `event-storming.png` ≥ 10 événements, ≥ 5 commandes, acteurs, flux | ✅ | `docs/event-storming.png` |
| `ubiquitous-language.md` ≥ 20 termes (v1 puis v2) | ✅ | 30+ termes, section "Termes par contexte" présente |
| `domain-overview.md` ≥ 6 fonctionnalités classées | ✅ | 8 fonctionnalités |
| `bounded-contexts.md` ≥ 3 BCs | ✅ | 3 BCs détaillés |
| `context-map.md` schéma + table de relations + ≥ 3 intégrations | ✅ | 4 relations + 3 intégrations |
| `domain-concepts.md` 2 entités + 1 OV avec invariants | ✅ | Réservation, Séance, Montant |
| `domain-model.md` 3 entités + 3 OV + UML | ✅ | Mermaid + ASCII + PNG |
| `invariants.md` 2 agrégats × 3 invariants min | ✅ | 8 invariants au total |
| `tests-domaine.md` Given/When/Then happy + sad par invariant | ✅ | 16 scénarios |
| `architecture-hexagonale.md` 3 couches + flux | ✅ | Domaine, Application, Adapters |
| `repositories.md` 2 interfaces conceptuelles | ✅ | 3 repositories |
| `api-examples.md` 1 POST + 1 GET | ✅ | 3 endpoints |
| `integration-scenarios.md` E2E + diagramme de séquence | ✅ | UML + narration |
| `contracts.md` ≥ 1 contrat formel | ✅ | 4 contrats JSON Schema |
| `integration-design.md` 1 REST + 1 événement | ✅ | 3 intégrations modélisées |
| `observability.md` Correlation ID + 3 métriques + log structuré | ✅ | 5 métriques, JSON exemples, tracing |
| `scenario-final.md` ≥ 2 contexts, narratif 15-30 lignes | ✅ | 6 étapes, 8 événements |
| `deployment-vision.md` description + Dockerfile annoté | ✅ | 6 sections |
| `architecture-runtime.md` schéma + description 10-15 lignes | ✅ | Schéma complet + flux Correlation ID |
| `dashboard-grafana.png` 1 métrique technique + 1 métrique métier | ✅ | 4 KPIs + 6 panneaux |
| `presentation-support.pdf` ou `.pptx` 7 slides | ✅ | `presentation-support.pptx` |

---

## Arborescence

```
TP_FilleRougeDomainDrivenDesign/
├── README.md                     ← ce fichier
├── docs/
│   ├── domaine.md
│   ├── event-storming.md
│   ├── event-storming.png
│   ├── ubiquitous-language.md
│   ├── domain-overview.md
│   ├── bounded-contexts.md
│   ├── context-map.md
│   ├── domain-concepts.md
│   ├── domain-model.md
│   ├── invariants.md
│   ├── tests-domaine.md
│   ├── architecture-hexagonale.md
│   ├── repositories.md
│   ├── api-examples.md
│   ├── integration-scenarios.md
│   ├── contracts.md
│   ├── integration-design.md
│   ├── observability.md
│   ├── scenario-final.md
│   ├── deployment-vision.md
│   ├── architecture-runtime.md
│   ├── dashboard-grafana.md
│   ├── dashboard-grafana.png
│   ├── presentation-support.md
│   ├── presentation-support.pptx
│   └── images/
│       ├── domain-model.png
│       └── SchemaDeRep.webp
└── (squelette code legacy : adapters/, application/, domain/, tests/ — non utilisé)
```

---

## Comment lire ce repository ?

1. Commencer par **`docs/domaine.md`** pour comprendre le contexte métier.
2. Continuer avec **`docs/ubiquitous-language.md`** pour le vocabulaire commun.
3. Explorer **`docs/bounded-contexts.md`** + **`docs/context-map.md`** pour la vue stratégique.
4. Approfondir **`docs/domain-model.md`** + **`docs/invariants.md`** + **`docs/tests-domaine.md`** pour la modélisation tactique.
5. Lire **`docs/architecture-hexagonale.md`** + **`docs/architecture-runtime.md`** pour la vision technique.
6. Terminer par **`docs/scenario-final.md`** qui démontre le système de bout en bout.

> Pour la présentation orale : **`docs/presentation-support.pptx`** (7 slides, ~10 min).
