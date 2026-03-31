# Scénario choisi

**Billetterie & réservation**

---

# Contexte métier

Le système de billetterie cinéma permet aux clients de consulter les séances disponibles, de réserver des places en ligne, et de procéder au paiement de leurs billets. Les caissiers peuvent gérer les réservations sur place et valider les billets, tandis que les gestionnaires administrent la programmation des films, la configuration des salles et suivent les statistiques de fréquentation.

Les enjeux sont à la fois techniques et commerciaux : garantir la disponibilité des places en temps réel, éviter la surréservation, assurer la fluidité du paiement en ligne et en caisse, et maximiser le taux de remplissage des salles. Le système doit également respecter des contraintes légales (remboursements, accessibilité) et offrir une expérience cohérente sur tous les canaux (site web, application mobile, guichets physiques).

---

# Rôles utilisateurs

| Rôle | Type | Description |
|------|------|-------------|
| **Gestionnaire** | Direction | Responsable de la programmation des films, de la configuration des salles et du suivi des performances commerciales. Il définit les tarifs, planifie les séances et consulte les statistiques de fréquentation et de chiffre d'affaires. |
| **Caissier** | Opérationnel | Agent en contact direct avec les clients au guichet. Il crée et modifie des réservations, encaisse les paiements, imprime les billets physiques et contrôle l'accès aux salles à l'entrée. |
| **Client** | Client | Utilisateur final qui consulte la programmation, choisit ses places et achète ses billets en ligne ou sur place. Il peut également annuler une réservation dans les délais autorisés et récupérer ses billets par email ou au guichet. |

---

# Problématiques métier

1. **Gestion de la disponibilité en temps réel** : plusieurs clients peuvent tenter de réserver la même place simultanément, notamment lors des sorties très attendues. Le système doit garantir l'unicité de chaque réservation de place et éviter toute surréservation.

2. **Multiplicité des canaux de vente** : les billets sont vendus en ligne, via l'application mobile et aux guichets physiques. Il faut assurer une cohérence de l'inventaire des places sur tous ces canaux en même temps.

3. **Gestion des annulations et remboursements** : les règles d'annulation varient selon le type de billet (plein tarif, réduit, abonné) et le délai avant la séance. Le système doit appliquer ces règles automatiquement tout en respectant les obligations légales.

4. **Planification et optimisation des séances** : le gestionnaire doit pouvoir programmer plusieurs films dans plusieurs salles sur une même journée, en tenant compte des durées, des intervalles de nettoyage entre deux séances et des contraintes de capacité de chaque salle.

5. **Gestion des tarifs et des profils clients** : le cinéma propose plusieurs grilles tarifaires (plein tarif, étudiant, senior, abonné, carte illimitée). Le système doit vérifier l'éligibilité du client au tarif demandé et traiter les avantages associés aux abonnements.

---

# Scénario fil rouge

Marie, une cliente régulière, consulte le site du cinéma un vendredi soir pour réserver des places pour le dernier film Marvel qui sort le lendemain. Elle se connecte à son compte, sélectionne la séance du samedi à 20h00 et accède au plan de salle interactif. Elle choisit deux places côte à côte en milieu de rangée. Le système vérifie en temps réel la disponibilité de ces places et les réserve temporairement pendant cinq minutes, le temps que Marie finalise son achat.

Marie sélectionne le tarif "plein" pour elle et le tarif "étudiant" pour son ami. Elle procède au paiement par carte bancaire via le module de paiement sécurisé. Une fois le paiement validé, le système enregistre la réservation, génère deux billets électroniques avec des QR codes uniques et les envoie par email à Marie.

Le lendemain, Marie et son ami arrivent au cinéma. À l'entrée de la salle, le caissier scanne les QR codes sur les téléphones de Marie. Le système valide les billets, marque les places comme occupées et autorise l'accès à la salle. La séance commence avec un taux de remplissage de 94%, ce que le gestionnaire peut constater en temps réel depuis son tableau de bord. En fin de journée, il consulte le récapitulatif des recettes et le taux d'occupation moyen de la journée pour alimenter son rapport hebdomadaire.