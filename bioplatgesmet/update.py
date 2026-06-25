import calendar
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from threading import Semaphore

import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

# Rate limiting: máximo 10 requests por segundo
API_RATE_LIMIT = 10
_rate_semaphore = Semaphore(API_RATE_LIMIT)

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


def _safe_get_total_results(session, url, max_retries=5):
    """Helper function to safely get total_results with retries and rate limit handling"""
    base_wait = 2  # segundos base de espera

    for attempt in range(max_retries):
        try:
            response = session.get(url)

            # Manejar error 429 (Too Many Requests)
            if response.status_code == 429:
                wait_time = base_wait * (2 ** attempt)  # Backoff exponencial: 2, 4, 8, 16, 32s
                print(f"Rate limit (429) alcanzado. Esperando {wait_time}s antes de reintentar...")
                time.sleep(wait_time)
                continue

            # Manejar otros errores HTTP
            if response.status_code != 200:
                print(f"HTTP {response.status_code} en intento {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(base_wait)
                    continue
                else:
                    raise Exception(f"HTTP error {response.status_code} after {max_retries} attempts")

            data = response.json()
            return data["total_results"]

        except KeyError:
            if attempt < max_retries - 1:
                print(f"KeyError: 'total_results' not found, waiting {base_wait}s before retry {attempt + 1}")
                time.sleep(base_wait)
            else:
                print(f"KeyError: 'total_results' not found after {max_retries} attempts")
                raise
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                wait_time = base_wait * (2 ** attempt)
                print(f"Rate limit detectado. Esperando {wait_time}s...")
                time.sleep(wait_time)
                if attempt < max_retries - 1:
                    continue
            print(f"Unexpected error: {e}")
            raise
    return 0

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
    # Reutilizar sesión existente (bug fix: antes se creaba nueva sesión)
    total_obs = _safe_get_total_results(session, url_obs)
    total_spe = _safe_get_total_results(session, url_spe)
    total_part = _safe_get_total_results(session, url_part)
    total_ident = _safe_get_total_results(session, url_ident)

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
        url_obs = observations + "&".join([f"{k}={v}" for k, v in params.items()])
        url_species = species + "&".join([f"{k}={v}" for k, v in params.items()])
        url_observers = observers + "&".join([f"{k}={v}" for k, v in params.items()])
        url_identifiers = identifiers + "&".join([f"{k}={v}" for k, v in params.items()])

        total_obs = _safe_get_total_results(session, url_obs)
        total_species = _safe_get_total_results(session, url_species)
        total_participants = _safe_get_total_results(session, url_observers)
        total_identifiers = _safe_get_total_results(session, url_identifiers)

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
            total_species = _safe_get_total_results(session, url1)

            url2 = f"{observers}&project_id={main_project}&place_id={v[0]}"
            total_participants = _safe_get_total_results(session, url2)

            url3 = f"{observations}&project_id={main_project}&place_id={v[0]}"
            total_obs = _safe_get_total_results(session, url3)

        else:
            total_species = 0
            total_participants = 0
            total_obs = 0

            for place_v in v:
                url1 = f"{species}&project_id={main_project}&place_id={place_v}"
                total_species += _safe_get_total_results(session, url1)

                url2 = f"{observers}&project_id={main_project}&place_id={place_v}"
                total_participants += _safe_get_total_results(session, url2)

                url3 = f"{observations}&project_id={main_project}&place_id={place_v}"
                total_obs += _safe_get_total_results(session, url3)
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
            total_species = _safe_get_total_results(session, url)
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
    url = species + "?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return _safe_get_total_results(session, url)


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


def _get_species_with_rate_limit(args):
    """Wrapper para _get_species con rate limiting"""
    user_name, proj_id = args
    with _rate_semaphore:
        result = _get_species(user_name, proj_id)
        time.sleep(0.1)  # 100ms entre llamadas para no saturar la API
    return user_name, result


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

    # Paralelizar obtención de especies por usuario con rate limiting
    users = pt_users["participant"].tolist()
    species_dict = {}

    print(f"Obteniendo especies para {len(users)} usuarios en paralelo...")

    # Usar máximo 5 workers para no saturar la API
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_get_species_with_rate_limit, (user, main_project)): user
            for user in users
        }

        completed = 0
        for future in as_completed(futures):
            user_name, species_count = future.result()
            species_dict[user_name] = species_count
            completed += 1
            if completed % 20 == 0:
                print(f"  Procesados {completed}/{len(users)} usuarios...")

    pt_users["espècies"] = pt_users["participant"].map(species_dict)
    print(f"Completado: {len(users)} usuarios procesados")
    return pt_users


