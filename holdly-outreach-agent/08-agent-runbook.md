# 08 — Runbook de l'agent IA

Comment faire tourner l'agent en pratique. Conçu pour un agent Claude (ou équivalent) avec accès à : Google Sheets API, recherche web, et un service d'envoi d'email (Resend `[À CONFIRMER]`).

---

## Prompt système (à copier dans la config de l'agent)

```
Tu es l'agent d'outreach de Holdly (holdly.co), une agence d'automatisation
IA basée à Montréal. Tu prospectes des PME de services au Québec et au Canada
pour leur vendre une réceptionniste IA bilingue (Elodie) déployable en 72h.

Tu opères selon les playbooks suivants (fournis en contexte) :
- 01-strategy.md : ICP, verticaux, volumes
- 02-sheet-schema.md : structure du Google Sheet CRM
- 03-prospecting.md : comment trouver les prospects par canal
- 04-messages-fr.md / 05-messages-en.md : templates de messages
- 06-followup.md : cadence de relances
- 07-compliance.md : règles légales (LCAP, PIPEDA, ToS)

Tu as accès à :
- Le Google Sheet "Holdly Outreach CRM" (ID : [INSÉRER])
- Recherche web (Google, sites publics)
- L'API Resend pour envoyer des emails au nom de outreach@holdly.pro
  [À CONFIRMER : ou autre sender]

CONTRAINTES ABSOLUES :
1. Tu ne contactes JAMAIS un prospect listé dans l'onglet Exclusion.
2. Tu n'envoies JAMAIS d'email à une adresse non publiée publiquement
   sur le site web de l'entreprise du prospect.
3. Tu n'envoies JAMAIS plus que les volumes définis dans Config.
4. Tu n'envoies JAMAIS de DM automatisé sur LinkedIn, IG, Facebook, TikTok
   ou Kijiji. Pour ces canaux, tu prépares uniquement le message dans
   l'onglet File_envoi_manuel.
5. Tout email contient : signature Holdly, adresse postale, lien de désabonnement.
6. Tu loggues TOUT email envoyé dans Email_log.
7. Si tu doutes (signal faible, langue incertaine, fit incertain) → tu ne contactes
   PAS. Tu marques le prospect score_fit < 3 et tu passes au suivant.

QUALITÉ AVANT VOLUME. Mieux vaut 20 messages excellents que 100 médiocres.
```

---

## Boucle quotidienne (la "journée type" de l'agent)

Exécution recommandée : **1 fois par jour, 7h30 du matin** (heure de Montréal).

### Étape 1 — Démarrage (1 min)

```
1. Lire Config → charger les paramètres du jour.
2. Lire Exclusion → charger en mémoire.
3. Vérifier Email_log des dernières 24h pour bounces / désabonnements → maj Prospects.
4. Lister tous les Prospects où date_prochaine_action <= aujourd'hui
   ET statut PAS DANS (client, perdu, exclusion).
   → c'est la "file du jour".
```

### Étape 2 — Traiter les relances (priorité absolue)

```
Pour chaque prospect en file du jour, dans cet ordre :
  - statut = répondu_intéressé → SKIP (alerte humaine déjà partie)
  - statut = contacté_3 → préparer breakup (email ou file manuelle)
  - statut = contacté_2 → préparer relance_2
  - statut = contacté_1 → préparer relance_1
  - statut = nouveau → traiter au step 4 (nouveaux)

Pour chaque message à envoyer :
  - Choisir template (langue + canal + type)
  - Remplir placeholders depuis Prospects + Config
  - Si canal = email → envoyer + logger
  - Si canal = autre → écrire dans File_envoi_manuel avec priorité 1
  - Maj Prospects : nb_touches += 1, date_dernier_contact, statut, date_prochaine_action
```

### Étape 3 — Traiter les réponses entrantes

```
Pour chaque email entrant dans la boîte outreach@holdly.pro :
  - Matcher avec un Prospect via email expéditeur
  - Analyser le contenu :
    * Intérêt ("oui", "intéressé", "envoyez-moi") → statut = répondu_intéressé
      → notification humaine immédiate
    * Refus ("stop", "pas intéressé", "désabonner") → statut = répondu_pas_intéressé
      → ajouter dans Exclusion
    * Pas maintenant ("dans X mois") → statut = nurture + date_prochaine_action = +X mois
    * Question/objection → préparer réponse en draft → notification humaine
  - Si email humain ambigu : NE PAS répondre auto. Mettre en draft, alerter.
```

### Étape 4 — Nouveaux prospects (jusqu'à atteindre le volume cible)

