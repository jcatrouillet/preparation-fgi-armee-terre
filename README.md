# Préparation à la FGI (Formation Générale Initiale) de l'Armée de Terre

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
- **Véhicules** : trois types de quiz — **Photo → Nom** (5 noms), **Nom → Photo** (4 photos) et **Mixte** (alternance des deux) ; les mauvaises réponses sont prises en priorité dans la même catégorie. À la réponse, le nom complet et le crédit de la photo sont affichés. Un mode **apprentissage** présente les 21 véhicules en fiches cliquables ; chaque fiche plein écran donne la date de mise en service, la vitesse, le poids, l'équipage / les passagers, l'armement (type et calibre), l'autonomie, les missions principales, un **conseil pour le reconnaître** ou le distinguer d'un véhicule voisin, et le crédit de la photo.
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

### Architecture

- `server.py` tourne via le **Planificateur de tâches** DSM (déclencheur « Au démarrage »), commande :
  `cd /volume1/.../Grades && GRADES_HOST=127.0.0.1 python3 server.py 8123`
- **Portail de connexion → Proxy inversé** : `grade.catrouillet.net:80` → `localhost:8123`. Python sert la page **et** `/api/scores`.
- N'utilisez **pas** Web Station pour héberger la page en statique (l'API répondrait 404).
- `scores.json` est créé à côté de `server.py` ; il doit être accessible en écriture par l'utilisateur de la tâche.

### Mettre à jour le jeu

Images, photos et questions sont embarquées dans `index.html` : seuls deux fichiers sont à envoyer, dans le dossier du jeu sur le NAS.

| Fichier | À envoyer |
|---|---|
| `index.html` | **Toujours** (contenu, photos, questions, interface). |
| `server.py` | Uniquement si sa logique change (ex. ajout du jeu `vehicules` et de son classement). |
| `Vehicules/`, `vehicules.json`, `build_vehicules.py`, `culture.json`, `*.png`, `*.txt` | **Jamais** (sources, utiles seulement en local). |
| `scores.json` | **Ne pas écraser** : c'est le classement en direct. |

1. En local : `python build_vehicules.py` si les photos ont changé, puis vérifier le jeu sur `http://localhost:8123`.
2. Copier `index.html` (et `server.py` si modifié) sur le NAS, par File Station ou SMB.
3. Si `server.py` a changé : DSM → Planificateur de tâches → sélectionner la tâche → **Exécuter** après l'avoir arrêtée (Python ne recharge pas le code seul). Si seul `index.html` a changé, aucun redémarrage n'est nécessaire.
4. Vérifier : `http://grade.catrouillet.net` (Ctrl+F5 pour vider le cache), puis jouer une partie Véhicules et contrôler que le score apparaît dans le classement.

En cas de problème, en SSH sur le NAS : `curl -i http://127.0.0.1:8123/api/scores`. `server.py` affiche ses erreurs dans la console et renvoie un 500 avec un champ `detail`.

> Version actuelle (quiz Véhicules) : `server.py` **doit** être mis à jour, sinon les scores Véhicules sont enregistrés comme des scores Grades.

## Crédits

- Galons : © A. Klopfenstein / armée de Terre / Défense — à titre indicatif, usage d'entraînement.
- Caractéristiques des véhicules (`info` dans `vehicules.json`) : [ministère des Armées](https://www.defense.gouv.fr/terre/nos-materiels/nos-equipements-terre/vehicules-larmee-terre) et Wikipédia (dates de mise en service, matériels absents du site officiel). Valeurs indicatives : elles varient selon les versions.
- Photos de véhicules : [Wikimedia Commons](https://commons.wikimedia.org/), sous licences libres (CC0, domaine public, Licence Ouverte, CC BY, CC BY-SA). L'auteur, la licence et le lien de chaque photo figurent dans `vehicules.json` et sont affichés dans le jeu. Les images sont des versions redimensionnées ; celles sous CC BY-SA restent sous CC BY-SA.
