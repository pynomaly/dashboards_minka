import calendar
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from mecoda_minka import get_dfs, get_obs

try:
    directory = f"{os.environ['DASHBOARDS']}/arsinoe"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )

API_PATH = "https://api.minka-sdg.org/v1"

places = {
    "3ο ΓΥΜΝΑΣΙΟ ΝΕΑΣ ΦΙΛΑΔΕΛΦΕΙΑΣ": [252],
    "2ο Γυμνάσιο Νέας Φιλαδέλφειας": [197],
    "ΜΟΥΣΙΚΟ ΓΥΜΝΑΣΙΟ Λ.Τ. ΙΛΙΟΥ": [247],
    "11ο Γυμνάσιο ΙΛΙΟΥ": [257],
    "1ο ΓΕΛ ΑΧΑΡΝΩΝ": [196],
    "ΒΑΡΒΑΚΕΙΟ ΠΡΟΤΥΠΟ ΓΥΜΝΑΣΙΟ": [240],
    "1ο Γυμνάσιο ΑΣΠΡΟΠΥΡΓΟΥ": [267],
    "6o ΓΕΛ ΑΘΗΝΩΝ": [253],
    "7ο ΓΕΛ ΑΧΑΡΝΩΝ": [195],
    "3ο ΓΕΛ ΖΩΓΡΑΦΟΥ": [211],
    "5ο ΕΚ ΑΝΑΤΟΛΙΚΗΣ ΑΤΤΙΚΗΣ": [238],
    "Γυμνάσιο-Λυκειακές Τάξεις Λαιμού Πρεσπών": [354],
    "3ο ΕΠΑΛ Αθηνών": [241],
    "4ο ΔΗΜΟΤΙΚΟ ΣΧΟΛΕΙΟ ΑΜΑΡΟΥΣΙΟΥ": [254],
    "ΠΡΟΤΥΠΟ ΓΕΛ ΑΓΙΩΝ ΑΝΑΡΓΥΡΩΝ": [210],
    "5ο ΓΕΛ ΑΧΑΡΝΩΝ ΑΓΙΑ ΑΝΝΑ": [245],
    "1ο Γυμνάσιο Καματερού": [237],
    "1ο ΕΠΑΛ ΝΕΑΣ ΙΩΝΙΑΣ ΑΤΤΙΚΗΣ": [386],
    "4ο Δημοτικό σχολείο Περάματος": [384],
    "1ο ΓΕΛ ΚΕΡΑΤΣΙΝΙΟΥ": [208],
    "3ο ΓΕΛ ΑΧΑΡΝΩΝ": [194],
    "1ο ΓΕΛ ΝΕΑΣ ΦΙΛΑΔΕΛΦΕΙΑΣ": [382],
    "ΓΕΛ ΛΑΥΡΙΟΥ": [250],
    "5ο ΔΗΜΟΤΙΚΟ ΣΧΟΛΕΙΟ ΚΕΡΑΤΣΙΝΙΟΥ": [390],
    "1ο ΕΠΑΛ Αγίων Αναργύρων": [274],
    "ΓΥΜΝΑΣΙΟ ΑΝΘΟΥΣΑΣ": [244],
    "1ο ΓΥΜΝΑΣΙΟ ΠΕΥΚΗΣ": [246],
    "2ο Γυμνάσιο Καισαριανής": [272],
    "3 ΓΥΜΝΑΣΙΟ ΙΛΙΟΥ": [389],
    "1ο Εσπερινό Γυμνάσιο ΑΘΗΝΩΝ": [188],
    "ΣΧΟΛΗ ΜΩΡΑΪΤΗ-ΟΜΙΛΟΣ ΠΑΡΑΤΗΡΗΣΗΣ & ΕΡΜΗΝΕΙΑΣ ΤΗΣ ΦΥΣΗΣ": [236],
    "6ο ΓΕΛ Περιστερίου": [199],
    "6ο Γυμνάσιο Ζωγράφου": [198],
    "10o ΓΕΛ ΠΕΡΙΣΤΕΡΙΟΥ": [202],
    "11ο ΔΗΜΟΤΙΚΟ ΣΧΟΛΕΙΟ ΑΜΑΡΟΥΣΙΟΥ": [374],
    "1o ΓΥΜΝΑΣΙΟ ΝΕΑΣ ΦΙΛΑΔΕΛΦΕΙΑΣ": [392],
    "1o ΔΗΜΟΤΙΚΟ ΣΧΟΛΕΙΟ ΝΕΑΣ ΣΜΥΡΝΗΣ": [379],
    "1ο ΓΕΝΙΚΟ ΛΥΚΕΙΟ ΚΑΜΑΤΕΡΟΥ": [388],
    "1ο Γυμνάσιο Κηφησιάς": [260],
    "1ο Γυμνάσιο Ραφήνας": [376],
    "26ο ΓΕΛ ΑΘΗΝΩΝ": [207],
    "2ο ΓΕΝΙΚΟ ΛΥΚΕΙΟ ΣΑΛΑΜΙΝΑΣ": [393],
    "2ο Γενικό Λύκειο Χολαργού": [387],
    "3o ΓΥΜΝΑΣΙΟ ΠΕΡΙΣΤΕΡΙΟΥ": [397],
    "3ο Γυμνάσιο Γαλατσίου": [251],
    "3ο Γυμνάσιο Χαϊδαρίου": [235],
    "3ο ΔΗΜ.ΣΧ.ΑΡΓΥΡΟΥΠΟΛΗΣ": [380],
    "49ο ΓΕ.Λ. Αθηνών": [373],
    "4o ΓΥΜΝΑΣΙΟ ΑΙΓΑΛΕΩ": [383],
    "4ο ΓΕΛ ΑΘΗΝΩΝ": [381],
    "4ο Δημοτικό Σχολείο Αλίμου": [391],
    "7o ΓΕΛ ΠΕΙΡΑΙΑ": [375],
    "7ο ΗΜΕΡΗΣΙΟ ΓΕΝΙΚΟ ΛΥΚΕΙΟ ΑΧΑΡΝΩΝ": [378],
    "ΓΕΛ ΨΥΧΙΚΟΥ": [377],
    "ΓΥΜΝΑΣΙΟ Ν. ΧΑΛΚΗΔΟΝΑΣ": [385],
    "ARSINOE": [None],
}

