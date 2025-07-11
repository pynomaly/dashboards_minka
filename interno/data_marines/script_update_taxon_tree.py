import os

import pandas as pd
import requests

try:
    directory = f"{os.environ['DASHBOARDS']}/interno"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


def get_marine(taxon_name):
    name_clean = taxon_name.replace(" ", "+")
    status = requests.get(
        f"https://www.marinespecies.org/rest/AphiaIDByName/{name_clean}?marine_only=true"
    ).status_code
    if (status == 200) or (status == 206):
        result = True
    else:
        result = False
    return result


nuevas_especies = []

taxon_url = f"{directory}/data_marines/taxon_tree_with_marines.csv"
taxon_tree = pd.read_csv(taxon_url)

last_id = taxon_tree.taxon_id.max()
session = requests.Session()

for i in range(last_id + 1, last_id + 100):
    print(i)
    url = f"https://minka-sdg.org/taxa/{i}.json"
    result = session.get(url).json()
    especie = {}
    try:
        especie["taxon_id"] = result["id"]
        especie["taxon_name"] = result["name"]
        especie["rank"] = result["rank"]
        especie["ancestry"] = result["ancestry"]
        especie["marine"] = get_marine(result["name"])
        nuevas_especies.append(especie)
    except:
        continue

if len(nuevas_especies) > 0:
    df_especies = pd.concat([taxon_tree, pd.DataFrame(nuevas_especies)])
    path = f"{directory}/data_marines/taxon_tree_with_marines.csv"
    df_especies.to_csv(path, index=False)
