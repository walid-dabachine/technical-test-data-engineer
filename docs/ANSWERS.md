<!-- Inscrivez vos réponses dans ce document -->

## ⚙ Instructions d'installation du projet

1. S'assurer que Python est bien installé sur la machine. Ce projet est compatible avec python `>=3.9, <=3.13`. Il a été testé en Python 3.10

2. Créer un environement virtuel nommé `venv` :
    ```shell
    python -m venv venv
    ```

3. Lancer l'environement virtuel :
    ```shell
    source venv/bin/activate
    ```

4. Installer `poetry` pour la gestion des dépendances du projet :
    ```shell
    pip install poetry && pip install --upgrade pip
    ```

5. Lancer l'installation du projet via `poetry` :
    ```shell
    poetry install
    ````

6. A ce stade, le projet est installé et prêt à être lancé. Commençons par lancer la suite de tests via `pytest` pour s'assurer que tout fonctionne : 
    ```shell
    pytest -rA
    ```
    Un total de 5 tests unitaires doivent passer avec succès

## ⚡ Lancement de l'extraction des données

1. S'ouvrir un terminal en arrière fond en s'assurant de bien être à la racine du projet `technical-test-data-engineer` et en activant l'environement virtuel, puis lancer le serveur API Moovitamix localement : 
    ```shell
    python -m uvicorn src.moovitamix_fastapi.main:app --reload
    ```

2. S'ouvrir à présent un nouveau terminal de travail, toujours à la racine du projet `technical-test-data-engineer` et lancer la pipeline d'ingestion, dans un premier temps, sans le module d'orchestration : 
    ```shell
    python src/moovitamix_data_connector/main.py --scheduling no
    ```
    La pipeline va lancer 3 flux d'ingestions: `tracks`, `users` et `listen_history`. Une fois l'exécution terminée, les données seront sauvegardées dans le dossier `data/01_source`

3. Pour activer le module d'orchestration `prefect` : 

    - S'assurer que `prefect` est bien installé en roulant la commande suivante :
        ```shell
        prefect version
        ```
    - Ouvrir un nouveau terminal en arrière fond pour lancer le serveur localement :
        ```shell
        prefect server start
        ```
        L'adresse du dashboard local s'affiche, normalement `http://127.0.0.1:4200`
    - Ouvrir un nouveau terminal de travail pour lancer la pipeline d'ingestion avec le module d'orchestration
        ```shell
        python src/moovitamix_data_connector/main.py --scheduling yes
        ```
    - Se rendre sur le dashboard à l'adresse affichée précedemment pour suivre le lancement des runs à chaque minute et leur état. Pour l'instant le projet n'implémente pas de méthodologie de versioning, les données sont donc extraites et écrasées à chaque minute sous `src/01_source`.

## 📖 Description des choix techniques du projet

Globalement, le projet se découpe en X thématiques techniques :

1. Setup du projet
2. Connecteur API Moovitamix
3. Modèle de données
4. Orchestration

Nous allons en explorer les choix, remarques et prochaines étapes.

### 1. Setup du projet

- Toutes les composantes sont codées en Python pour faciliter la collaboration avec l'équipe Data Science qui travaille principalement avec ce language. L'utilisation du SQL notamment pour le module de transformation de données est également une option valide à explorer

- J'ai utilisé `poetry` pour la gestion des dépendances du projet. Sa capacité à résoudre les dépendances automatiquement, centraliser en un seul fichier les configurations de dév et de prod, centraliser les commandes de build ainsi qu'encapsuler la gestion des dépendances et de l'environement virtuel en font un outil très robuste en comparaison à une utilisation manuelle de `pip`

- Le projet est découpé en 3 modules techniques sous `src` :
    1. `moovitamix_fastapi` : Module de création de l'API (fourni par MoovAI)
    2. `moovitamix_data_connector` : Connecteur de données visant à extraire les données `source` de l'API Moovitamix
    3. `data_transformation` : Module responsable de la création des pipelines de transformation de données de la couche `source` à la couche `mart`

### 2. Connecteur API Moovitamix

- Le connecteur se trouve dans `src/moovitamix_data_connector.py`

