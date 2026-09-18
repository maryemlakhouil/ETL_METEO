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

# 6. Planification Jira — Sprint 1

## Sprint

**Nom :** `Sprint 1 — Pipeline ETL Météo`

**Durée :** 10 jours

### Sprint Goal

> Construire un pipeline météo complet Bronze → Silver → Gold, charger les données dans PostgreSQL, fournir un dashboard Streamlit et automatiser le traitement avec Airflow et Docker.

---

# 7. METEO-1 — Architecture et configuration

**Type : Story**

## Description

Mettre en place la structure technique et l'environnement du projet.

## Sub-tasks

- [ ] Créer le repository
- [ ] Créer les dossiers du projet
- [ ] Configurer Python
- [ ] Configurer les dépendances
- [ ] Configurer `.env`
- [ ] Créer `config.py`
- [ ] Créer le logger
- [ ] Installer PostgreSQL
- [ ] Tester la connexion PostgreSQL

## Acceptance Criteria

- La structure du projet existe.
- Les dépendances sont installées.
- Les paramètres sont centralisés.
- PostgreSQL est accessible.

---

# 8. METEO-2 — Extraction SimpleMaps

**Type : Story**

## Description

Récupérer et valider le dataset des villes marocaines.

## Sub-tasks

- [ ] Télécharger le dataset
- [ ] Identifier les colonnes nécessaires
- [ ] Conserver `city`, `lat`, `lng`
- [ ] Vérifier les valeurs manquantes
- [ ] Vérifier les coordonnées
- [ ] Implémenter `extract_cities.py`
- [ ] Ajouter les logs
- [ ] Tester l'extraction

## Acceptance Criteria

Chaque ville possède un nom et des coordonnées valides.

---

# 9. METEO-3 — Extraction Open-Meteo / Bronze

**Type : Story**

## Description

Interroger Open-Meteo pour récupérer les prévisions météo quotidiennes.

## Variables

```text
temperature_2m_max
temperature_2m_min
precipitation_sum
precipitation_probability_max
wind_speed_10m_max
wind_gusts_10m_max
weather_code
```

## Sub-tasks

- [ ] Configurer l'URL API
- [ ] Préparer les paramètres
- [ ] Boucler sur les villes
- [ ] Effectuer les appels API
- [ ] Ajouter un timeout
- [ ] Gérer les erreurs HTTP
- [ ] Gérer les erreurs réseau
- [ ] Gérer les réponses JSON invalides
- [ ] Implémenter les retries
- [ ] Ajouter un délai entre retries
- [ ] Sauvegarder les réponses brutes
- [ ] Générer un manifest
- [ ] Logger les villes en échec

## Acceptance Criteria

Les données brutes sont stockées dans :

```text
data/bronze/YYYY-MM-DD/
```

Les fichiers Bronze ne sont pas modifiés par les transformations.

---

# 10. METEO-4 — Transformation Silver

**Type : Story**

## Description

Transformer les données Bronze en données propres et structurées.

## Sub-tasks

- [ ] Lire les JSON Bronze
- [ ] Extraire les données quotidiennes
- [ ] Standardiser les noms de colonnes
- [ ] Convertir les dates
- [ ] Convertir les colonnes numériques
- [ ] Détecter les doublons
- [ ] Traiter les valeurs manquantes
- [ ] Détecter les incohérences
- [ ] Ajouter les coordonnées
- [ ] Générer un rapport qualité
- [ ] Exporter CSV
- [ ] Exporter Parquet

## Standardisation

| Bronze | Silver |
|---|---|
| `time` | `forecast_date` |
| `temperature_2m_max` | `temp_max` |
| `temperature_2m_min` | `temp_min` |
| `precipitation_sum` | `precipitation_mm` |
| `precipitation_probability_max` | `precipitation_prob` |
| `wind_speed_10m_max` | `wind_speed_max` |
| `wind_gusts_10m_max` | `wind_gust_max` |
| `weather_code` | `weather_code` |

## Acceptance Criteria

Les données Silver sont propres, typées et prêtes pour le Feature Engineering.

---

# 11. METEO-5 — Gold et Risk Score

**Type : Story**

## Description

Créer les indicateurs métier et le score de risque.

## Features

- `temp_category`
- `precipitation_category`
- `wind_category`
- `day_of_week`
- `is_weekend`
- `days_ahead`
- `risk_score`
- `risk_level`
- `data_quality_flag`

## Risk Score

Le score est compris entre :

```text
0 ───────────────────────────── 100
Faible                         Critique
```

Proposition de pondération :

| Facteur | Poids maximal |
|---|---:|
| Précipitations | 35 |
| Vent | 30 |
| Température extrême | 15 |
| Weather Code | 20 |
| **Total** | **100** |

### Précipitations — 35 points

Le score peut prendre en compte :

- quantité de précipitations ;
- probabilité maximale de précipitations.

### Vent — 30 points

Le score prend en compte notamment les rafales maximales.

### Température — 15 points

Une pénalité est appliquée lorsque la température sort d'une zone de confort définie.

### Weather Code — 20 points

