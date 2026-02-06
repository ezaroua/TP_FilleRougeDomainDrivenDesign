# Vue d'ensemble du domaine — Billetterie Cinéma

## Liste des fonctionnalités

1. **Réservation et gestion intelligente des places**
2. **Programmation des séances**
3. **Calcul de tarification**
4. **Génération et validation des billets**
5. **Gestion du catalogue de films**
6. **Traitement des paiements**
7. **Envoi de notifications clients**
8. **Planification des équipes**

## Classification des sous-domaines

| Fonctionnalité | Type (Core / Supporting / Generic) | Justification (2–3 phrases) |
|----------------|-----------------------------------|------------------------------|
| **Réservation et gestion intelligente des places** | Core Domain | C'est notre véritable différenciation. On a développé un système qui détecte et évite les places isolées, ce qui maximise notre taux de remplissage. Pendant les grosses sorties, cette optimisation fait vraiment la différence sur nos revenus. |
| **Programmation des séances** | Core Domain | La planification est complexe : 8 salles de tailles différentes, équilibre blockbusters/films d'auteur, contraintes techniques (15-20 min de nettoyage), projections scolaires. Cette optimisation nous permet de maximiser le CA tout en respectant nos obligations contractuelles (20% films indépendants). |
| **Calcul de tarification** | Core Domain | Actuellement on a des tarifs standards mais on prévoit d'évoluer vers une tarification dynamique en 2025 (moins cher en semaine, plus cher samedi soir). Cette capacité d'adaptation tarifaire deviendra un avantage concurrentiel majeur. |
| **Génération et validation des billets** | Supporting Domain | Nécessaire au fonctionnement mais pas différenciant. La génération de QR codes et la validation à l'entrée utilisent des technologies standard. Important pour l'expérience client mais ne nous distingue pas de la concurrence. |
| **Gestion du catalogue de films** | Supporting Domain | On récupère les données d'Allociné mais on les enrichit avec nos propres tags adaptés à notre public local (beaucoup de familles). Cette couche d'enrichissement justifie le classement en Supporting plutôt que Generic. |
| **Planification des équipes** | Supporting Domain | Essentiel pour le fonctionnement quotidien (15 personnes à planifier selon l'affluence prévue) mais n'apporte pas de valeur différenciante. Chaque séance doit avoir son projectionniste, chaque période de forte affluence ses caissiers. |
| **Traitement des paiements** | Generic Domain | On utilise Stripe. Aucun intérêt à réinventer la roue pour les paiements CB, c'est trop risqué niveau sécurité. Stripe gère tout (CB, Apple Pay, Google Pay) et c'est largement suffisant. |
| **Envoi de notifications clients** | Generic Domain | Complètement standard : SendGrid pour les emails de confirmation, Twilio pour les SMS de rappel 1h avant. Des templates basiques suffisent, rien de spécifique à notre métier. |

## Schéma de répartition

```
TODO 

```

## Notes et réflexions

### Points encore à clarifier

1. **Reporting et statistiques** : On hésite entre Generic (si c'est juste du reporting basique) et Core (si on développe de la prédiction d'affluence pour optimiser la programmation).

2. **Programme de fidélité** : Le directeur veut lancer un système de points en 2025. À déterminer si ça s'intègre dans Tarification ou devient un Supporting Domain séparé.

3. **Contrôle d'accès physique** : Si on installe des portiques automatiques, est-ce que ça reste dans Billetterie ou ça devient un nouveau sous-domaine ?

### Bounded Contexts pressentis

D'après cette première analyse, on envisage 4-5 Bounded Contexts :
- **Context Réservation** (Core)
- **Context Programmation** (Core)
- **Context Billetterie** (Supporting)
- **Context Paiement** (Generic)
- **Context Catalogue** (Supporting - possibilité de fusion avec Programmation)

