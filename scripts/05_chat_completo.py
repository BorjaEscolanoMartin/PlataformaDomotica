import requests
import ollama
import json
import threading
import sys
sys.path.insert(0, ".")
from config import OPENHAB_URL, API_TOKEN, HEADERS_REST, HEADERS_JSON, MODELO

herramientas = [
    {
        "type": "function",
        "function": {
            "name": "actuar_openhab",
            "description": "Controla dispositivos del IES (luces ON/OFF, clima con números). Usa nombres técnicos de Item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device": {"type": "string", "description": "Nombre técnico del item, ej: Luz_Direccion"},
                    "value":  {"type": "string", "description": "Valor a enviar: ON, OFF, o un número"},
                },
                "required": ["device", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_items_openhab",
            "description": "Obtiene la lista completa de dispositivos, nombres técnicos y estados actuales.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

SYSTEM_PROMPT = (
    "Eres el gestor inteligente del sistema domótico del IES Sequeros. "
    "Controlas dispositivos mediante openHAB. "
    "REGLAS IMPORTANTES:\n"
    "- Para luces SIEMPRE usa ON (encender) y OFF (apagar) en MAYÚSCULAS.\n"
    "- Para temperaturas usa valores numéricos.\n"
    "- Usa los nombres técnicos exactos de los items.\n"
    "Items de luces: Luz_Secretaria, Luz_Direccion, Luz_Jefatura, "
    "Luz_Conserjeria, Luz_SalaProfesores, Luz_PatioNorte, Luz_PatioSur.\n"
    "Items de clima: AC_Power (ON/OFF), AC_CurrentTemp (lectura), AC_Setpoint (número)."
)

mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
lock = threading.Lock()


def ejecutar_actuador(device, value):
    r = requests.post(f"{OPENHAB_URL}/rest/items/{device}", headers=HEADERS_REST, data=value, timeout=5)
    return f"OK: {device} → {value}" if r.status_code in (200, 202) else f"Error {r.status_code}"


def listar_items():
    r = requests.get(f"{OPENHAB_URL}/rest/items", headers=HEADERS_JSON, timeout=10)
    if r.status_code != 200:
        return "Error al obtener items"
    return "\n".join(
        f"{i['name']} ({i.get('label','')}) → {i.get('state','NULL')}"
        for i in r.json() if i.get("type") != "Group"
    )


def chat_con_ia(texto, es_evento=False):
    with lock:
        prefijo = "\n[Evento] " if es_evento else "\nTú: "
        print(f"{prefijo}{texto}")

        mensajes.append({"role": "user", "content": texto})

        response = ollama.chat(
            model=MODELO,
            messages=mensajes,
            tools=herramientas,
            think=False,
        )

        if response.message.tool_calls:
            mensajes.append(response.message.model_dump())
            for tool in response.message.tool_calls:
                if tool.function.name == "actuar_openhab":
                    resultado = ejecutar_actuador(
                        tool.function.arguments["device"],
                        tool.function.arguments["value"],
                    )
                elif tool.function.name == "listar_items_openhab":
                    resultado = listar_items()
                else:
                    resultado = "Tool desconocida"
                print(f"  [tool] {tool.function.name}({tool.function.arguments}) → {resultado}")
                mensajes.append({"role": "tool", "content": resultado, "name": tool.function.name})

        print("\nIA: ", end="", flush=True)
        respuesta = ""
        for chunk in ollama.chat(model=MODELO, messages=mensajes, think=False, stream=True):
            token = chunk["message"]["content"]
            print(token, end="", flush=True)
            respuesta += token
        print("\n")
        mensajes.append({"role": "assistant", "content": respuesta})


def listener_sse():
    url = f"{OPENHAB_URL}/rest/events"
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "text/event-stream"}

    while True:
        try:
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
                            chat_con_ia(f"El item {item} cambió de {antiguo} a {valor}", es_evento=True)
                    except (json.JSONDecodeError, IndexError):
                        continue
        except Exception:
            import time
            time.sleep(5)


def main():
    print("Chat completo con SSE (escribe 'salir' para terminar)\n")

    hilo = threading.Thread(target=listener_sse, daemon=True)
    hilo.start()

    while True:
        try:
            entrada = input("Tú: ")
        except EOFError:
            break
        if entrada.lower() == "salir":
            break
        chat_con_ia(entrada)


if __name__ == "__main__":
    main()
