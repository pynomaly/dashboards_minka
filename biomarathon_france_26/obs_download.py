import time

import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

df_obs = pd.read_csv("data/576_df_obs.csv")
df_obs.taxon_id = pd.to_numeric(df_obs.taxon_id, errors="coerce").astype("Int64")


def get_first_obs(taxon_id):
    url = f"https://api.minka-sdg.org/v1/observations?taxon_id={taxon_id}&order=asc&order_by=observed_on"
    response = requests.get(url).json()
    time.sleep(0.2)
    try:
        observed_on = response["results"][0]["observed_on_details"]["date"]
        return observed_on
    except:
        return None


taxon_ids = df_obs["taxon_id"].unique()
results = {taxon_id: get_first_obs(taxon_id) for taxon_id in taxon_ids}
df_obs["first_obs"] = df_obs["taxon_id"].map(results)
df_obs["in_biomarato26"] = df_obs["first_obs"] >= "2026-05-02"


def _get_common_name_from_taxon(taxon_id, lang="en", session=None):
    url_taxon = f"https://api.minka-sdg.org/v1/taxa?taxon_id={taxon_id}&locale={lang}"
    if session is None:
        session = requests.Session()
    try:
        results = session.get(url_taxon).json()["results"]
    except:
        return None
    for result in results:
        try:
            return result["preferred_common_name"]
        except:
            return None


# Lista de idiomas que quieres
languages = ["en", "es", "ca"]  # ajusta según necesites

taxon_ids = df_obs["taxon_id"].unique()

# Crear diccionario de resultados por idioma
for lang in languages:
    results = {
        taxon_id: _get_common_name_from_taxon(taxon_id, lang=lang, session=None)
        for taxon_id in taxon_ids
    }
    df_obs[f"{lang}_common_name"] = df_obs["taxon_id"].map(results)

# especies de interés
df_exotic = pd.read_csv("data/species/species_exotic.csv")
df_protected = pd.read_csv("data/species/species_protected.csv")

df_exotic.columns = ["taxon_name", "taxon_id", "category", "regulation"]
df_protected.columns = ["taxon_name", "taxon_id", "category", "regulation"]
df_species = pd.concat([df_exotic, df_protected], ignore_index=True)

df_obs = pd.merge(
    df_obs,
    df_species[["taxon_id", "category", "regulation"]],
    on="taxon_id",
    how="left",
)

df_marine = pd.read_csv("data/marines.csv")
df_obs = pd.merge(
    df_obs, df_marine[["taxon_name", "marine"]], on="taxon_name", how="left"
)

session = requests.Session()


def get_marine(taxon_name, session=session):
    try:
        name_clean = taxon_name.replace(" ", "+")
        status = session.get(
            f"https://www.marinespecies.org/rest/AphiaIDByName/{name_clean}?marine_only=true"
        ).status_code
        print(status)
        if (status == 200) or (status == 206):
            result = True
        else:
            result = False
            print(result)
        print(taxon_name, result)
        time.sleep(0.5)
        return result
    except:
        return None


taxon_new = df_obs.loc[df_obs.marine.isnull(), ["taxon_id", "taxon_name"]]

if len(taxon_new) > 0:
    # actualizo el archivo marines
    taxon_new["marine"] = taxon_new["taxon_name"].apply(get_marine)
    df_marine = pd.concat([df_marine, taxon_new], ignore_index=True)
    df_marine = df_marine[df_marine.marine.notnull()].reset_index()
    df_marine.to_csv("data/marines.csv", index=False)
    # vuelvo a hacer el merge con todos los taxones
    df_obs = df_obs.drop(columns="marine")
    df_obs = pd.merge(df_obs, df_marine[["taxon_name", "marine"]], on="taxon_name")

df_obs.to_csv("data/obs_to_download.csv", index=False)
