# MindTrace - Modifications apportees

## Contexte

Le projet a ete verifie et ameliore pour mieux repondre au brief du challenge CISTAC 1.0 AI4Brain. L'architecture existante a ete conservee : Streamlit pour l'interface, SQLite pour les donnees, Plotly pour les graphiques et Google Gemini pour le coaching.

Les modifications sont non cliniques : MindTrace reste un prototype experimental. Le Cognitive Index n'est pas presente comme une mesure standardisee ni comme un score de QI valide.

## 1. Nettoyage du depot

- `README.md_` a ete renomme en `README.md`.
- `requirements.txt` a ete converti en UTF-8 sans modifier la liste des paquets.
- `app_copy.py`, ancienne copie de l'application, a ete supprime apres verification qu'aucun fichier ne l'importait.
- Une mention a ete ajoutee dans `app.py` pour indiquer qu'aucune donnee biometrique (camera, voix ou visage) n'est collectee.

## 2. Intervalles d'incertitude

Un nouveau module `assessment_logic.py` contient la fonction pure `wilson_interval(correct, total, z=1.96)`.

Cette fonction calcule un intervalle de confiance de Wilson a 95 %, renvoye en pourcentage arrondi. Le cas `total = 0` est gere et renvoie `(0, 0)`.

Dans `app.py` :

- chaque categorie affiche son score et son intervalle, par exemple `67% | 95% CI: 30-90%` ;
- les bornes basse et haute sont conservees dans `category_scores_json` avec `interval_low` et `interval_high` ;
- le radar affiche le score principal ainsi que deux lignes pointillees pour les bornes de l'intervalle ;
- l'interface explique que l'incertitude est elevee lorsque le nombre de questions est faible ;
- les anciens enregistrements restent compatibles grace a l'utilisation de valeurs par defaut avec `.get()`.

## 3. Heatmap du Brain Twin

Dans `2_Brain_Twin.py`, une heatmap Plotly montre les scores des categories selon les tentatives.

La heatmap :

- affiche les categories en lignes ;
- affiche les tentatives en colonnes ;
- utilise une echelle de couleur de 0 a 100 % ;
- gere une seule tentative ;
- gere les categories absentes d'anciens enregistrements en affichant une cellule vide ;
- accepte les anciens scores numeriques et les nouveaux scores stockes dans des dictionnaires ;
- contient une legende de couleur et un titre explicite.

## 4. Consentement, export et suppression des donnees

Dans `auth_ui.py`, la creation de compte demande maintenant un consentement obligatoire. Le texte explique que MindTrace stocke :

- les scores ;
- les temps de reponse ;
- l'historique des evaluations.

Le consentement precise aussi que seuls les scores et les erreurs, jamais le nom ou le mot de passe, sont envoyes a Gemini, et que le compte peut etre supprime a tout moment.

Dans `2_Brain_Twin.py`, la section `My data` permet :

- d'exporter l'historique complet au format JSON ;
- de confirmer puis supprimer le compte et toutes les evaluations associees.

La suppression utilise la fonction SQLite existante `delete_user`, puis vide la session Streamlit et revient a l'ecran de connexion.

## 5. Rapport de secours sans IA

Dans `app.py`, si les trois modeles Gemini echouent, l'application genere maintenant un rapport local base sur des regles.

Le rapport de secours contient les memes grandes sections que le rapport IA :

1. performance globale ;
2. points forts ;
3. categories a pratiquer ;
4. progression ;
5. trois exercices cibles ;
6. plan pour la prochaine session ;
7. conclusion motivante.

Il inclut la mention `Report generated without AI (service unavailable)` et n'effectue aucun appel reseau supplementaire.

## 6. Fiabilite et logique pure

Les fonctions suivantes ont ete extraites dans `assessment_logic.py` :

- `next_difficulty` : monte ou descend d'un niveau selon la reponse, sans depasser `Moderate` ou `Challenging` ;
- `category_summary` : calcule les scores, les temps moyens et les intervalles par categorie ;
- `processing_speed_score` : combine precision et rapidite.

Le score affiche de `Processing Speed` combine :

- 70 % de precision ;
- 30 % de rapidite.

La rapidite est normalisee avec les seuils suivants : 100 % a 5 secondes ou moins par question, 0 % a 30 secondes ou plus.

Le prompt du coach ne retire plus automatiquement la derniere tentative. Il exclut uniquement l'evaluation courante quand son `run_id` est disponible dans `st.session_state["assessment_saved_run_id"]`. Si la sauvegarde a echoue, tout l'historique est conserve.

## 7. Tests ajoutes

`test_logic.py` verifie :

- la montee de difficulte ;
- la descente de difficulte ;
- le plafond de difficulte ;
- le cas Wilson avec `total = 0`.

## 8. Compte de demonstration

`seed_demo.py` cree ou reutilise le compte suivant :

- utilisateur : `demo_user` ;
- mot de passe : `MindTrace-Demo-2026!`.

Le script genere six evaluations reparties sur plusieurs jours, avec des scores progressifs dans les six categories. Il est idempotent : une seconde execution ne cree pas de doublons et reutilise le compte existant.

## 9. Validation realisee

Les commandes suivantes ont ete executees avec succes :

```text
py test_logic.py
py test_brain_twin_db.py
py -m py_compile app.py auth_ui.py brain_twin_db.py assessment_logic.py 2_Brain_Twin.py pages/1_Daily_Games.py seed_demo.py test_logic.py
py seed_demo.py
```

`seed_demo.py` a ete execute deux fois. La premiere execution a cree les six evaluations et la seconde a confirme qu'aucun doublon n'etait ajoute.

## 10. Limites de validation

`test_ai.py` n'a pas pu etre execute dans l'environnement utilise car le module `streamlit` n'y etait pas installe. Les diagnostics d'import de Streamlit, Plotly et Gemini reflettaient la meme absence de dependances dans cet environnement.

Pour une validation complete, installer les paquets avec :

```text
py -m pip install -r requirements.txt
```

Puis lancer l'application avec :

```text
streamlit run app.py
```

## Fichiers principaux concernes

- `app.py`
- `auth_ui.py`
- `brain_twin_db.py`
- `2_Brain_Twin.py`
- `assessment_logic.py`
- `test_logic.py`
- `seed_demo.py`
- `README.md`
- `requirements.txt`