main_project = 186


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
        url_obs = f"{API_PATH}/observations?project_id={place_id}&created_d1={start_date}&created_d2={end_date}"
        url_spe = f"{API_PATH}/observations/species_counts?project_id={place_id}&created_d1={start_date}&created_d2={end_date}"
        url_part = f"{API_PATH}/observations/observers?project_id={place_id}&created_d1={start_date}&created_d2={end_date}"
        url_ident = f"{API_PATH}/observations/identifiers?project_id={place_id}&created_d1={start_date}&created_d2={end_date}"
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


def get_obs_from_project_places(places):
    for k, v in places.items():

        total_obs = []
        for i in range(len(v)):
            if v[i] is None:
                continue
            obs = get_obs(id_project=v[i])
            total_obs.extend(obs)
        if len(total_obs) > 0:
            df1, __ = get_dfs(total_obs)
            df1.to_csv(f"{directory}/data/obs_{v[i]}.csv", index=False)
            # df2.to_csv(f"{directory}/data/photos_{k}.csv")
        else:
            print(f"No hay observaciones para {v[i]}")


def get_obs_from_main_project(main_project):
    obs = get_obs(id_project=main_project)
    df_obs, df_photos = get_dfs(obs)
    df_obs.to_csv(f"{directory}/data/{main_project}_obs.csv", index=False)
    df_photos.to_csv(f"{directory}/data/{main_project}_photos.csv", index=False)


def update_main_metrics(proj_id, df_main_metrics, session=None):
    # Fecha de inicio del proyecto
    fecha_inicio_proyecto = datetime(2023, 10, 16)

    results = []

    observations = f"{API_PATH}/observations?"
    species = f"{API_PATH}/observations/species_counts?"
    observers = f"{API_PATH}/observations/observers?"
    identifiers = f"{API_PATH}/observations/identifiers?"

    # Crear una sesión de requests si no se proporciona
    if session is None:
        session = requests.Session()

    # Fecha inicial para la actualización
    day = fecha_inicio_proyecto

    # Calcular el rango de días desde la fecha de inicio hasta hoy
    rango_temporal = (datetime.today().date() - day.date()).days

    for i in range(rango_temporal + 1):
        print(f"Procesando día {i}: {day.strftime('%Y-%m-%d')}")
        st_day = day.strftime("%Y-%m-%d")

        params = {
            "project_id": proj_id,
            "created_d2": st_day,
            "order": "desc",
            "order_by": "created_at",
        }

        # Realizar las solicitudes a la API
        total_obs = (
            session.get(observations, params=params).json().get("total_results", 0)
        )
        total_species = (
            session.get(species, params=params).json().get("total_results", 0)
        )
        total_participants = (
            session.get(observers, params=params).json().get("total_results", 0)
        )
        total_identifiers = (
            session.get(identifiers, params=params).json().get("total_results", 0)
        )

        result = {
            "date": st_day,
            "observations": total_obs,
            "species": total_species,
            "observers": total_participants,
            "identifiers": total_identifiers,
        }

        results.append(result)
        day += timedelta(days=1)

    result_df = pd.DataFrame(results)

    print("Updated main metrics")
    return result_df


