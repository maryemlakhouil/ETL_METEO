# 🌦️ ETL Météo — Analyse des risques pour les livraisons au Maroc

## 1. Présentation du projet

### Contexte

Une entreprise de livraison et de logistique opère dans plusieurs villes marocaines. Les conditions météorologiques peuvent perturber les opérations de livraison, notamment en cas de fortes précipitations, de vents importants ou de températures extrêmes.

L'objectif de ce projet est de construire une solution de données permettant de récupérer les prévisions météorologiques, de transformer les données brutes en informations exploitables, de calculer un niveau de risque météorologique et de présenter les résultats dans un dashboard.

### Question métier

> **Quelles villes et quelles périodes présentent le plus grand risque météorologique dans les prochains jours ?**

La solution doit aider un responsable opérationnel à :

- comparer les conditions météorologiques entre les villes ;
- identifier les périodes défavorables ;
- anticiper les risques pour les livraisons ;
- adapter l'organisation des opérations.

---

# 2. Objectifs du projet

Le projet doit permettre de :

1. récupérer les villes marocaines et leurs coordonnées ;
2. récupérer les prévisions météo quotidiennes ;
3. conserver les données brutes dans une couche Bronze ;
4. nettoyer et structurer les données dans une couche Silver ;
5. créer des features métier dans une couche Gold ;
6. calculer un `risk_score` compris entre 0 et 100 ;
7. charger les données finales dans PostgreSQL ;
8. réaliser des analyses SQL ;
9. visualiser les résultats avec Streamlit ;
10. automatiser le pipeline avec Airflow ;
11. conteneuriser les principaux services avec Docker Compose.

---

# 3. Sources de données

## 3.1 SimpleMaps

Source utilisée pour les villes marocaines :

- Source : SimpleMaps
- Données utilisées : nom de ville, latitude, longitude

Référence :

https://simplemaps.com/data/ma-cities

Les colonnes nécessaires au projet sont :

| Colonne | Description |
|---|---|
| `city` | Nom de la ville |
| `lat` | Latitude |
| `lng` | Longitude |

---

## 3.2 Open-Meteo

Open-Meteo fournit les prévisions météorologiques quotidiennes.

Variables utilisées :

- Maximum Temperature
- Minimum Temperature
- Precipitation Sum
- Precipitation Probability Max
- Maximum Wind Speed
- Maximum Wind Gusts
- Weather Code

Les coordonnées provenant de SimpleMaps sont utilisées pour interroger l'API.

---

# 4. Architecture du projet

L'architecture principale suit le modèle :

```text
                    ┌─────────────────┐
                    │    SimpleMaps   │
                    │   Cities CSV    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Open-Meteo    │
                    │       API       │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     BRONZE      │
                    │   Données raw   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     SILVER      │
                    │ Nettoyage / QA  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │      GOLD       │
                    │ Features + Risk │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │  Data Warehouse │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
        ┌───────────────┐          ┌───────────────┐
        │   Streamlit   │          │     SQL       │
        │   Dashboard   │          │   Analysis    │
        └───────────────┘          └───────────────┘

                 Airflow orchestre le pipeline
                 Docker conteneurise les services
```

---

# 5. Structure du projet

Structure recommandée :

```text
ETL_Meteo/
│
├── data/
│   ├── bronze/
│   │   └── YYYY-MM-DD/
│   ├── silver/
│   └── gold/
│
├── src/
│   ├── extract/
│   │   ├── extract_cities.py
│   │   └── extract_weather.py
│   │
│   ├── transform/
│   │   ├── clean_silver.py
│   │   └── build_gold.py
│   │
│   ├── load/
│   │   └── load_postgres.py
│   │
│   └── utils/
│       ├── config.py
│       └── logger.py
│
├── sql/
│   ├── schema.sql
│   └── analysis_queries.sql
│
├── dashboard/
│   ├── app.py
│   └── logic.py
│
├── dags/
│   └── weather_pipeline.py
│
├── docker/
│   └── requirements.txt
│
├── .env
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

# 6. Technologies utilisées

| Technologie | Utilisation |
|---|---|
| Python | Développement du pipeline |
| Pandas | Transformation des données |
| Requests | Appels API |
| SimpleMaps | Source des villes |
| Open-Meteo | Source météo |
| PostgreSQL | Stockage |
| SQL | Analyse |
| Streamlit | Dashboard |
| Plotly | Visualisations interactives |
| Airflow | Orchestration |
| Docker | Conteneurisation |
| Docker Compose | Gestion des services |

---

# 7. Commandes principales en développement local

Depuis la racine du projet :

```bash
cd ~/ETL_Meteo
```

Extraction des villes :

```bash
python -m src.extract.extract_cities
```

Extraction météo :

```bash
python -m src.extract.extract_weather
```

Silver :

```bash
python -m src.transform.clean_silver
```

Gold :

```bash
python -m src.transform.build_gold
```

Chargement PostgreSQL :

```bash
python -m src.load.load_postgres
```

Dashboard :

```bash
python -m streamlit run dashboard/app.py
```

---

# 8. Roadmap finale

```text
                    SPRINT 1
                       │
                       ▼
              ┌─────────────────┐
              │    Extraction   │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │     Bronze      │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │     Silver      │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │      Gold       │
              │  Risk Score     │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │   PostgreSQL    │
              └────────┬────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
        ┌───────────┐      ┌───────────┐
        │ SQL       │      │ Streamlit │
        │ Analytics │      │ Dashboard │
        └───────────┘      └───────────┘

                 ▲
                 │
              Airflow
                 │
              Docker
```

# 9. Résultat attendu

À la fin du Sprint 1, l'entreprise dispose d'une solution capable de :

**Récupérer → nettoyer → enrichir → stocker → analyser → visualiser → automatiser**

les données météorologiques des villes marocaines.

Le résultat final permet au responsable opérationnel d'identifier les **villes et périodes présentant les niveaux de risque météorologique les plus élevés selon le Risk Score défini dans le projet**, afin de disposer d'informations utiles à la préparation des opérations de livraison.
