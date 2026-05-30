# 02 — Schéma du Google Sheet

Un seul fichier Google Sheet, 5 onglets. Sert de CRM léger pour l'opération entière.

> **Pourquoi Google Sheet et pas HubSpot/Airtable** : friction zéro, l'agent peut lire/écrire via l'API en 5 min, et tu vois tout d'un coup d'œil. Migration possible plus tard.

---

## Onglet 1 — `Prospects`

La table principale. Une ligne = un prospect.

| Colonne | Type | Exemple | Note |
|---|---|---|---|
| `id` | string | `P-00042` | Auto-incrémenté, format `P-NNNNN` |
| `date_ajout` | date | `2026-05-30` | Auto |
| `source` | enum | `linkedin` / `ig` / `google_maps` / `kijiji` / `referral` | D'où l'agent l'a trouvé |
| `vertical` | enum | `clinique` / `salon` / `immo` / `resto` / `services_pro` | Voir 01-strategy |
| `entreprise` | string | `Clinique Dentaire Plateau` | |
| `site_web` | url | `https://...` | |
| `ville` | string | `Montréal` | |
| `province` | string | `QC` | |
| `langue` | enum | `fr` / `en` / `bilingue` | Détermine quelle langue de template utiliser |
| `taille_estimee` | string | `5-10` | Employés |
| `decideur_nom` | string | `Marie Tremblay` | Nom du contact ciblé |
| `decideur_role` | string | `Propriétaire` | Owner, Manager, Directeur, etc. |
| `decideur_linkedin` | url | `https://linkedin.com/in/...` | Si trouvé |
| `decideur_email` | string | `marie@...` | Si trouvé |
| `decideur_telephone` | string | `+1-514-...` | Format E.164 |
| `instagram` | string | `@cliniqueplateau` | |
| `facebook` | string | `facebook.com/...` | |
| `tiktok` | string | `@...` | |
| `signal_fit` | text | `Avis Google mentionne "difficile à joindre" (×3 derniers mois)` | Pourquoi c'est un bon prospect — utilisé dans le message |
| `score_fit` | int 1-5 | `4` | 5 = parfait, 1 = douteux |
| `statut` | enum | voir machine d'états ↓ | |
| `canal_actuel` | enum | `email` / `linkedin` / `ig` / `fb` / `tiktok` / `kijiji` | Canal de la dernière touche |
| `date_dernier_contact` | date | `2026-05-28` | |
| `date_prochaine_action` | date | `2026-06-04` | **L'agent lit cette colonne pour planifier la journée** |
| `nb_touches` | int | `2` | Combien de fois contacté |
| `notes` | text | | Champ libre |
| `exclusion` | bool | `FALSE` | Mettre à `TRUE` pour ne plus jamais contacter |

### Machine d'états (`statut`)

```
nouveau
   │
   ▼
contacté_1 ──► répondu_intéressé ──► rdv_booké ──► démo_faite ──► client / perdu
   │                │
   ▼                ▼
contacté_2     répondu_pas_intéressé ──► exclusion=TRUE
   │
   ▼
contacté_3
   │
   ▼
silence ──► exclusion=TRUE (après 4 touches sans réponse)
```

---

## Onglet 2 — `File_envoi_manuel`

Tout ce qui n'est pas l'email automatique passe ici. C'est la **file que toi (ou un VA) traites chaque matin** : copier-coller-envoyer.

| Colonne | Type | Note |
|---|---|---|
| `id_prospect` | ref | Lien vers `Prospects.id` |
| `canal` | enum | `linkedin` / `ig` / `fb` / `tiktok` / `kijiji` |
| `url_profil` | url | Lien direct pour gagner du temps |
| `message_prêt` | text | Message complet à copier-coller |
| `priorité` | int 1-3 | 1 = envoyer aujourd'hui |
| `généré_le` | datetime | |
| `envoyé` | bool | À cocher manuellement après envoi |
| `envoyé_le` | date | |

---

## Onglet 3 — `Email_log`

Log des emails envoyés automatiquement (la conformité LCAP exige un registre).

| Colonne | Note |
|---|---|
| `id_prospect` | |
| `email` | destinataire |
| `sujet` | |
| `corps` | message complet |
| `type` | `initial` / `relance_1` / `relance_2` / `relance_3` / `breakup` |
| `envoyé_le` | datetime |
| `ouvert_le` | datetime (via tracking pixel si activé) |
| `cliqué_le` | datetime |
| `répondu_le` | datetime |
| `desabonné_le` | datetime |
| `bounce` | bool |

---

## Onglet 4 — `Config`

Paramètres globaux. L'agent lit cet onglet au démarrage.

| Clé | Valeur |
|---|---|
| `verticaux_actifs` | `clinique,salon,immo` |
| `villes_cibles` | `Montréal,Laval,Longueuil,Québec,Gatineau` |
| `volume_email_jour` | `30` |
| `volume_manuel_jour` | `15` |
| `email_sender` | `outreach@holdly.pro` |
| `calendrier_url` | `https://cal.com/holdly/strategy` |
| `langue_defaut` | `fr` |
| `signature_fr` | `— L'équipe Holdly · holdly.co · Montréal` |
| `signature_en` | `— The Holdly Team · holdly.co · Montreal` |

---

## Onglet 5 — `Exclusion`

Liste noire. L'agent vérifie ici avant chaque ajout dans `Prospects`.

| Colonne |
|---|
| `entreprise` |
| `email` |
| `domaine` |
| `raison` (`client_actuel` / `desabonné` / `concurrent` / `demande_explicite`) |
| `date` |

---

## Vues recommandées (filtres)

Crée ces vues dans Google Sheet (Données → Créer un filtre) :

- **À contacter aujourd'hui** : `date_prochaine_action <= TODAY()` AND `statut != client/perdu/exclusion`
- **Réponses à traiter** : `statut = répondu_intéressé`
- **RDV à venir** : `statut = rdv_booké` AND date dans `notes` >= TODAY
- **Métriques semaine** : pivot par `source` / `statut`

---

## Template prêt à copier

Pour créer le Sheet rapidement :

1. Nouveau Google Sheet vide → renommer "Holdly Outreach CRM".
2. Créer les 5 onglets avec les noms exacts ci-dessus.
3. Coller les en-têtes (colonne par colonne) de chaque tableau.
4. Partager avec l'email du service account de l'agent (`[À CONFIRMER]`).
5. Copier l'ID du Sheet → l'agent l'utilisera comme cible.