def get_metrics_cities(main_project, places, session=None):
    result = []
    del places["ARSINOE"]

    species = "https://api.minka-sdg.org/v1/observations/species_counts?"
    observers = "https://api.minka-sdg.org/v1/observations/observers?"
    observations = "https://api.minka-sdg.org/v1/observations?"
    if session is None:
        session = requests.Session()

    for k, v in places.items():
        if len(v) == 1:
            url1 = f"{species}&project_id={v[0]}"
            total_species = session.get(url1).json()["total_results"]

            url2 = f"{observers}&project_id={v[0]}"
            total_participants = session.get(url2).json()["total_results"]

            url3 = f"{observations}&project_id={v[0]}"
            total_obs = session.get(url3).json()["total_results"]

        else:
            total_species = 0
            total_participants = 0
            total_obs = 0

            for place_v in v:
                url1 = f"{species}&project_id={place_v}"
                total_species += session.get(url1).json()["total_results"]

                url2 = f"{observers}&project_id={place_v}"
                total_participants += session.get(url2).json()["total_results"]

                url3 = f"{observations}&project_id={place_v}"
                total_obs += session.get(url3).json()["total_results"]
        data = {
            "city": k,
            "species": total_species,
            "observers": total_participants,
            "observations": total_obs,
        }
        result.append(data)
    main_metrics = pd.DataFrame(result)
    return main_metrics


def get_num_species(main_project, session=None):
    if session is None:
        session = requests.Session()
    num_species = []
    base_url = "https://api.minka-sdg.org/v1/observations/species_counts?"
    start_date = datetime(2023, 10, 16)
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


def _get_identifiers(user_name, proj_id, session=None):
    if session is None:
        session = requests.Session()
    identifiers = f"{API_PATH}/observations/identifiers"
    params = {"project_id": proj_id, "user_login": user_name}
    return session.get(identifiers, params=params).json()["total_results"]


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
    pt_users["identificacions"] = pt_users["participant"].apply(
        lambda x: _get_identifiers(x, main_project, session)
    )
    pt_users["espècies"] = pt_users["participant"].apply(
        lambda x: _get_species(x, main_project, session)
    )
    return pt_users


if __name__ == "__main__":
    start_time = time.time()

    session = requests.Session()

    print("Actualizando métricas acumulativas del proyecto principal")
    try:
        df_main_metrics = pd.read_csv(
            f"{directory}/data/{main_project}_main_metrics.csv"
        )
        result_df = update_main_metrics(main_project, df_main_metrics, session)
        result_df.to_csv(
            f"{directory}/data/{main_project}_main_metrics.csv", index=False
        )
    except FileNotFoundError:
        print("No se encontraron datos previos. Descargando métricas desde cero.")
        df_main_metrics = update_main_metrics(main_project, pd.DataFrame(), session)
        df_main_metrics.to_csv(
            f"{directory}/data/{main_project}_main_metrics.csv", index=False
        )

    print("Descargando métricas mensuales de los places del proyecto")
    current_year = datetime.now().year
    years = list(range(2023, current_year + 1))
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
    get_obs_from_project_places(places)

    print("Incluyendo school en datos del main project")
    df_obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")
    for school, school_id in places.items():
        try:
            df_city = pd.read_csv(f"{directory}/data/obs_{school_id[0]}.csv")
            df_obs.loc[df_obs["id"].isin(df_city["id"].to_list()), "address"] = (
                school_id[0]
            )
        except FileNotFoundError:
            print(f"No se encontraron datos para {school}")
    df_obs.to_csv(f"{directory}/data/{main_project}_obs.csv", index=False)

    print("Descargando especies introducidas")
    df_introduced_by_month = get_num_species(main_project, session)
    df_introduced_by_month.to_csv(
        f"{directory}/data/introduced_by_month.csv", index=False
    )

    print("Descargando tabla de participantes")
    pt_users = get_participation_df(main_project)
    pt_users.to_csv(f"{directory}/data/{main_project}_observers.csv", index=False)

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Tiempo de ejecución {(execution_time / 60):.2f} minutos")
