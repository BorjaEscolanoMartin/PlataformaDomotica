# config.py — Variables compartidas para todos los scripts
# Reemplazar API_TOKEN con el token generado en OpenHAB tras el primer arranque

OPENHAB_URL = "http://localhost:8080"
API_TOKEN = "oh.practicaLLM.4cfgpsLWaKMnM6jEw3WxmUKmbbZrZaHjX7bT4yTeddhEdEp9nDoxeHRTx94w4vw91rNjuTleBALX4IOCg"

HEADERS_REST = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "text/plain"
}

HEADERS_JSON = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/json"
}

MODELO = "qwen3.5:2b"