```
Tant que (nouveaux_aujourd'hui < volume_cible_jour) :
  - Choisir une combinaison (vertical, ville) depuis Config, en rotation.
  - Suivre la recette du canal correspondant (voir 03-prospecting.md).
  - Pour chaque candidat :
    a. Vérifier Exclusion (entreprise + domaine + email). Si match → skip.
    b. Vérifier doublon dans Prospects (par site web + nom). Si déjà là → skip.
    c. Enrichir (décideur, email, signaux).
    d. Calculer score_fit. Si < 3 → ne pas ajouter ; passer au suivant.
    e. Si score_fit ≥ 3 :
       - Ajouter dans Prospects avec statut = nouveau, date_prochaine_action = aujourd'hui.
       - Préparer message initial (template + signal_specifique).
       - Si email : vérifier que l'email est publié sur le site (sinon ne pas envoyer).
       - Envoyer (email) ou écrire dans File_envoi_manuel (autres canaux).
       - Logger.
```

### Étape 5 — Rapport quotidien

À la fin du run, l'agent poste un résumé dans `[À CONFIRMER : Slack ? email ?]` :

```
📊 Rapport outreach Holdly — {{date}}

Nouveaux prospects ajoutés : 42
Emails envoyés : 30 (18 initiaux, 8 R1, 3 R2, 1 breakup)
File manuelle générée : 25 (LinkedIn: 15, IG: 7, Kijiji: 3)

Réponses entrantes traitées : 6
  - 2 intéressés → escaladé à toi (ID: P-00042, P-00051)
  - 3 désabonnements → ajoutés à l'exclusion
  - 1 ambigu → draft prêt pour toi

À ton agenda demain :
  - 17 relances à préparer
  - 3 RDV bookés cette semaine

Anomalies : bounce rate à 1.2 % (cible < 2 %), OK.
```

---

## Pseudo-code (référence pour l'implémentation)

Si tu codes ça en TypeScript ou Python plutôt qu'en agent natif, la structure est la même. Boucle quotidienne déclenchée par un cron.

```typescript
async function dailyOutreachRun() {
  const config = await sheet.readConfig();
  const exclusion = await sheet.readExclusion();

  await processInboundResponses(config, exclusion);

  const todaysQueue = await sheet.getProspectsForToday();
  for (const prospect of todaysQueue) {
    if (isExcluded(prospect, exclusion)) continue;
    await processFollowupTouch(prospect, config);
  }

  let added = 0;
  while (added < config.volumeNewPerDay) {
    const candidate = await findAndEnrichCandidate(config);
    if (!candidate || candidate.scoreFit < 3) continue;
    if (await isDuplicate(candidate)) continue;

    await sheet.addProspect(candidate);
    await sendInitialMessage(candidate, config);
    added++;
  }

  await postDailyReport({ added, ...stats });
}
```

---

## Gouvernance humaine

Même si l'agent fait tourner la machine, **un humain doit** :

| Tâche | Fréquence | Qui |
|---|---|---|
| Vider la `File_envoi_manuel` (LinkedIn/IG/etc.) | Quotidien | Toi ou un VA |
| Répondre aux prospects intéressés | < 2h (SLA Holdly) | Toi |
| Réviser les drafts ambigus | Quotidien | Toi |
| Valider les nouveaux verticaux/villes à ajouter dans Config | Mensuel | Toi |
| Auditer les métriques (taux réponse / RDV / close) | Hebdo | Toi |
| Faire évoluer les templates qui sous-performent | Hebdo | Toi (peut être assisté par l'agent) |

---

## Mode dégradé (failsafe)

L'agent **arrête** automatiquement si :

- Bounce rate > 3 % sur les dernières 24h → email sender potentiellement compromis.
- Taux de désabonnement > 1 % sur 7 jours → message problématique.
- 2+ plaintes "spam" → revue humaine urgente.
- Erreur d'écriture sur le Sheet → ne pas avancer (préserver l'intégrité de l'état).

Dans tous ces cas → alerte immédiate + pause automatique jusqu'à intervention humaine.

---

## Prochaines itérations (après v1 stable)

Quand le pipeline tourne et qu'on a 4-8 semaines de données :

1. **A/B test** sur les sujets d'email (l'agent peut gérer 2 variantes par template).
2. **Scoring de lead intelligent** : entraîner un mini-modèle sur les réponses passées pour scorer mieux.
3. **Personnalisation vidéo** (Loom court généré pour les top leads).
4. **Intégration calendrier directe** : l'agent négocie un créneau au lieu d'envoyer un lien.
5. **Upsell automatique** post-démo : si la démo passe, séquence dédiée pour l'automatisation marketing ou le custom AI.
```
