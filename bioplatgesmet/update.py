import calendar
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

API_PATH = "https://api.minka-sdg.org/v1"

places = {
    "Montgat": [357],
    "Castelldefels": [349],
    "Gavà": [350],
    "El Prat de Llobregat": [351],
    "Sant Adrià del Besòs": [352],
    "Viladecans": [354],
    "Barcelona": [355, 356],
    "Badalona": [347, 348],
    "BioPlatgesMet": [None],
}
main_project = 264


def get_month_dict(years: list) -> dict:
    current_year = datetime.now().year
    current_month = datetime.now().month
    meses = {}

    for year in years:
        max_month = 12 if year < current_year else current_month
        for month in range(1, max_month + 1):
            last_day = calendar.monthrange(year, month)[1]
            meses[f"{year}-{str(month).zfill(2)}"] = last_day

    return meses


# acumulados mensuales
def _get_totals(place_id, start_date, end_date, session=None):
    if session is None:
        session = requests.Session()
    if place_id is not None:
        url_obs = f"{API_PATH}/observations?project_id={main_project}&place_id={place_id}&created_d1={start_date}&created_d2={end_date}"
        url_spe = f"{API_PATH}/observations/species_counts?project_id={main_project}&place_id={place_id}&created_d1={start_date}&created_d2={end_date}"
        url_part = f"{API_PATH}/observations/observers?project_id={main_project}&place_id={place_id}&created_d1={start_date}&created_d2={end_date}"
        url_ident = f"{API_PATH}/observations/identifiers?project_id={main_project}&place_id={place_id}&created_d1={start_date}&created_d2={end_date}"
    else:
        url_obs = f"{API_PATH}/observations?project_id={main_project}&created_d1={start_date}&created_d2={end_date}"
        url_spe = f"{API_PATH}/observations/species_counts?project_id={main_project}&created_d1={start_date}&created_d2={end_date}"
        url_part = f"{API_PATH}/observations/observers?project_id={main_project}&created_d1={start_date}&created_d2={end_date}"
        url_ident = f"{API_PATH}/observations/identifiers?project_id={main_project}&created_d1={start_date}&created_d2={end_date}"
    session = requests.Session()
    total_obs = session.get(url_obs).json()["total_results"]
    total_spe = session.get(url_spe).json()["total_results"]
    total_part = session.get(url_part).json()["total_results"]
    total_ident = session.get(url_ident).json()["total_results"]

    return total_obs, total_spe, total_part, total_ident


def get_monthly_metrics(places, meses, session=None):
    if session is None:
        session = requests.Session()
    total_metrics = []
    for place_k, place_v in places.items():
        for key, value in meses.items():
            total = {}
            total_obs = 0
            total_spe = 0
            total_part = 0
            total_ident = 0
            if len(place_v) == 0:
                total_obs, total_spe, total_part, total_ident = _get_totals(
                    None, f"{key}-01", f"{key}-{value}", session
                )
            elif len(place_v) == 1:
                total_obs, total_spe, total_part, total_ident = _get_totals(
                    place_v[0], f"{key}-01", f"{key}-{value}", session
                )
            elif len(place_v) > 1:
                for p in place_v:
                    obs, spe, part, ident = _get_totals(
                        p, f"{key}-01", f"{key}-{value}", session
                    )
                    total_obs += obs
                    total_spe += spe
                    total_part += part
                    total_ident += ident

            total["city"] = place_k
            total["month"] = key
            total["total_obs"] = total_obs
            total["total_spe"] = total_spe
            total["total_part"] = total_part
            total["total_ident"] = total_ident
            total_metrics.append(total)

    df = pd.DataFrame(total_metrics)
    return df


def get_cumulative_monthly_metrics(places, meses, session=None):
    if session is None:
        session = requests.Session()
    total_metrics = []
    for place_k, place_v in places.items():
        for key, value in meses.items():
            total = {}
            total_obs = 0
            total_spe = 0
            total_part = 0
            total_id = 0
            if len(place_v) == 0:
                total_obs, total_spe, total_part, total_id = _get_totals(
                    None, f"", f"{key}-{value}", session
                )
            elif len(place_v) == 1:
                total_obs, total_spe, total_part, total_id = _get_totals(
                    place_v[0], f"", f"{key}-{value}", session
                )
            elif len(place_v) > 1:
                for p in place_v:
                    obs, spe, part, iden = _get_totals(
                        p, f"", f"{key}-{value}", session
                    )
                    total_obs += obs
                    total_spe += spe
                    total_part += part
                    total_id += iden

            total["city"] = place_k
            total["month"] = key
            total["total_obs"] = total_obs
            total["total_spe"] = total_spe
            total["total_part"] = total_part
            total["total_ident"] = total_id
            total_metrics.append(total)

    df = pd.DataFrame(total_metrics)
    return df


