# Image Airflow personnalisée : on part de l'image officielle et on
# ajoute uniquement les dépendances nécessaires à NOS scripts src/
# (pandas, requests, pyarrow, psycopg2) - pas besoin de streamlit/plotly
# ici, c'est le rôle du service dashboard, dans une image séparée.
FROM apache/airflow:2.10.5-python3.11

COPY docker/requirements-airflow.txt /tmp/requirements-airflow.txt
RUN pip install --no-cache-dir -r /tmp/requirements-airflow.txt
