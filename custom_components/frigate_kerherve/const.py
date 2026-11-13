"""Constantes de Frigate Kerherve."""

DOMAIN = "frigate_kerherve"
CONF_URL = "url"
DEFAULT_URL = "http://ccab4aaf-frigate-fa:5000"
SCAN_INTERVAL_SECONDS = 60

# Seuils du capteur « problème » par caméra (sur la dernière heure).
PROBLEM_RECONNECTS = 5
PROBLEM_STALLS = 20
