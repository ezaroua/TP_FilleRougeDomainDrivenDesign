# Tests de Domaine — Scénarios Given/When/Then

> Chapitre 3 — Livrable 3 : Scénarios textuels (sans code) validant les invariants métier.
> Pour chaque invariant défini dans `invariants.md`, 2 scénarios : happy path et sad path.

---

## Agrégat : Réservation

### INV-R1 : Limite de 10 places par réservation

#### Scénario Happy Path — Ajout dans la limite autorisée

**Given** une réservation en cours pour la séance #S123, contenant actuellement 8 places réservées, avec un statut EN_ATTENTE

**When** le client sélectionne 2 places supplémentaires (F11 et F12)

**Then** les 2 places sont ajoutées à la réservation, portant le total à 10 places, et le montant_total est recalculé à 115,00€ (10 × 11,50€)

---

#### Scénario Sad Path — Dépassement de la limite

**Given** une réservation en cours pour la séance #S123, contenant déjà 10 places réservées

**When** le client tente d'ajouter une 11ème place (G01)

**Then** le système refuse l'ajout avec le message "Une réservation ne peut excéder 10 places", la réservation reste à 10 places et la place G01 reste libre pour d'autres clients

---

### INV-R2 : Expiration automatique après 15 minutes

#### Scénario Happy Path — Confirmation dans les délais

**Given** une réservation #RES-456 créée à 19h30 pour 3 places, avec expiration à 19h45, statut EN_ATTENTE

**When** le client confirme le paiement à 19h42 (avant l'expiration)

**Then** la réservation passe au statut CONFIRMÉE, les places sont définitivement attribuées au client, un billet électronique est généré et une notification de confirmation est envoyée

---

#### Scénario Sad Path — Tentative de confirmation après expiration

**Given** une réservation #RES-456 créée à 19h30, expirée à 19h45, il est maintenant 19h52 et la réservation est toujours EN_ATTENTE

**When** le client tente de confirmer le paiement pour cette réservation

**Then** le système refuse la confirmation avec le message "Réservation expirée — veuillez recommencer votre sélection", les places sont libérées et redeviennent disponibles pour d'autres clients, la réservation passe au statut ANNULÉE

---

### INV-R3 : Immuabilité après confirmation

#### Scénario Happy Path — Consultation d'une réservation confirmée

**Given** une réservation #RES-789 confirmée et payée, contenant les places D05, D06, D07

**When** le client consulte les détails de sa réservation

**Then** le système affiche les informations de la réservation (places, séance, montant) en lecture seule, sans possibilité de modification

---

#### Scénario Sad Path — Tentative de modification après confirmation

**Given** une réservation #RES-789 avec statut CONFIRMÉE, le client souhaite changer la place D05 pour E05

**When** le client tente de modifier la sélection de places

**Then** le système refuse la modification avec le message "Impossible de modifier une réservation confirmée — utilisez l'option d'annulation si nécessaire", la réservation reste inchangée avec les places D05, D06, D07

---

## Agrégat : Paiement

### INV-P1 : Montant exact requis

#### Scénario Happy Path — Paiement avec montant correct

**Given** une réservation #RES-456 confirmée avec montant_total = 34,50€ (3 places à 11,50€), un paiement #PAY-001 est créé avec montant = 34,50€

**When** le système valide la cohérence du montant

**Then** le paiement est accepté, la transaction est initiée auprès de Stripe, le paiement passe au statut PENDING puis SUCCESS, la réservation est définitivement confirmée

---

#### Scénario Sad Path — Montant incorrect

**Given** une réservation #RES-456 avec montant_total = 34,50€, un client tente de créer un paiement avec montant = 30,00€

**When** le système vérifie la cohérence du montant

**Then** le système rejette la création du paiement avec le message "Montant incorrect : attendu 34,50€, reçu 30,00€", aucune transaction n'est initiée, la réservation reste EN_ATTENTE

---

### INV-P2 : Unicité du paiement par réservation

#### Scénario Happy Path — Premier paiement pour une réservation

**Given** une réservation #RES-456 EN_ATTENTE, sans paiement associé existant

**When** le système crée un paiement #PAY-001 pour cette réservation

**Then** le paiement est créé avec succès, la transaction Stripe est initiée, la réservation est mise à jour vers CONFIRMÉE une fois le paiement validé

---

#### Scénario Sad Path — Tentative de double-paiement

**Given** une réservation #RES-456 qui possède déjà un paiement #PAY-001 avec statut SUCCESS

**When** le système reçoit une demande de création d'un second paiement #PAY-002 pour la même réservation

**Then** le système rejette la création avec le message "Cette réservation a déjà un paiement réussi (#PAY-001)", aucune transaction supplémentaire n'est créée, la réservation reste CONFIRMÉE sans double-facturation

---

### INV-P3 : Statut final immuable (SUCCESS ou FAILED)

#### Scénario Happy Path — Consultation d'un paiement finalisé

**Given** un paiement #PAY-001 avec statut SUCCESS, traité le 15/02/2026 à 19h45, montant = 34,50€

**When** le système consulte ce paiement dans le cadre d'un remboursement

**Then** le système identifie correctement le statut SUCCESS, autorise la procédure de remboursement (qui crée une nouvelle opération, sans modifier le statut du paiement original)

---

#### Scénario Sad Path — Tentative de re-traitement d'un paiement finalisé

**Given** un paiement #PAY-001 avec statut FAILED (échec de carte bancaire)

**When** un opérateur tente de re-lancer le traitement sur ce même paiement

**Then** le système refuse l'opération avec le message "Paiement #PAY-001 déjà finalisé avec statut FAILED — créez un nouveau paiement pour réessayer", le client doit recommencer avec un nouveau paiement #PAY-002

---

## Tableau récapitulatif des scénarios

| Invariant | Happy Path | Sad Path |
|-----------|-----------|---------|
| INV-R1 : Max 10 places | Ajout de 2 places sur 8 existantes → OK (10 total) | Tentative d'ajout sur 10 existantes → rejet |
| INV-R2 : Expiration 15min | Confirmation à 19h42, expiration à 19h45 → confirmée | Confirmation à 19h52, expirée à 19h45 → rejet |
| INV-R3 : Immuable confirmée | Consultation d'une réservation confirmée → lecture seule | Modification d'une réservation confirmée → rejet |
| INV-P1 : Montant exact | Paiement 34,50€ pour réservation 34,50€ → accepté | Paiement 30,00€ pour réservation 34,50€ → rejet |
| INV-P2 : Unicité paiement | Premier paiement pour réservation → créé | Second paiement pour réservation déjà payée → rejet |
| INV-P3 : Statut final | Consultation d'un paiement SUCCESS pour remboursement | Re-traitement d'un paiement FAILED → rejet |