# Parcelas - sesión global para reutilizar
_parcelas_session = None

grupos_biologicos = {
    "Plantes": 12,
    "Mamífers": 8,
    "Ocells": 5,  # aves
    "Mol·luscs": 15,
    "Insectes": 11,
    "Lepidòpters": 325,  # mariposas
    "Himenòpter": 326,  # abejas
    "Aràcnid": 9,
    "Rèptils": 6,
    "Fongs i Líquens": 13,
}


def _fetch_parcela_metric(args):
    """Obtiene una métrica específica para una parcela con rate limiting"""
    place_id, metric_type, taxon_id = args
    global _parcelas_session
    if _parcelas_session is None:
        _parcelas_session = requests.Session()

    with _rate_semaphore:
        if metric_type == "obs":
            url = f"{API_PATH}/observations?project_id={main_project}&place_id={place_id}"
        elif metric_type == "species":
            url = f"{API_PATH}/observations/species_counts?project_id={main_project}&place_id={place_id}"
        elif metric_type == "taxon":
            url = f"{API_PATH}/observations?project_id={main_project}&place_id={place_id}&taxon_id={taxon_id}"
        else:
            return place_id, metric_type, taxon_id, 0

        result = _safe_get_total_results(_parcelas_session, url)
        time.sleep(0.1)  # 100ms entre llamadas

    return place_id, metric_type, taxon_id, result


def get_all_parcelas_data(df_parcelas):
    """Obtiene todos los datos de parcelas en paralelo"""
    place_ids = df_parcelas["place_id"].tolist()

    # Preparar todas las tareas: (place_id, metric_type, taxon_id)
    tasks = []
    for place_id in place_ids:
        # Métricas básicas
        tasks.append((place_id, "obs", None))
        tasks.append((place_id, "species", None))
        # Grupos biológicos
        for grupo_name, taxon_id in grupos_biologicos.items():
            tasks.append((place_id, "taxon", taxon_id))

    total_tasks = len(tasks)
    print(f"Procesando {total_tasks} llamadas API para {len(place_ids)} parcelas en paralelo...")

    # Almacenar resultados
    results = {place_id: {"num_obs": 0, "num_species": 0} for place_id in place_ids}
    for place_id in place_ids:
        for grupo_name in grupos_biologicos.keys():
            results[place_id][grupo_name] = 0

    # Mapeo de taxon_id a nombre de grupo
    taxon_to_grupo = {v: k for k, v in grupos_biologicos.items()}

    # Ejecutar en paralelo con 5 workers
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_parcela_metric, task): task for task in tasks}

        completed = 0
        for future in as_completed(futures):
            place_id, metric_type, taxon_id, value = future.result()

            if metric_type == "obs":
                results[place_id]["num_obs"] = value
            elif metric_type == "species":
                results[place_id]["num_species"] = value
            elif metric_type == "taxon":
                grupo_name = taxon_to_grupo.get(taxon_id, "")
                if grupo_name:
                    results[place_id][grupo_name] = value

            completed += 1
            if completed % 50 == 0:
                print(f"  Procesadas {completed}/{total_tasks} llamadas...")

    # Actualizar DataFrame
    for place_id in place_ids:
        mask = df_parcelas["place_id"] == place_id
        df_parcelas.loc[mask, "num_obs"] = results[place_id]["num_obs"]
        df_parcelas.loc[mask, "num_species"] = results[place_id]["num_species"]
        for grupo_name in grupos_biologicos.keys():
            df_parcelas.loc[mask, grupo_name] = results[place_id][grupo_name]

    print(f"Completado: {len(place_ids)} parcelas procesadas")
    return df_parcelas


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

    # update de parcelas (paralelizado)
    print("Actualizando datos de parcelas")
    df_parcelas = pd.read_csv(f"{directory}/data/parcelas.csv")
    df_parcelas = get_all_parcelas_data(df_parcelas)

    df_parcelas.to_csv(f"{directory}/data/parcelas.csv", index=False)

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Tiempo de ejecución {(execution_time / 60):.2f} minutos")