- J'ai fait le choix de le coder from scratch bien que d'autres options sur étagère et beaucoup plus robustes existent afin d'éviter de réinventer la roue :
    * Créer un connecteur `Airbyte`
    * Créer un connecteur `Kedro`
    
    Cela s'explique notamment par 2 raisons:
    
    1. un manque de temps pour rentrer dans la doc de ses solutions respectives qui offrent un template prêt à l'usage pour créer des connecteurs personnalisées mais nécessite d'adhérer à leur modèle de données pour en tirer profit
    
    2. Les connecteurs génériques de type API HTTP de ces 2 solutions n'offrent pas la gestion de la pagination et/ou de gestion du retry en cas de dépassement de la limite de l'API

- Le connecteur gère la pagination de l'API

- Le connecteur gère pour l'instant uniquement les erreurs de type 429 (rate limit error)

- Le connecteur implémente un mechanisme de validation de données à l'aide de `Pydantic`. Qui implémente pour l'instant exclusivement la validation du typage. Une des petites limitations de Pydantic ici est le fait qu'il n'offre pas de solution DataFrame-like permettant d'évaluer la validité des données au niveau du Dataframe Pandas lors du runtime. Une solution comme `pandera` pourrait être une bonne alternative pour améliorer cela pour étendre, simplifier et robustifier le scope de la validation

- Prochaines étapes:
    * Présentemment, le connecteur se réalise systématiquement une extraction de données en mode "full load". Cela n'est pas très performant ici car pour ce type de données on peut s'imaginer que la volumétrie peut très vite grossir ce qui rendra une extraction de type incrémentale beaucoup plus performante du point de vue du cout et du temps. On devra donc réfléchir à l'avenir à l'implémentation d'une telle feature
    * Explorer l'éventualité d'adhérer à un framework offrant des connecteurs sur-étagère beacoup plus robuste afin d'éviter de réinventer la roue
    * Etendre la gestion des erreurs à plus de code HTML pour le rendre plus robuste

### 3. Modèle de données

#### 3.1 Structuration du pipeline de transformation de données

J'ai tiré mon modèle de données des best practices provenant des frameworks open source utilisés par la communauté, notamment [dbt](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview). La donnée passe par 3 couches de transformation:

1. Source: Donnée brute sans transformation
2. Staging: Couche où sont appliquées les transformations de base de notre modèle de données (ex: casting, cleaning, ...)
3. Mart: Couche où se trouve les modèles de données utilisés par le business, l'équipe Data Science. Ils définissent l'unique source of truth qui permet d'alimenter l'ensemble des cas d'usage analytiques plus bas dans le pipeline (ex: on y définit ce qu'est un utilisateur, ce qu'est un track, ...)

Par manque de temps, j'ai eu la possibilité d'explorer uniquement la couche source qui est la couche où les données extraites par le connecteur API atterissent. Si demain on décide d'intégrer une nouvelle source de données comme une base de données SQL, c'est dans cette couche qu'atterisseront aussi les tables de cette BD.

Pour cet exercice, il n'y a pas énormément de transformation à appliquer sur les données, les modèles développés dans ces différentes couches auraient été légers. Si j'avais eu davantage de temps j'aurais utilisé `Kedro` pour réaliser ces transformations. Sa solution de pipelining et de visualisation des jobs de transformation de données le rend très efficace.

#### 3.2 Structuration du modèle de données

Etant donnée la nature du problème, j'ai opté pour une modélisation en étoile (star schema) avec les composantes suivantes:

* `tracks` : table de dimension
* `users` : tables de dimension
* `listen_history` : table de fait

plus d'info dans les [best bractices dbt](https://docs.getdbt.com/terms/dimensional-modeling)

### 4. Orchestration

- J'ai utilisé `Prefect` car moins verbeux qu'une solution comme `Airflow`. Avec le peu de temps que j'ai, j'ai préféré opté pour cette solution pour implémenter rapidement une soltuion d'orchestration. L'inconvénient d'une solution comme `Prefect` est sa maturité relativement faible en comparaison à `Airflow` qui est la solution la plus populaire dans l'écosystème Python.

- Ma solution n'implémente pas pour l'instant de versioning, à chaque run du job les données fraiches viendront écrasées les anciennes données. Si j'avais plus de temps j'aurais d'abord commencé par analyser les différentes options à ma disposition pour implémenter ce versioning. Cela peut passer par différentes options comme:
    - un format de données qui gère by design les versions (ex: delta lake qui est du parquet sous stéroide)
    - une structure de fichier/dossier qui conserve la tracabilité (ex: un dossier par date, avec un dossier `latest` contenant en tout temps la version la plus à jour des données)