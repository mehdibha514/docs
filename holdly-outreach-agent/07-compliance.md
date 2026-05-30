# 07 — Conformité (LCAP, PIPEDA, ToS)

Le plus important : on est au Canada, donc **LCAP s'applique** et elle a des dents (jusqu'à 10M $ d'amende pour une entreprise, 1M $ pour un individu).

---

## LCAP — Loi canadienne anti-pourriel

S'applique à tout **message électronique commercial** (MEC) envoyé à une adresse au Canada : email, SMS, DM sur réseau social.

### Les 3 exigences cumulatives

#### 1. Consentement

Deux types valides :

- **Exprès** : la personne a explicitement opt-in (case cochée, formulaire). Le must pour Holdly à long terme — bâtir une liste opt-in via le site.
- **Tacite** : valable seulement si :
  - Vous avez eu une **relation d'affaires existante** (achat, contrat, demande d'info) dans les **2 dernières années**, OU
  - L'adresse est **publiée publiquement** (sur le site web de l'entreprise, sans mention "ne pas envoyer de pourriel"), ET le message est **pertinent au rôle** de la personne.

> **Notre cas (cold outreach B2B)** : on s'appuie sur la **2e branche du consentement tacite** — l'email du propriétaire est publié sur son site, et notre offre est pertinente à son rôle (propriétaire = décide des outils business).
> Limite : il faut que l'email soit **vraiment** publié (pas trouvé via deviner-pattern), et que le message soit **pertinent au rôle**.

#### 2. Identification claire

Chaque message doit contenir :

- Le nom de l'expéditeur (Holdly)
- L'adresse postale physique
- Un moyen de joindre Holdly (téléphone OU email OU site web)

#### 3. Mécanisme de désabonnement

- Fonctionnel dans **chaque** message
- Doit fonctionner pour **60 jours** après envoi
- Traité dans **10 jours ouvrables**

### Checklist par message

- [ ] Identité Holdly visible (signature + nom légal)
- [ ] Adresse postale au pied de page
- [ ] Lien de désabonnement fonctionnel
- [ ] Email du décideur **vérifié comme publié publiquement** (pas pattern-guessing aveugle)
- [ ] Pertinence au rôle clair (on parle bien à un.e propriétaire/décideur de l'offre business)

### À NE PAS faire

- Acheter des listes d'emails (pas de consentement → violation)
- Envoyer à des `info@`, `contact@` génériques en masse (gris : pertinence au rôle faible)
- Ignorer un désabonnement (violation directe)
- Réutiliser un email après désabonnement (même offre, même expéditeur = violation)

---

## PIPEDA — Loi sur la protection des renseignements personnels

S'applique aux **renseignements personnels** qu'on collecte sur les prospects (nom, email, téléphone, etc.).

### Obligations

- **Finalité claire** : on collecte pour prospection commerciale B2B. Documenté.
- **Données minimales** : ne collecter que ce qui sert la prospection.
- **Sécurité** : le Google Sheet doit être en accès restreint (pas public, pas partagé large).
- **Conservation limitée** : purger les prospects perdus/exclus après **24 mois** d'inactivité.
- **Droit d'accès** : si une personne demande "quelles données avez-vous sur moi ?", on doit pouvoir répondre.

### Implémentation

- Sheet partagé uniquement avec : équipe Holdly + service account de l'agent.
- Onglet `Exclusion` conservé indéfiniment (preuve de respect du désabonnement).
- Onglet `Email_log` conservé 3 ans (preuve de conformité LCAP en cas d'audit du CRTC).
- Tout autre prospect inactif > 24 mois → archivé/supprimé.

---

## Conditions d'utilisation des plateformes

### Email (Resend / SendGrid / etc.)

- Domaine d'envoi authentifié (SPF, DKIM, DMARC) — obligatoire pour la délivrabilité.
- Réputation à protéger : warm-up du domaine pendant 2-4 semaines avant de pousser le volume.
- Bounce rate < 2 %, complaint rate < 0.1 %.

### LinkedIn

- **Pas de scraping automatisé** (Terms 8.2, et `hiQ v. LinkedIn` a confirmé le droit de LinkedIn de bloquer).
- **Pas d'outils tiers d'envoi automatisé** (Dux-Soup, Phantombuster côté envoi, etc.) → comptes bannis.
- Cap manuel : 15-20 connexions/jour, 15-20 messages/jour par compte humain.
- Notes de connexion < 300 caractères.

### Meta (Instagram & Facebook)

- DM automation par bot → ban quasi-garanti, et possible action légale.
- L'API Messenger officielle existe mais réservée à **l'inbound** (24h customer service window après qu'un user a écrit en premier) — pas applicable à l'outreach à froid.
- Cap manuel : 10-15 DMs/jour par compte.

### TikTok

- Pas d'API DM publique.
- Automation = ToS violation.
- Cap manuel : 5-10 DMs/jour.

### Kijiji

- ToS interdit le scraping et le messaging automatisé.
- Réponses manuelles uniquement, à des annonces réelles.

---

## Avis Google et données publiques

Lecture des avis Google publics pour la qualification → **OK** (données publiques). Mais :

- Ne pas stocker l'avis tel quel dans le Sheet ; stocker uniquement le **signal extrait** ("3 avis mentionnent attente téléphone").
- Ne pas citer un avis nominatif dans un message au prospect (gênant + atteinte potentielle à la réputation).

---

## En cas de plainte

Si un prospect répond mécontent ("c'est du spam", "comment vous avez eu mon email") :

1. **Réponse humaine dans les 24h** — pas un template, une vraie excuse + explication.
2. Ajout immédiat dans `Exclusion`.
3. Si menace de plainte CRTC → escalade interne, documenter tout l'historique.

---

## Pour aller plus loin

- LCAP : https://crtc.gc.ca/fra/internet/anti.htm
- PIPEDA : https://www.priv.gc.ca/fr/sujets-lies-a-la-protection-de-la-vie-privee/lois-sur-la-protection-des-renseignements-personnels-au-canada/
- LinkedIn User Agreement : https://www.linkedin.com/legal/user-agreement
- Meta Platform Terms : https://developers.facebook.com/terms/

> **Ne pas considérer ce document comme un avis juridique.** Pour un déploiement à grande échelle, faire valider par un avocat spécialisé en droit numérique au Québec.
