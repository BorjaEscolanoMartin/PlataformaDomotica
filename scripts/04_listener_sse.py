import requests
import json
import sys
sys.path.insert(0, ".")
from config import OPENHAB_URL, API_TOKEN

def listener():
    url = f"{OPENHAB_URL}/rest/events"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "text/event-stream",
    }

    print(f"Conectando a {url}...")
    print("Esperando eventos (mueve un slider en OpenHAB para ver cambios)...\n")

    with requests.get(url, headers=headers, stream=True, timeout=None) as r:
        for line in r.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8")
            if not decoded.startswith("data:"):
                continue
            try:
                data = json.loads(decoded[5:])
                if data.get("type") == "ItemStateChangedEvent":
                    item = data["topic"].split("/")[2]
                    payload = json.loads(data["payload"])
                    valor = payload.get("value")
                    antiguo = payload.get("oldValue")
                    print(f"[SSE] {item}: {antiguo} → {valor}")
            except (json.JSONDecodeError, IndexError):
                continue

if __name__ == "__main__":
    listener()
