# Scénario : Billetterie Cinéma

## Description du domaine

Le système de billetterie cinéma permet aux clients de consulter les séances disponibles, de réserver des places en ligne, et de procéder au paiement de leurs billets. Les caissiers peuvent gérer les réservations sur place et valider les billets, tandis que les gestionnaires administrent la programmation des films, la configuration des salles et suivent les statistiques de fréquentation.

## Rôles identifiés

### 1. Client
**Responsabilités :**
- Consulter la programmation des films et séances
- Réserver et acheter des places en ligne
- Choisir ses places dans la salle
- Annuler une réservation (sous conditions)
- Récupérer ses billets (email ou sur place)

### 2. Caissier
**Responsabilités :**
- Créer des réservations pour les clients sur place
- Valider et encaisser les paiements
- Imprimer les billets physiques
- Contrôler les billets à l'entrée des salles
- Gérer les remboursements et modifications

### 3. Gestionnaire
**Responsabilités :**
- Créer et planifier les séances
- Configurer les salles (nombre de places, disposition)
- Gérer le catalogue des films
- Définir les tarifs (plein, réduit, abonnés)
- Consulter les statistiques de réservation et chiffre d'affaires