def get_obs_from_project_places(project, places):
    for k, v in places.items():
        total_obs = []
        for i in range(len(v)):
            obs = get_obs(id_project=project, place_id=v[i])
            total_obs.extend(obs)
        df1, df2 = get_dfs(total_obs)
        df1.to_csv(f"{directory}/data/obs_{k}.csv", index=False)
        # df2.to_csv(f"{directory}/data/photos_{k}.csv")


def get_obs_from_main_project(main_project):
    obs = get_obs(id_project=main_project)
    df_obs, df_photos = get_dfs(obs)
    df_obs.to_csv(f"{directory}/data/{main_project}_obs.csv", index=False)
    df_photos.to_csv(f"{directory}/data/{main_project}_photos.csv", index=False)


def update_main_metrics(proj_id, df_main_metrics, session=None):
    # Actualiza solo los datos desde 2024
    df_main_metrics.date = pd.to_datetime(df_main_metrics["date"], format="mixed")
    fecha_fin = datetime.today() - timedelta(days=60)
    antiguo = df_main_metrics[df_main_metrics.date <= fecha_fin].copy()
    results = []
    observations = f"{API_PATH}/observations?"
    species = f"{API_PATH}/observations/species_counts?"
    observers = f"{API_PATH}/observations/observers?"
    identifiers = f"{API_PATH}/observations/identifiers?"

    # Crear una sesión de requests
    if session is None:
        session = requests.Session()

    # Fecha de inicio de la actualización
    day = fecha_fin + timedelta(days=1)

    rango_temporal = (datetime.today().date() - day.date()).days

    for i in range(rango_temporal + 1):
        print(i)
        st_day = day.strftime("%Y-%m-%d")

        params = {
            "project_id": proj_id,
            "created_d2": st_day,
            "order": "desc",
            "order_by": "created_at",
        }

        # Utilizar la sesión para realizar las solicitudes
        total_obs = session.get(observations, params=params).json()["total_results"]
        total_species = session.get(species, params=params).json()["total_results"]
        total_participants = session.get(observers, params=params).json()[
            "total_results"
        ]
        total_identifiers = session.get(identifiers, params=params).json()[
            "total_results"
        ]

        result = {
            "date": st_day,
            "observations": total_obs,
            "species": total_species,
            "participants": total_participants,
            "identifiers": total_identifiers,
        }

        results.append(result)

        day = day + timedelta(days=1)

    result_df = pd.DataFrame(results)
    total_result = pd.concat([antiguo, result_df], ignore_index=True)
    print("Updated main metrics")
    return total_result


def get_metrics_cities(main_project, places, session=None):
    result = []
    print("Places antes:", len(places))
    del places["BioPlatgesMet"]
    print("Places después:", len(places))

    species = f"{API_PATH}/observations/species_counts?"
    observers = f"{API_PATH}/observations/observers?"
    observations = f"{API_PATH}/observations?"
    if session is None:
        session = requests.Session()

    for k, v in places.items():
        if len(v) == 1:
            url1 = f"{species}&project_id={main_project}&place_id={v[0]}"
            total_species = session.get(url1).json()["total_results"]

            url2 = f"{observers}&project_id={main_project}&place_id={v[0]}"
            total_participants = session.get(url2).json()["total_results"]

            url3 = f"{observations}&project_id={main_project}&place_id={v[0]}"
            total_obs = session.get(url3).json()["total_results"]

        else:
            total_species = 0
            total_participants = 0
            total_obs = 0

            for place_v in v:
                url1 = f"{species}&project_id={main_project}&place_id={place_v}"
                total_species += session.get(url1).json()["total_results"]

                url2 = f"{observers}&project_id={main_project}&place_id={place_v}"
                total_participants += session.get(url2).json()["total_results"]

                url3 = f"{observations}&project_id={main_project}&place_id={place_v}"
                total_obs += session.get(url3).json()["total_results"]
        data = {
            "ciutat": k,
            "espècies": total_species,
            "participants": total_participants,
            "observacions": total_obs,
        }
        result.append(data)
    main_metrics = pd.DataFrame(result)
    return main_metrics