Les codes météo sont regroupés selon leur niveau de sévérité.

## Niveaux

```text
0 – <25     → Faible
25 – <50    → Modéré
50 – <75    → Élevé
75 – 100    → Critique
```

## Justification

Le score est un indicateur synthétique destiné à faciliter la lecture opérationnelle. Il ne constitue pas une mesure scientifique universelle du danger météorologique.

## Acceptance Criteria

- Le score est toujours compris entre 0 et 100.
- Chaque ligne possède un niveau de risque.
- La formule est documentée.
- Les données manquantes sont signalées par `data_quality_flag`.

---

# 12. METEO-6 — Chargement PostgreSQL

**Type : Story**

## Description

Charger les données Gold dans PostgreSQL.

## Modèle de données

### Table `villes`

```text
city_id
city_name
latitude
longitude
```

### Table `previsions_meteo`

```text
forecast_id
city_id
forecast_date
temp_max
temp_min
precipitation_mm
precipitation_prob
wind_speed_max
wind_gust_max
weather_code
temp_category
precipitation_category
wind_category
risk_score
risk_level
data_quality_flag
```

## Sub-tasks

- [ ] Créer `schema.sql`
- [ ] Créer la table `villes`
- [ ] Créer la table `previsions_meteo`
- [ ] Ajouter les clés primaires
- [ ] Ajouter la clé étrangère
- [ ] Ajouter les contraintes
- [ ] Ajouter les index
- [ ] Implémenter le chargement
- [ ] Implémenter UPSERT
- [ ] Tester les nouvelles exécutions
- [ ] Vérifier l'absence de doublons

## Stratégie anti-doublons

Utiliser une contrainte unique sur :

```text
(city_id, forecast_date)
```

et un UPSERT lors du chargement.

Les prévisions peuvent être mises à jour à chaque nouvelle exécution.

## Bonus historique

Conserver plusieurs versions d'une même prévision avec :

```text
forecast_generated_at
loaded_at
```

ou une table dédiée à l'historique.

---

# 13. METEO-7 — Analyse SQL

**Type : Story**

## Objectif

Répondre aux questions métier avec PostgreSQL.

## Requêtes minimales

### SQL 1 — Température maximale

> Quelles villes auront les températures les plus élevées ?

### SQL 2 — Précipitations

> Quelles villes auront les précipitations les plus importantes ?

### SQL 3 — Risque moyen

> Quelles villes présentent le risque moyen le plus élevé ?

### SQL 4 — Risque maximal

> Quelles périodes présentent le risque maximal ?

### SQL 5 — Risque par ville

> Pour chaque ville, quelle période présente le plus grand risque ?

## Bonus

- [ ] Sous-requête
- [ ] CTE
- [ ] `ROW_NUMBER()`
- [ ] `RANK()`
- [ ] `PARTITION BY`
- [ ] fonctions d'agrégation

---

# 14. METEO-8 — Dashboard Streamlit

**Type : Story**

## Objectif

Créer une interface permettant aux responsables opérationnels d'analyser rapidement les risques météo.

## KPIs

Le dashboard affiche :

1. Nombre de villes
2. Température maximale
3. Précipitations maximales
4. Nombre de périodes à risque
5. Ville présentant le risque moyen le plus élevé

## Filtres

- Ville
- Date
- Période
- Niveau de risque

## Visualisations

### Graphique 1 — Bar chart

Risque moyen par ville.

```python
st.bar_chart(by_city)
```

### Graphique 2 — Line chart

Évolution du risque au fil des jours.

```python
st.line_chart(pivot)
```

### Graphique 3 — Carte

Carte interactive avec Plotly.

```python
px.scatter_mapbox(...)
```

Les points représentent les villes et utilisent :

- la latitude ;
- la longitude ;
- la couleur selon le niveau de risque ;
- la taille selon le `risk_score`.

### Tableau détaillé

Afficher notamment :

```text
city_name
forecast_date
temp_max
precipitation_mm
wind_gust_max
risk_score
risk_level
data_quality_flag
```

## Acceptance Criteria

Le dashboard permet de répondre rapidement :

> **Où et quand faut-il être particulièrement vigilant ?**

---

# 15. METEO-9 — Airflow

**Type : Story**

## Objectif

Automatiser l'ensemble du pipeline.

## DAG

```text
extract_cities
       ↓
extract_weather
       ↓
clean_silver
       ↓
build_gold
       ↓
load_postgres
       ↓
validation
```

## Sub-tasks

- [ ] Créer le DAG
- [ ] Configurer les tâches
- [ ] Définir les dépendances
- [ ] Planifier une exécution quotidienne
- [ ] Ajouter les retries
- [ ] Configurer les logs
- [ ] Tester un succès
- [ ] Tester un échec
- [ ] Vérifier les données après exécution

## Exemple de stratégie

```text
Schedule : quotidien
Retries : 2 ou 3
Retry delay : quelques minutes
```

## Acceptance Criteria

Le pipeline peut être exécuté automatiquement et les erreurs temporaires sont retentées.

---

# 16. METEO-10 — Docker Compose

**Type : Story**

## Objectif

