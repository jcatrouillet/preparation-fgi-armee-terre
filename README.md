# Grades de l'armée de Terre française — Jeu d'apprentissage

Jeu web pour apprendre et réviser :

- **🎖️ Grades** — reconnaître les galons de l'armée de Terre française (officiers généraux, officiers, sous-officiers, militaires du rang, et un jeu « Chasseurs »).
- **📚 Culture générale** — QCM de culture générale française (histoire, géographie, institutions, fleuves…).
- **⚔️ Culture militaire** — QCM de culture militaire.
- **🚙 Véhicules** — reconnaître les véhicules de l'armée de Terre (blindés, artillerie, hélicoptères, camions…) à partir d'une photo.

En ligne : **http://grade.catrouillet.net**

## Fonctionnalités

- **Grades** : quiz Galon → Nom, Nom → Galon ou mixte, plus un mode **apprentissage** (fiches cliquables en plein écran).
- **Culture** : QCM à 5 choix.
- **Chrono** optionnel (10 / 5 / 3 s par question).
- **Véhicules** : photo → nom parmi 5 choix (mauvaises réponses prises en priorité dans la même catégorie) ; à la réponse, le nom complet et le crédit de la photo sont affichés.
- **Meilleurs scores** : trois classements Top 20 séparés (**Grades**, **Culture** et **Véhicules**), stockés côté serveur.
- Interface responsive (ordinateur / tablette / mobile).
- `index.html` est **autonome** : CSS, JS, images (base64) et questions y sont embarqués — il fonctionne même ouvert directement dans un navigateur.

## Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `index.html` | Le jeu complet (autonome), images et questions embarquées. |
| `server.py` | Serveur Python (bibliothèque standard) : sert la page **et** l'API des scores. |
| `culture.json` | Source des questions de culture (générale + militaire). Ré-injectée dans `index.html`. |
| `Questions culture *.txt` | Sources brutes des questions. |
| `Vehicules/`, `vehicules.json` | Photos des véhicules et leur fiche (nom, catégorie, auteur, licence, lien source). |
| `build_vehicules.py` | Compresse les photos et les injecte dans `index.html` (`python build_vehicules.py`, nécessite Pillow). |
| `*.jpg`, `*.png` | Images des galons (sources). |

> `scores.json` (le classement en direct) n'est pas versionné — il est créé par le serveur à l'exécution.

## Lancer localement

```sh
python server.py            # http://localhost:8123 (accès local uniquement)
python server.py 9000       # port personnalisé
GRADES_HOST=0.0.0.0 python server.py 8123   # exposer sur le réseau
```

Puis ouvrir l'URL affichée. Aucune dépendance externe (Python 3.7+).

### API des scores

- `GET /api/scores` → liste JSON du Top 20 par catégorie.
- `POST /api/scores` `{name, score, total, timer, game}` → enregistre un score.

Le serveur **recalcule** le pourcentage à partir de `score/total` et rejette les valeurs impossibles.

## Déploiement (Synology NAS)

`server.py` tourne via le planificateur de tâches ; un reverse proxy DSM redirige `grade.catrouillet.net` vers le port du serveur. Comme images et questions sont embarquées, il suffit de recopier `index.html` (et `server.py` si sa logique change).

## Crédits

- Galons : © A. Klopfenstein / armée de Terre / Défense — à titre indicatif, usage d'entraînement.
- Photos de véhicules : [Wikimedia Commons](https://commons.wikimedia.org/), sous licences libres (CC0, domaine public, Licence Ouverte, CC BY, CC BY-SA). L'auteur, la licence et le lien de chaque photo figurent dans `vehicules.json` et sont affichés dans le jeu. Les images sont des versions redimensionnées ; celles sous CC BY-SA restent sous CC BY-SA.