def get_num_species(main_project, session=None):
    if session is None:
        session = requests.Session()
    num_species = []
    base_url = f"{API_PATH}/observations/species_counts?"
    start_date = datetime(2022, 1, 1)
    end_date = datetime.now().replace(day=1)

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"{base_url}project_id={main_project}&introduced=true&d2={date_str}"
        try:
            total_species = session.get(url).json()["total_results"]
            datos = {"data": date_str, "introduced_species": total_species}
            num_species.append(datos)
        except Exception as e:
            print(f"Error al obtener datos para la fecha {date_str}: {e}")
        current_date = current_date + timedelta(
            days=32
        )  # Avanzar al primer día del siguiente mes
        current_date = current_date.replace(day=1)
    df_introduced_by_month = pd.DataFrame(num_species)
    return df_introduced_by_month


def _get_species(user_name, proj_id, session=None):
    if session is None:
        session = requests.Session()
    species = f"{API_PATH}/observations/species_counts"
    params = {"project_id": proj_id, "user_login": user_name}
    return session.get(species, params=params).json()["total_results"]


def _get_identifiers(df_users, proj_id, session=None):
    if session is None:
        session = requests.Session()
    identifiers = f"{API_PATH}/observations/identifiers?"
    url4 = f"{identifiers}&project_id={proj_id}"
    results = session.get(url4).json()["results"]
    for result in results:
        user_name = result["user"]["login"]
        df_users.loc[df_users.participant == user_name, "identificacions"] = result[
            "count"
        ]
    df_users["identificacions"] = df_users["identificacions"].fillna(0)
    return df_users


def get_participation_df(main_project, session=None):
    if session is None:
        session = requests.Session()
    df_obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")
    pt_users = (
        df_obs["user_login"]
        .value_counts()
        .to_frame()
        .reset_index(drop=False)
        .rename(columns={"user_login": "participant", "count": "observacions"})
    )
    pt_users = _get_identifiers(pt_users, main_project, session)

    pt_users["espècies"] = pt_users["participant"].apply(
        lambda x: _get_species(x, main_project, session)
    )
    return pt_users


if __name__ == "__main__":
    start_time = time.time()

    session = requests.Session()

    print("Actualizando métricas acumulativas del proyecto principal")
    df_main_metrics = pd.read_csv(f"{directory}/data/264_main_metrics.csv")
    result_df = update_main_metrics(main_project, df_main_metrics, session)
    result_df.to_csv(f"{directory}/data/{main_project}_main_metrics.csv", index=False)

    print("Descargando métricas mensuales de los places del proyecto")
    current_year = datetime.now().year
    years = list(range(2022, current_year + 1))
    meses = get_month_dict(years)

    df = get_monthly_metrics(places, meses, session)
    df.to_csv(f"{directory}/data/city_monthly_metrics.csv", index=False)

    print("Descargando métricas mensuales acumuladas de los places del proyecto")
    df_cumulative = get_cumulative_monthly_metrics(
        places=places, meses=meses, session=session
    )
    df_cumulative.to_csv(
        f"{directory}/data/cumulative_city_monthly_metrics.csv", index=False
    )

    print("Descargando métricas de ciudades")
    main_metrics_by_city = get_metrics_cities(main_project, places, session)
    main_metrics_by_city.to_csv(f"{directory}/data/city_total_metrics.csv", index=False)

    print("Descargando observaciones de proyecto principal")
    get_obs_from_main_project(main_project)
    get_obs_from_project_places(main_project, places)

    print("Incluyendo ciudad en 264_obs.csv")
    df_obs = pd.read_csv(f"{directory}/data/264_obs.csv")
    for city in [
        "Badalona",
        "Barcelona",
        "Castelldefels",
        "El Prat de Llobregat",
        "Gavà",
        "Montgat",
        "Sant Adrià del Besòs",
        "Viladecans",
    ]:
        df_city = pd.read_csv(f"{directory}/data/obs_{city}.csv")
        df_obs.loc[df_obs["id"].isin(df_city["id"].to_list()), "address"] = city
    df_obs.to_csv(f"{directory}/data/264_obs.csv", index=False)

    print("Descargando especies introducidas")
    df_introduced_by_month = get_num_species(main_project, session)
    df_introduced_by_month.to_csv(
        f"{directory}/data/introduced_by_month.csv", index=False
    )

    print("Descargando tabla de participantes")
    pt_users = get_participation_df(main_project)
    pt_users.to_csv(f"{directory}/data/{main_project}_participants.csv", index=False)

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Tiempo de ejecución {(execution_time / 60):.2f} minutos")