Conteneuriser les services principaux.

## Services

```text
PostgreSQL
Airflow
Streamlit
```

## Sub-tasks

- [ ] Créer Dockerfile
- [ ] Créer `docker-compose.yml`
- [ ] Configurer PostgreSQL
- [ ] Configurer Airflow
- [ ] Configurer Streamlit
- [ ] Configurer les volumes
- [ ] Configurer le réseau
- [ ] Configurer les variables d'environnement
- [ ] Tester le démarrage
- [ ] Tester la communication entre services

## Acceptance Criteria

Les principaux services peuvent être démarrés avec Docker Compose.

---

# 17. METEO-11 — Tests et validation

**Type : Task**

## Tests

### Extraction

- [ ] CSV disponible
- [ ] Colonnes correctes
- [ ] Coordonnées valides

### API

- [ ] API accessible
- [ ] Timeout géré
- [ ] HTTP errors gérées
- [ ] Retry fonctionnel
- [ ] JSON valide

### Silver

- [ ] Types corrects
- [ ] Dates correctes
- [ ] Doublons contrôlés
- [ ] Valeurs manquantes identifiées

### Gold

- [ ] Risk Score entre 0 et 100
- [ ] Risk Level cohérent
- [ ] Features générées

### PostgreSQL

- [ ] Tables créées
- [ ] Relations correctes
- [ ] UPSERT fonctionnel
- [ ] Pas de doublons

### Dashboard

- [ ] Connexion PostgreSQL
- [ ] KPIs fonctionnels
- [ ] Filtres fonctionnels
- [ ] Graphiques fonctionnels
- [ ] Carte fonctionnelle

### Airflow

- [ ] DAG visible
- [ ] DAG exécutable
- [ ] Retry fonctionnel
- [ ] Logs disponibles

### Docker

- [ ] Services démarrent
- [ ] Services communiquent
- [ ] Pipeline exécutable

---

# 18. METEO-12 — Documentation

**Type : Task**

## Documentation à fournir

- [ ] Contexte
- [ ] Objectifs
- [ ] Sources
- [ ] Architecture
- [ ] Structure du projet
- [ ] Bronze
- [ ] Silver
- [ ] Gold
- [ ] Risk Score
- [ ] PostgreSQL
- [ ] SQL
- [ ] Streamlit
- [ ] Airflow
- [ ] Docker
- [ ] Installation
- [ ] Exécution
- [ ] Tests
- [ ] Screenshots

---

# 19. Planning du Sprint

| Jour | Tickets | Objectif |
|---|---|---|
| J1 | METEO-1 | Setup et architecture |
| J2 | METEO-2 + METEO-3 | Sources et début extraction |
| J3 | METEO-3 | Bronze complet |
| J4 | METEO-4 | Silver |
| J5 | METEO-5 | Gold + Risk Score |
| J6 | METEO-6 | PostgreSQL |
| J7 | METEO-7 | SQL |
| J8 | METEO-8 | Streamlit |
| J9 | METEO-9 | Airflow |
| J10 | METEO-10 + 11 + 12 | Docker + tests + documentation |

---

# 20. Priorités Jira

## Priorité Haute

- METEO-1
- METEO-2
- METEO-3
- METEO-4
- METEO-5
- METEO-6
- METEO-8
- METEO-9
- METEO-10

## Priorité Moyenne

- METEO-7
- METEO-12

## Priorité finale

- METEO-11 — Tests et validation

---

# 21. Definition of Done globale

Le Sprint est considéré comme terminé lorsque :

- [ ] Les villes marocaines sont récupérées.
- [ ] Les prévisions Open-Meteo sont récupérées.
- [ ] Les données Bronze sont conservées sans modification.
- [ ] Les données Silver sont nettoyées.
- [ ] Les données Gold sont enrichies.
- [ ] Le Risk Score est calculé entre 0 et 100.
- [ ] Les données sont chargées dans PostgreSQL.
- [ ] Les nouvelles exécutions ne créent pas de doublons.
- [ ] Les 5 requêtes SQL sont fonctionnelles.
- [ ] Le dashboard Streamlit fonctionne.
- [ ] Les filtres fonctionnent.
- [ ] Les KPIs fonctionnent.
- [ ] Les graphiques fonctionnent.
- [ ] La carte fonctionne.
- [ ] Le DAG Airflow fonctionne.
- [ ] Les retries sont configurés.
- [ ] Docker Compose démarre les services.
- [ ] Les tests de bout en bout sont réalisés.
- [ ] Le README est complet.

---

# 22. Technologies utilisées

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

# 23. Commandes principales en développement local

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

# 24. Roadmap finale

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

# 25. Résultat attendu

À la fin du Sprint 1, l'entreprise dispose d'une solution capable de :

**Récupérer → nettoyer → enrichir → stocker → analyser → visualiser → automatiser**

les données météorologiques des villes marocaines.

Le résultat final permet au responsable opérationnel d'identifier les **villes et périodes présentant les niveaux de risque météorologique les plus élevés selon le Risk Score défini dans le projet**, afin de disposer d'informations utiles à la préparation des opérations de livraison.
