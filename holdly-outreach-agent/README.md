# Holdly — Agent d'outreach multi-canal

Playbook complet pour un agent IA qui prospecte, contacte et relance des PME au Québec / Canada pour Holdly.

> **Statut** : v1 — playbook + templates. Le code d'exécution (script Node/Python + intégration Google Sheet + intégration Resend/email) reste à brancher selon le stack choisi.

## Ce que fait l'agent

1. **Cherche** des prospects qualifiés (PME de services au QC/CA) sur 4 canaux.
2. **Enrichit** chaque prospect (nom, rôle, téléphone, site, signal de fit).
3. **Remplit** un Google Sheet structuré (le "CRM léger" de l'opération).
4. **Rédige** un message personnalisé par prospect, par canal, en FR ou EN.
5. **Envoie** : automatique pour l'email conforme ; **prépare une file manuelle** pour LinkedIn / IG / TikTok / FB / Kijiji.
6. **Track les relances** : qui relancer, quand, avec quel message.

## Ce qu'il NE fait PAS (et pourquoi)

- **DM automatisé en masse sur IG / TikTok / FB / LinkedIn** → violation des ToS, ban quasi garanti, exposition à la LCAP. L'agent prépare les messages, **l'humain envoie**.
- **Scraping agressif de Kijiji** → contraire aux ToS. Recherche manuelle assistée seulement.
- **Email à froid sans opt-out ni identité claire** → violation LCAP, amendes jusqu'à 10M $.

Voir [`07-compliance.md`](./07-compliance.md) pour les garde-fous.

## Structure du playbook

| Fichier | Contenu |
|---|---|
| [`01-strategy.md`](./01-strategy.md) | ICP, canaux, volumes cibles |
| [`02-sheet-schema.md`](./02-sheet-schema.md) | Schéma exact du Google Sheet (CRM) |
| [`03-prospecting.md`](./03-prospecting.md) | Recettes de recherche par canal |
| [`04-messages-fr.md`](./04-messages-fr.md) | Templates FR par vertical / canal |
| [`05-messages-en.md`](./05-messages-en.md) | Templates EN par vertical / canal |
| [`06-followup.md`](./06-followup.md) | Cadence des relances |
| [`07-compliance.md`](./07-compliance.md) | LCAP, PIPEDA, ToS plateformes |
| [`08-agent-runbook.md`](./08-agent-runbook.md) | Prompt système + boucle quotidienne de l'agent |

## Inputs à confirmer

À fournir avant le lancement :

- [ ] **Outil CRM** : Google Sheet (défaut) ou Airtable / HubSpot ?
- [ ] **Email sender** : Resend (défaut, simple) / SendGrid / Smartlead ?
- [ ] **Domaine d'envoi** : `outreach@holdly.pro` ou sous-domaine dédié ?
- [ ] **Volume cible** : 50 / 100 / 200 prospects par semaine ?
- [ ] **Verticaux à prioriser** : cliniques / salons / immo / restos / services pro — top 2 ?
- [ ] **Calendrier** : lien Cal.com / Calendly pour le booking d'appel stratégie ?
- [ ] **Liste d'exclusion** : clients actuels + prospects en cours (anti-double-touch).

## Démarrage rapide

1. Copier le template de Google Sheet depuis [`02-sheet-schema.md`](./02-sheet-schema.md).
2. Remplir les inputs ci-dessus dans la feuille `Config`.
3. Lancer le prompt système de [`08-agent-runbook.md`](./08-agent-runbook.md) dans un agent Claude avec accès au Sheet + outils de recherche web.
4. L'agent produit chaque jour : `N` prospects nouveaux + `M` relances + une file d'envoi manuel pour les réseaux sociaux.
