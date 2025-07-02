import argparse

import pandas as pd
import requests

# api_token_v1 = "eyJhbGciOiJIUzUxMiJ9.eyJ1c2VyX2lkIjozLCJleHAiOjE3MjExNTA3OTJ9.GbQVQR3qdsmGinOqlzbcpr7yXjltl34S7HQFEVPUyO8PkrBBDjftI0HDhMsOJm-I5pQzJE4LudBwI4UngOCH8g"

parser = argparse.ArgumentParser(
    description="Procesa datos de observaciones de especies amenazadas."
)
parser.add_argument(
    "api_token_v1", type=str, help="El token de la API para verificador_1"
)

args = parser.parse_args()
api_token_v1 = args.api_token_v1
path = "amenazadas.csv"


def get_count_amenazadas(taxon_id, api_token_v1):
    url = f"https://api.minka-sdg.org/v1/observations?verifiable=any&&project_id=264&taxon_id={taxon_id}&order=asc&&order_by=observed_on"
    headers = {
        "Authorization": api_token_v1,
    }
    response = requests.get(url, headers=headers)
    print(response.status_code)
    num_obs = response.json()["total_results"]
    if num_obs > 0:
        first_observed = response.json()["results"][0]["observed_on_details"]["date"]
        last_observed = response.json()["results"][-1]["observed_on_details"]["date"]
    else:
        first_observed = None
        last_observed = None
    return num_obs, first_observed, last_observed


df = pd.read_csv(path)

# Aplicar la función a cada valor en 'taxon_id' y convertir los resultados en un DataFrame temporal
results = (
    df["taxon_id"]
    .apply(lambda x: get_count_amenazadas(x, api_token_v1))
    .apply(pd.Series)
)

# Renombrar las columnas del DataFrame temporal
results.columns = ["count", "first_observed", "last_observed"]

# Concatenar los resultados con el DataFrame original
df = pd.concat([df[["taxon_name", "taxon_id"]], results], axis=1)

print("csv actualizado")

df.to_csv(path, index=False)
