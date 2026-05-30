# 03 — Recettes de prospection par canal

Comment l'agent trouve, enrichit et qualifie un prospect, canal par canal. Toutes les recettes produisent une ligne dans l'onglet `Prospects`.

---

## A. Google Maps / recherche locale (le moteur principal)

**Pourquoi en premier** : c'est la source la plus fiable pour des PME locales avec téléphone visible. Conforme et scrapable légèrement via Places API.

### Requêtes types

Pour chaque combinaison `(vertical × ville)` listée dans `Config` :

```
"dentiste" Montréal
"clinique esthétique" Laval
"salon de coiffure" Plateau Mont-Royal
"courtier immobilier" Brossard
"restaurant" Outremont
```

### Données à extraire

- Nom de l'entreprise
- Site web
- Téléphone
- Note + nombre d'avis
- Heures d'ouverture (signal : pas de 24/7 = douleur appels manqués potentielle)
- 3-5 derniers avis Google → scanner pour mots-clés : "pas répondu", "appelé plusieurs fois", "attente", "rappel jamais reçu" → **signal de fit fort**

### Score automatique

```
score_fit = 3 (défaut)
+1 si 3+ avis avec signal de douleur dans les 6 derniers mois
+1 si site web pro mais pas de chat / pas de booking en ligne
+1 si présence Instagram/Facebook active
-1 si chaîne / franchise nationale
-1 si < 10 avis Google (trop petit ou trop nouveau)
```

Garder seulement score ≥ 3.

### Enrichissement décideur

Pour chaque entreprise gardée, l'agent cherche le décideur :

1. Site web → page "À propos" / "Équipe" → nom du propriétaire ou directeur.
2. Si non trouvé → recherche LinkedIn : `[nom entreprise] propriétaire OR fondateur OR directeur Montréal`.
3. Si email pas visible publiquement : essayer **pattern** (prénom@domaine, p.tremblay@domaine, etc.) et **valider** avec un service de vérification email (Hunter, NeverBounce, ZeroBounce) — **ne pas deviner sans valider** sinon bounce rate explose.

---

## B. LinkedIn (mode : agent prépare, humain envoie)

### Recherche

L'agent utilise des recherches LinkedIn ciblées (manuel ou via Sales Navigator si tu y as accès) :

```
Filtres :
- Lieu : Grand Montréal / Québec
- Industrie : Soins de santé / Beauté & bien-être / Immobilier / Restauration
- Taille : 1-10 / 11-50 employés
- Titres : Propriétaire / Owner / Fondateur / Directeur général / President
```

### Enrichissement

Pour chaque profil retenu :
- Nom complet
- Rôle exact
- Entreprise + lien
- URL du profil
- **Signal personnalisable** : leur dernier post (sujet + 1 phrase) → utilisé dans le hook du message.

### Limites à respecter (ToS)

- **Pas de scraping automatisé** des profils. Lecture manuelle assistée ou outil officiel uniquement.
- **Pas de connection requests en masse** automatisées.
- **Cap d'envoi** : max 15-20 messages par jour par compte humain qui envoie.

---

## C. Instagram / Facebook (mode : agent prépare, humain envoie)

### Recherche

Par hashtag et géolocalisation :

```
Hashtags QC :
#cliniquedentairemtl #salonmontreal #estheticienne #immobiliermtl
#restomtl #petitebusinessquebec #entrepreneurqc

Géo :
- Page Explorer Instagram → location Montréal / Laval / Québec
- Pages Facebook locales avec catégorie business
```

### Critères de retention

- Profil business (pas perso).
- Bio FR ou bilingue.
- Posts dans les 30 derniers jours (compte actif).
- < 10k followers (sinon trop gros / agence dédiée).
- Visible : nom du propriétaire OU style "founder-led" reconnaissable.

### Enrichissement

- Handle, lien du profil
- Nom du proprio si visible dans la bio ou les posts
- **Signal personnalisable** : dernière story / post (référence dans le message — "j'ai vu ton post sur X")

### Limites à respecter

- **Pas de DM automation**. Période. Meta bannit.
- Cap d'envoi manuel : 10-15 DMs/jour par compte pour ne pas trigger les filtres anti-spam.

---

## D. TikTok (mode : agent prépare, humain envoie)

Volume faible mais conversion intéressante si la personne y est active (= ouverte au numérique).

### Recherche

```
Hashtags : #entrepreneurqc #pmequebec #salondebeautemtl #cliniquemtl
Recherche par lieu : Montréal, Québec
```

### Critères

- Compte business.
- Vidéos régulières (signal : ils ont du temps marketing, donc reconnaissent la valeur du temps).
- < 50k followers.

### Enrichissement

- Handle, lien profil
- 1 vidéo récente (sujet → utilisé en hook)

### Limites

- Pas d'automation possible (pas d'API DM ouverte, et ToS).
- Cap d'envoi : 5-10 DMs/jour.

---

## E. Kijiji (mode : réponse à annonces)

Kijiji est un **canal réactif**, pas proactif : on répond à des annonces de PME qui cherchent des services qu'on peut compléter.

### Catégories à surveiller (Grand Montréal + Québec)

- **Services > Petites entreprises** — souvent : "cherche aide administrative", "VA", "réceptionniste à temps partiel"
- **Services > Soins de santé/beauté** — propriétaires de salons/cliniques qui annoncent
- **Emplois > À pourvoir** — qui cherche un.e réceptionniste à temps plein/partiel = candidat parfait pour Elodie

### Critères

- Annonce postée dans les 14 derniers jours.
- Mention d'embauche d'un poste qu'Elodie remplace (réceptionniste, agent service à la clientèle).
- Coordonnées de contact visibles.

### Action

L'agent prépare une **réponse à l'annonce** (pas un DM générique) :

> "Bonjour, j'ai vu votre annonce pour un.e réceptionniste. Avant d'embaucher, vous voudriez peut-être voir comment d'autres [type business] de Montréal gèrent ça avec une réceptionniste IA bilingue, déployable en 72h, ~10× moins cher qu'un salaire. 15 min de démo gratuite : [calendrier]. Sinon bonne suite avec votre embauche !"

### Limites

- Pas de scraping automatisé (ToS).
- L'agent identifie les annonces manuellement assistées ; toi tu envoies.
- Ne pas spammer Kijiji (filtres internes agressifs).

---

## F. Référencement croisé (la pépite)

Avant de toucher quelqu'un de nouveau, l'agent vérifie :

1. Est-il dans l'onglet `Exclusion` ? → skip
2. A-t-il un partenariat / fournisseur commun avec un client actuel ? → mention dans le message ("vu via [client]")
3. Sa ville/vertical a-t-il déjà eu des leads similaires ? → adapter le message

---

## Volume quotidien attendu (par défaut)

| Source | Nouveaux prospects/jour | Temps agent |
|---|---|---|
| Google Maps | 20-30 | 30 min |
| LinkedIn | 10-15 | 20 min |
| IG / FB | 10-15 | 20 min |
| TikTok | 3-5 | 10 min |
| Kijiji | 2-5 | 10 min |
| **Total** | **~45-70** | **~90 min** |

Ajustable via `Config.volume_*_jour`.
