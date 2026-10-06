# 🎙️ Studio Podcast

Outil **local** de gestion de podcast. Tout tourne sur votre ordinateur : aucune
inscription, aucune dépendance à installer, vos données restent chez vous.

## Fonctionnalités

- **Tableau de bord** : épisodes publiés / en production / idées, prochains
  enregistrements et publications, tâches en retard.
- **Épisodes** : tableau Kanban (Idée → Préparation → Enregistré → Montage →
  Planifié → Publié) avec glisser-déposer, ou vue liste avec recherche.
  Chaque épisode a : saison, numéro, dates d'enregistrement et de publication,
  durée, invités, tags, description publique, notes privées (script, questions),
  fichier audio (avec lecteur), visuel, et une checklist de production.
- **Calendrier éditorial** : vue mensuelle des enregistrements 🎙️, publications 📢
  et échéances de tâches.
- **Invités** : carnet de contacts avec statut (à contacter, contacté, confirmé…),
  bio, sujet proposé et épisodes associés.
- **Tâches** : to-do avec échéance, reliée ou non à un épisode.
- **Flux RSS** compatible Apple Podcasts / Spotify, généré automatiquement à
  `http://localhost:3000/rss.xml` à partir des épisodes publiés avec audio.
- **Sauvegarde** : export / import de toutes les données en JSON.

## Démarrage

Prérequis : [Node.js](https://nodejs.org) 18 ou plus récent (rien d'autre).

- **Windows** : double-cliquez sur `demarrer.bat`
- **macOS / Linux** : `./demarrer.sh`
- ou dans un terminal : `npm start` (ou `node server.js`)

Puis ouvrez <http://localhost:3000>.

Options (variables d'environnement) : `PORT` (défaut 3000), `HOST`
(défaut `127.0.0.1`, accessible uniquement depuis votre machine ; mettez
`0.0.0.0` pour l'ouvrir au réseau local), `DATA_DIR` (défaut `./data`).

## Données

- `data/db.json` : épisodes, invités, tâches, paramètres
- `data/uploads/` : fichiers audio et images envoyés

Le dossier `data/` est ignoré par git. Pensez à le sauvegarder (ou à utiliser
l'export depuis **Paramètres**).

## Publier le flux RSS

Le flux pointe vers l'« URL publique » définie dans **Paramètres**. En local, il
ne sert qu'à vérifier le rendu ; pour le soumettre à Apple Podcasts ou Spotify,
il faut que le serveur (ou au moins les fichiers audio) soit accessible sur
internet. Vous pouvez aussi indiquer des URL `https://…` d'un hébergeur dans les
champs audio.
