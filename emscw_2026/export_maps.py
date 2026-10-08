"""
Script para exportar mapas de coropletas a PNG
Ejecutar: python export_maps.py
"""

import os

import geopandas as gpd
import pandas as pd
import plotly.express as px

# Configuración
DIRECTORY = os.environ.get("DASHBOARDS", ".") + "/biodiverciutat_26"
MAIN_PROJ = 522
COLORS = ["#c5e8eb", "#5fb8c4", "#007c8a"]

# Métricas a exportar
METRICS = {
    "Observacions": "observacions",
    "Espècies": "especies",
    "Participants": "participants",
}


def create_geo_df():
    """Carga y prepara el GeoDataFrame con los datos"""
    archivo_geojson = f"{DIRECTORY}/data/divisions-administratives-cat-20240118/divisions-administratives-municipis-20240118.json"
    datos_geojson = gpd.read_file(archivo_geojson)

    df_projects = pd.read_csv(f"{DIRECTORY}/data/{MAIN_PROJ}_main_metrics_projects.csv")

    datos_completos = pd.merge(
        datos_geojson, df_projects, left_on="NOMMUNI", right_on="city", how="right"
    )

    datos_completos.rename(
        columns={
            "AREAM5000": "Area",
            "observations": "Observacions",
            "species": "Espècies",
            "participants": "Participants",
        },
        inplace=True,
    )

    datos_completos["Area"] = round(datos_completos["Area"], 2)
    datos_completos.index = datos_completos.Area.astype(str)

    # Excluir área marina
    mask = datos_completos["project"] != 499
    return datos_completos[mask]


def export_map(datos_mapa, color_option, color_label, output_path):
    """Genera y exporta un mapa de coropletas a PNG"""
    fig = px.choropleth_map(
        data_frame=datos_mapa,
        geojson=datos_mapa.geometry.__geo_interface__,
        locations=datos_mapa["Area"],
        color=color_option,
        color_continuous_scale=COLORS,
        zoom=10.5,
        center={"lat": 41.4, "lon": 2.05},
        opacity=1,
        hover_name="city",
        hover_data={color_option: True, "Area": False},
        height=1200,
        map_style="white-bg",
    )

    fig.update_coloraxes(
        colorbar_title_text=color_label,
        colorbar_orientation="h",
        colorbar_y=-0.05,
        colorbar_len=0.5,
        colorbar_thickness=20,
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
    )

    fig.write_image(output_path, scale=3, width=1600, height=1200)
    print(f"Mapa exportado: {output_path}")


def main():
    print("Cargando datos...")
    datos_mapa = create_geo_df()

    print(f"Exportando mapas a {DIRECTORY}/data/")

    for metric_col, metric_name in METRICS.items():
        output_path = f"{DIRECTORY}/data/mapa_{metric_name}.png"
        export_map(datos_mapa, metric_col, metric_col, output_path)

    print("Completado!")


if __name__ == "__main__":
    main()
