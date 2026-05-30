# 06 — Cadence des relances

Principe : **3 relances max après le premier message, puis breakup**. Au-delà = nuisance, dégrade la marque.

Total sur un prospect non-répondant : **4 touches sur 21 jours**, puis exclusion automatique.

---

## Cadence email

| Touche | Délai après précédente | Type | Stratégie |
|---|---|---|---|
| 1 | J+0 | `initial` | Hook personnalisé + offre + CTA |
| 2 | J+4 | `relance_1` | "Bump" — courte, ramène le message en haut de l'inbox |
| 3 | J+9 | `relance_2` | Changement d'angle — preuve sociale (cas client) |
| 4 | J+18 | `breakup` | Dernière touche — "je ferme votre dossier" |

### Template `relance_1` (FR)

```
Bonjour {{prénom}},

Je remonte ce fil — peut-être enseveli sous le reste.

15 min pour voir si Elodie peut aider {{entreprise}} à ne plus rater de RDV ?
👉 {{calendrier_url}}

{{signature}}

---
Désabonnement : {{lien_desabonnement}}
```

### Template `relance_2` (FR — preuve sociale)

```
Bonjour {{prénom}},

Petit exemple : on a aidé {{cas_client_meme_vertical — ex: "une clinique dentaire
de Laval"}} à passer de ~25 % d'appels manqués à ~3 %. Résultat : ~8 nouveaux
RDV/semaine récupérés.

Le déploiement a pris 3 jours. Si ça vous parle, 15 min ici : {{calendrier_url}}

{{signature}}

---
Désabonnement : {{lien_desabonnement}}
```

### Template `breakup` (FR)

```
Bonjour {{prénom}},

Je vais clore votre dossier — je présume que ce n'est pas le bon moment pour
{{entreprise}}.

Si la question des appels manqués revient sur la table dans 3 ou 6 mois,
holdly.co est toujours là. Pas de relance de ma part d'ici là.

Bonne continuation,
{{signature}}

---
Désabonnement : {{lien_desabonnement}}
```

> **Pourquoi le breakup marche** : 5-15 % des leads silencieux répondent au breakup ("attendez, parlez-moi"). Psychologie de la perte > psychologie du gain.

---

## Cadence LinkedIn

| Touche | Délai | Type | Note |
|---|---|---|---|
| 1 | J+0 | Connection request avec note courte | Pas de pitch dans la note |
| 2 | J+3 (si acceptée) | Premier vrai message (le template "Initial" du `04`) | |
| 3 | J+8 | Relance courte | "{{prénom}}, est-ce que c'est encore un sujet d'actualité chez {{entreprise}} ?" |
| 4 | J+20 | Breakup | "Je vais arrêter de vous embêter — bonne continuation" |

> Si la demande de connexion n'est pas acceptée après 14 jours → on retire la demande et on passe sur un autre canal (email).

---

## Cadence IG / FB / TikTok

Cadence plus légère parce que les filtres de spam sont agressifs et qu'un même message qui revient sonne le "block".

| Touche | Délai | Action |
|---|---|---|
| 1 | J+0 | DM initial |
| 2 | J+7 | UNE relance "{{prénom}}, ça t'intéresse ?" |
| — | — | **Pas de 3e touche.** Si pas de réponse, fermer le dossier. |

---

## Cadence Kijiji

Une seule réponse par annonce. Pas de relance. Si pas de retour dans 7 jours → fermé.

---

## Règles transverses

### Si réponse "pas intéressé" / "stop" / désabonnement

→ `statut = répondu_pas_intéressé`
→ `exclusion = TRUE`
→ Ajouter le domaine email dans l'onglet `Exclusion`
→ **Jamais re-contacter sur aucun canal**.

### Si réponse "rappelez-moi dans X mois"

→ `statut = nurture`
→ `date_prochaine_action = aujourd'hui + X mois`
→ L'agent remet en file à ce moment

### Si réponse "je veux en savoir plus" / "envoyez infos"

→ `statut = répondu_intéressé`
→ Notification dans le canal d'alerte `[À CONFIRMER : Slack, email, SMS ?]`
→ **Réponse humaine** dans la journée (SLA 2h, c'est la promesse Holdly)

### Si RDV booké

→ `statut = rdv_booké`
→ Email de confirmation (template existant Holdly)
→ Rappel SMS 24h avant (template existant Holdly)
→ Après le RDV : maj `statut = démo_faite`

### Bounce email

→ `statut = email_invalide`
→ Re-vérification du décideur via LinkedIn
→ Si décideur trouvé via autre canal → bascule sur ce canal
→ Sinon → fermer dossier

---

## Volume de relances vs nouveaux contacts

Sur une journée type, l'agent traite **~60 % de nouveaux + ~40 % de relances**. Trop de nouveaux = pas assez de capitalisation sur ceux déjà touchés.

Exemple journée à 30 emails :
- 18 emails initiaux (nouveaux prospects)
- 8 relances 1
- 3 relances 2
- 1 breakup

L'agent calcule ça automatiquement depuis `Prospects.date_prochaine_action`.
