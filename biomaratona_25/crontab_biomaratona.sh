#!/bin/bash
echo 
echo 
date
source /home/pynomaly/dashboards_minka/.env/bin/activate
export DASHBOARDS="/home/pynomaly/dashboards_minka"
python /home/pynomaly/dashboards_minka/biomaratona_25/update.py
