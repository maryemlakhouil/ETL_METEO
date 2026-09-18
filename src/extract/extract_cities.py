#  Lit du fichier csv et retorne un dataframe ,aucun transformation 
import pandas as pd 

from src.utils.config import CITIES_CSV_PATH
from src.utils.logger import get_Logger 

logger = get_Logger(__name__)

def load_cities() -> pd.DataFrame : 

    if not CITIES_CSV_PATH.exists(): 
        raise FileNotFoundError(f"Fichier villes introuvable : {CITIES_CSV_PATH}. ")
    
    df = pd.read_csv(CITIES_CSV_PATH)

    logger.info(f"{len(df)} villes chargées depuis {CITIES_CSV_PATH.name}")

    required_columns = {'city',"lat","lng"}
    missing = required_columns - set(df.columns)

    if missing : 
        raise ValueError(
            f"Colonnes manquantes dans le CSV : {missing}. "
            f"Colonnes disponibles : {list(df.columns)}"
        )
    # On retire ici uniquement les lignes totalement inutilisables 

    before = len(df)
    df = df.dropna(subset=["lat", "lng"])
    dropped = before - len(df)

    if dropped : 
        logger.warning(f"{dropped} villes ignorées car lat/lng manquantes")

    return df[["city","lat","lng"]].reset_index(drop=True)


if __name__ == '__main__':
        cities = load_cities()
        print(cities)


