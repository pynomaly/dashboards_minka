#!/bin/bash
echo 
echo 
date
source /home/pynomaly/dashboards_minka/.env/bin/activate
export DASHBOARDS="/home/pynomaly/dashboards_minka"
python /home/pynomaly/dashboards_minka/internal-analytics/download_observations.py
python /home/pynomaly/dashboards_minka/internal-analytics/download_identifications.py
