echo
echo
date
source /home/pynomaly/dashboards_minka/.env/bin/activate
export DASHBOARDS="/home/pynomaly/dashboards_minka"
python /home/pynomaly/dashboards_minka/emscw_2026/update.py
