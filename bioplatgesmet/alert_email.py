import os
import smtplib
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText

import pandas as pd
from dotenv import load_dotenv

try:
    directory = f"{os.environ['DASHBOARDS']}/bioplatgesmet"
except KeyError:
    print(
        "Configura la variable de entorno DASHBOARDS en .bashrc apuntando al directorio de los dashboards."
    )


# Funciones


def enviar_email_html_csic(
    destinatarios, asunto, cuerpo_html, usuario, password, remitente_email
):
    """
    Envía un correo electrónico HTML a uno o varios destinatarios a través del servidor SMTP del CSIC.

    Args:
        destinatarios: Lista de direcciones de correo electrónico (incluso si es un solo destinatario)
        asunto: Asunto del correo
        cuerpo_html: Contenido del correo en formato HTML
        usuario: Nombre de usuario para autenticación SMTP
        password: Contraseña para autenticación SMTP
        remitente_email: Dirección de correo del remitente

    Returns:
        Mensaje indicando éxito o error
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    servidor_smtp = os.getenv("EMAIL_SERVER")
    puerto_smtp = 587

    # Verificar que destinatarios sea una lista
    if not isinstance(destinatarios, (list, tuple)):
        raise TypeError(
            "El parámetro 'destinatarios' debe ser una lista o tupla de direcciones de correo, incluso para un solo destinatario"
        )

    # Crear mensaje con partes alternativas (texto plano y HTML)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = remitente_email
    msg["To"] = ", ".join(destinatarios)

    # Crear una versión de texto plano del mensaje HTML (simplificada)
    import re

    texto_plano = re.sub("<.*?>", " ", cuerpo_html)
    texto_plano = re.sub(r"\s+", " ", texto_plano).strip()

    # Adjuntar ambas versiones al mensaje
    part1 = MIMEText(texto_plano, "plain")
    part2 = MIMEText(cuerpo_html, "html")

    # La última parte añadida es la preferida por el cliente de correo
    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP(servidor_smtp, puerto_smtp) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(usuario, password)
            servidor.sendmail(remitente_email, destinatarios, msg.as_string())
        return "¡Correo enviado con éxito!"
    except Exception as e:
        return f"Error al enviar: {str(e)}"


def get_message(grupo: str, df_obs: pd.DataFrame, days: int) -> str:
    """Get message for a group of species."""
    # Leer el archivo de especies
    df_grupo = pd.read_csv(f"{directory}/data/species/{grupo}.csv")
    species_ids = df_grupo.taxon_id.to_list()

    # Filtrar las observaciones del grupo y ordenar por más recientes
    last_obs = df_obs[df_obs.taxon_id.isin(species_ids)].sort_values(
        by="observed_on", ascending=False
    )

    # Filtrar observaciones de los últimos x días
    fecha_actual = date.today()
    limite = fecha_actual - timedelta(days=days)
    last_week = last_obs[
        last_obs.observed_on >= limite.strftime("%Y-%m-%d")
    ].reset_index(drop=True)

    msg = ""

    # Agrupamos las observaciones por taxon_name y contamos cada grupo
    if len(last_week) > 0:

        grouped = last_week.groupby("taxon_name")

        # Ordenar los grupos por el tamaño de cada grupo, de mayor a menor
        sorted_groups = sorted(grouped, key=lambda x: len(x[1]), reverse=True)

        for taxon_name, group in sorted_groups:
            msg += f"- <b>{taxon_name}</b>: {len(group)} observacions\n"

            # Iteramos en cada observación dentro del grupo para agregar detalles
            for _, row in group.iterrows():
                # Construimos fecha con formato DD-MM-YYYY
                fecha = f"{row['observed_on'][-2:]}-{row['observed_on'][-5:-3]}-{row['observed_on'][0:4]}"
                msg += (
                    f"    - Registrat el {fecha} a {row['address']} por <i>{row['user_login']}</i>: "
                    f"https://minka-sdg.org/observations/{row['id']} \n"
                )

    else:

        msg = f"Cap observació registrada."
    return msg


def get_message_html(grupo: str, df_obs: pd.DataFrame, days: int) -> str:
    """
    Genera un mensaje en formato HTML enriquecido para un grupo de especies.

    Args:
        grupo: Nombre del grupo de especies ('invasoras', 'alerta', etc.)
        df_obs: DataFrame con observaciones
        days: Número de días hacia atrás para filtrar observaciones

    Returns:
        Mensaje en formato HTML enriquecido
    """
    # Leer el archivo de especies
    df_grupo = pd.read_csv(f"{directory}/data/species/{grupo}.csv")
    species_ids = df_grupo.taxon_id.to_list()

    # Filtrar las observaciones del grupo y ordenar por más recientes
    last_obs = df_obs[df_obs.taxon_id.isin(species_ids)].sort_values(
        by="observed_on", ascending=False
    )

    # Filtrar observaciones de los últimos x días
    fecha_actual = date.today()
    limite = fecha_actual - timedelta(days=days)
    last_week = last_obs[
        last_obs.observed_on >= limite.strftime("%Y-%m-%d")
    ].reset_index(drop=True)

    # Iniciar la construcción del mensaje HTML
    if len(last_week) > 0:
        # Comenzar con un div contenedor con estilo
        html = '<div style="font-family: Arial, sans-serif; line-height: 1.6;">'

        # Agrupar por taxon_name y contar cada grupo
        grouped = last_week.groupby("taxon_name")

        # Ordenar los grupos por el tamaño de cada grupo, de mayor a menor
        sorted_groups = sorted(grouped, key=lambda x: len(x[1]), reverse=True)

        for taxon_name, group in sorted_groups:
            # Nombre de la especie con formato y conteo
            html += f'<h3 style="color: #336699; margin-bottom: 5px; margin-top: 15px;">{taxon_name} <span style="color: #666;">({len(group)} observacions)</span></h3>'

            # Crear una tabla para las observaciones
            html += '<table style="width: 100%; margin-left: 20px; margin-bottom: 15px; border-collapse: collapse;">'
            html += '<tr style="background-color: #f2f2f2;"><th style="text-align: left; padding: 8px;">Data</th><th style="text-align: left; padding: 8px;">Ubicació</th><th style="text-align: left; padding: 8px;">Usuari</th><th style="text-align: left; padding: 8px;">Enllaç</th></tr>'

            # Iterar en cada observación para agregar filas a la tabla
            for i, row in enumerate(group.iterrows()):
                row = row[1]  # Obtener la serie de datos
                # Formato de fecha DD-MM-YYYY
                fecha = f"{row['observed_on'][-2:]}-{row['observed_on'][-5:-3]}-{row['observed_on'][0:4]}"

                # Alternar colores de fondo para filas
                bg_color = "#ffffff" if i % 2 == 0 else "#f9f9f9"

                html += f'<tr style="background-color: {bg_color};">'
                html += f'<td style="padding: 6px;">{fecha}</td>'
                html += f'<td style="padding: 6px;">{row["address"]}</td>'
                html += f'<td style="padding: 6px;"><i>{row["user_login"]}</i></td>'
                html += f'<td style="padding: 6px;"><a href="https://minka-sdg.org/observations/{row["id"]}" style="color: #0066cc; text-decoration: none;">Veure</a></td>'
                html += "</tr>"

            html += "</table>"

        html += "</div>"
    else:
        html = (
            '<p style="color: #666; font-style: italic;">Cap observació registrada.</p>'
        )

    return html


def compose_final_html_message(msg_invasoras_html, msg_alerta_html):
    """
    Compone un mensaje HTML final que incluye las secciones de especies invasoras y de interés.

    Args:
        msg_invasoras_html: Mensaje HTML de especies invasoras
        msg_alerta_html: Mensaje HTML de especies de interés

    Returns:
        Mensaje HTML completo
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Informe d'espècies - MINKA Bioplatgesmet</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #336699;">Alerta de Noves Espècies</h1>
            <p style="color: #666;">MINKA Bioplatgesmet</p>
        </div>
    """

    # Añadir sección de especies invasoras si hay datos
    if "Cap observació registrada" not in msg_invasoras_html:
        html += f"""
        <div style="margin-bottom: 30px; border: 1px solid #f0f0f0; border-radius: 5px; padding: 15px;">
            <h2 style="color: #f85531; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">Noves espècies invasores registrades</h2>
            {msg_invasoras_html}
        </div>
        """

    # Añadir sección de especies de interés si hay datos
    if "Cap observació registrada" not in msg_alerta_html:
        html += f"""
        <div style="margin-bottom: 30px; border: 1px solid #f0f0f0; border-radius: 5px; padding: 15px;">
            <h2 style="color: #B60505; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">Noves espècies monitoritzades registrades</h2>
            {msg_alerta_html}
        </div>
        """

    html += """
        <div style="text-align: center; margin-top: 30px; font-size: 0.9em; color: #666; border-top: 1px solid #f0f0f0; padding-top: 15px;">
            <p>Per més informació, visiti <a href="https://dashboard.minka-sdg.org/bioplatgesmet/destacats" style="color: #0066cc; text-decoration: none;">dashboard.minka-sdg.org/bioplatgesmet/destacats</a></p>
        </div>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":

    main_project = 264
    days = 1
    df_obs = pd.read_csv(f"{directory}/data/{main_project}_obs.csv")

    load_dotenv()
    email_password = os.getenv("EMAIL_PASSWORD")
    email_address = os.getenv("EMAIL")
    email_user = os.getenv("EMAIL_USER")
    email_to = os.getenv("EMAIL_TO").split(",")

    # Generar mensajes HTML para cada grupo
    msg_invasoras_html = get_message_html("invasoras", df_obs, days)
    msg_alerta_html = get_message_html("alerta", df_obs, days)

    # Componer el mensaje final
    final_html_message = compose_final_html_message(msg_invasoras_html, msg_alerta_html)

    if "Noves espècies" in final_html_message:
        # Configurar y enviar el email HTML
        config = {
            "usuario": email_user,  # Solo el usuario, NO el email
            "password": email_password,
            "remitente_email": email_address,
            "destinatarios": email_to,
            "asunto": "[MINKA - Bioplatgesmet] Noves espècies registrades",
            "cuerpo_html": final_html_message,
        }

        resultado = enviar_email_html_csic(
            destinatarios=config["destinatarios"],
            asunto=config["asunto"],
            cuerpo_html=config["cuerpo_html"],
            usuario=config["usuario"],
            password=config["password"],
            remitente_email=config["remitente_email"],
        )
        print(resultado)
    else:
        print("Ninguna especie nueva. Mensaje no enviado.")
