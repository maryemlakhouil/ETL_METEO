# DAG Airflow 
import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.log.logging_mixin import LoggingMixin

logger = LoggingMixin().log


# détecter l’échec d’une tâche
def on_failure_alert(context):
    task_id = context["task_instance"].task_id
    dag_id = context["dag"].dag_id
    execution_date = context["logical_date"]
    exception = context.get("exception")
    logger.error(
        f"[ALERTE DAG] Échec de la tache '{task_id}' dans le DAG '{dag_id}' "
        f"(run du {execution_date}) : {exception}"
    )


#  lancer extraction  : **context permet à Airflow de transmettre plusieurs informations à la fonction 

def task_extract(**context):
    from src.extract.extract_weather import run_bronze_extraction
    output_dir = run_bronze_extraction()
    logger.info(f"Bronze écrit dans {output_dir}")


def task_silver(**context):
    from src.transform.clean_silver import run_silver
    output_path = run_silver()
    logger.info(f"Silver écrit dans {output_path}")


def task_gold(**context):
    from src.transform.build_gold import run_gold
    output_path = run_gold()
    logger.info(f"Gold écrit dans {output_path}")


def task_load(**context):
    from src.load.load_postgres import run_load
    run_load()
    logger.info("Chargement PostgreSQL terminé")


#  Définition du DAG
default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=30),
    "on_failure_callback": on_failure_alert,
}

with DAG(
    dag_id="weather_risk_pipeline",
    description="Pipeline météo livraison : extraction, nettoyage, scoring, chargement",
    default_args=default_args,
    schedule="0 6 * * *",   
    start_date=datetime(2026, 9, 1),
    catchup=False,          
    max_active_runs=1,    
    tags=["weather", "etl", "livraison"],
) as dag:

    extract = PythonOperator(
        task_id="extract_bronze",
        python_callable=task_extract,
    )

    silver = PythonOperator(
        task_id="clean_silver",
        python_callable=task_silver,
    )

    gold = PythonOperator(
        task_id="build_gold",
        python_callable=task_gold,
    )

    load = PythonOperator(
        task_id="load_postgres",
        python_callable=task_load,
    )

    extract >> silver >> gold >> load
