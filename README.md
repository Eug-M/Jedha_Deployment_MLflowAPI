# Projet Deployment Jedha

## Structure des dossiers

Les sources sont organisés de la manière suivante :
 - *root* :
   - *.gitignore* : configuration Git
   - *Projet_01-Getaround_analysis_vF.ipynb* : Notebook d'exploration des données et de run du modèle prédictif (contient les consignes Jedha du projet)
   - *README.md* : documentation générale du projet 
   - *requirements.txt* : dépendances nécessaires à l'exécution du projet en local
 - *API_predict* : image Docker, dépendances de l'API, scripts d'exécution et documentation
   - *src* : sources de l'API
 - *Streamlit_app* : image Docker, dépendances de l'application Streamlit, scripts d'exécution et documentation
   - *src* : sources de l'application


## Environnement local

### Prérequis

- python 3.12.x

### Installation

1. Clone de ce github repository :
```
git clone https://github.com/your-username/XXXX.git
```
Attention à bien remplacer *your-username* par votre propre identifiant GitHub

2. Rentrer dans le répertoire du projet :
```
cd XXXX
```

3. Créer un environnement virtuel et l'activer (optionnel mais recommandé) :
```
python -m venv .venv
```
```Windows
.\.venv\Scripts\Activate.ps1
```
```Mac/Linux
source .venv/bin/activate
```

4. Installer les dépendances du projet :
```
pip install -r requirements.txt
```

### Exécution du Dashboard Streamlit avec Docker

1. Rentrer dans le répertoire du Dashboard Streamlit :
```
cd Streamlit_Dashboard
```

2. Lancer localement le Docker contenant l'application Streamlit :
```
docker build . -t image_streamlit
docker run -it -v "$(pwd):/home/app" -p 4000:4000 image_streamlit:latest 
```

Le Dashboard sera disponible localement dans votre navigateur web à cette adresse : *http://localhost:4000*

### Run du serveur MLFlow traçant les modèles prédictifs

1. Créer la base de données AWS

Créer un stockage S3 sur AWS avec les paramètres suivants :
- Nom du compartiment : jedha-mlflow
- Bloquer tous les accès publics : Non (et cocher la confirmation)

Créer une base de données sur AWS avec les paramètres suivants :
- Type de moteur : PostgreSQL
- Modèles : Offre gratuite
- Identifiant d'instance de base de données : jedha-mlflow
- Mot de passe principal : **************
- Accès public : Oui
- Activer l'analyse des performances : Non

2. Déployer le serveur sur HuggingFaceSpaces

- Créer un espace nommé **jedha-mlworkflow** dans HuggingfaceSpaces
- Dans l'onglet *Files*, ajouter les éléments suivants :
  - Dockerfile
  - requirements.txt
- Committer les modifications sur la branche *main* du HuggingfaceSpaces
- Dans l'onglet Settings, ajouter les secrets suivants :
  - DEFAULT_PORT : 7860
  - PORT : 7860
  - AWS_ACCESS_KEY_ID : **************
  - AWS_SECRET_ACCESS_KEY : **************
  - BACKEND_STORE_URI : postgresql://{user}:{password}@{endpoint}:{port}/{database_name}?sslmode=require
  - ARTIFACT_STORE_URI : s3://jedha-final-project
  - MLOPS_SERVER_PORT : 7860
- Accéder à l'onglet *App* et vérifier que l'application ait correctement démarré.

> Le endpoint et le port de la base SQL sont affichés dans l'onglet Connectivité et sécurité de l'instance RDS.

3. Runner des modèles pour alimenter le MLFlow

- Rentrer dans le répertoire du serveur MLFlow :
```
cd ../Predict_API/ml
```

- Créer le fichier *sources.sh* :
bash
export MLFLOW_TRACKING_URI="https://YOUR_OWN-jedha-mlworkflow.hf.space"
export AWS_ACCESS_KEY_ID="TO_REPLACE_WITH_YOUR_OWN"
export AWS_SECRET_ACCESS_KEY="TO_REPLACE_WITH_YOUR_OWN"
export BACKEND_STORE_URI="TO_REPLACE_WITH_YOUR_OWN" 
export ARTIFACT_ROOT="s3://jedha-mlflow"

- Exporter ces variables d'environnement :
```
source secrets.sh
```

- Lancer les expériences après avoir modifié les paramètres (MODEL_NAME & DF_PREPROCESS) dans le fichier train.py :
```
python train.py
```

### Run de l'API de prédiction avec Docker

L'application est déployée sur HuggingfaceSpaces à cette adresse : https://eug-m-jedha-api.hf.space
La documentation est disponible à cette adresse : https://eug-m-jedha-api.hf.space/docs

Procédure de déploiement :

1. Créer un espace nommé **jedha-api** (de type Docker) dans HuggingfaceSpaces

2. Dans l'onglet *Files*, ajouter les éléments suivants :
  - Dockerfile
  - requirements.txt
  - src

3. Committer les modifications sur la branche *main*

4. Dans l'onglet Settings, ajouter les secrets suivants :
  - DEFAULT_PORT : 6001
  - PORT : 6001
  - AWS_ACCESS_KEY_ID : **************
  - AWS_SECRET_ACCESS_KEY : **************
  - MLOPS_SERVER_URI : https://YOUR_OWN-jedha-mlworkflow.hf.space
  - MODEL_PATH : runs:/YOUR_OWN/Getaround_PredictPricing

5. Accéder à l'onglet *App* et vérifier que l'application a correctement démarré.

6. Vous pouvez tester le bon fonctionnement de l'API avec le fichier test.py, en modifiant votre adresse HuggingfaceSpaces
