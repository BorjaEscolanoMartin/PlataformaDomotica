import requests
import ollama
import sys
sys.path.insert(0, ".")
from config import OPENHAB_URL, HEADERS_REST, HEADERS_JSON, MODELO

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


def ejecutar_actuador(device, value):
    url = f"{OPENHAB_URL}/rest/items/{device}"
    r = requests.post(url, headers=HEADERS_REST, data=value, timeout=5)
    if r.status_code in (200, 202):
        return f"OK: {device} → {value}"
    return f"Error {r.status_code}: {device} → {value}"


def listar_items():
    r = requests.get(f"{OPENHAB_URL}/rest/items", headers=HEADERS_JSON, timeout=10)
    if r.status_code != 200:
        return "Error al obtener items"
    items = r.json()
    lineas = []
    for i in items:
        if i.get("type") == "Group":
            continue
        estado = i.get("state", "NULL")
        lineas.append(f"{i['name']} ({i.get('label','')}) → {estado}")
    return "\n".join(lineas)


def main():
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Control domótico con tools (escribe 'salir' para terminar)\n")

    while True:
        entrada = input("Tú: ")
        if entrada.lower() == "salir":
            break

        mensajes.append({"role": "user", "content": entrada})

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
            for chunk in ollama.chat(
                model=MODELO,
                messages=mensajes,
                think=False,
                stream=True,
            ):
                token = chunk["message"]["content"]
                print(token, end="", flush=True)
                respuesta += token
            print("\n")
            mensajes.append({"role": "assistant", "content": respuesta})

        else:
            print("\nIA: ", end="", flush=True)
            respuesta = ""
            for chunk in ollama.chat(
                model=MODELO,
                messages=mensajes,
                think=False,
                stream=True,
            ):
                token = chunk["message"]["content"]
                print(token, end="", flush=True)
                respuesta += token
            print("\n")
            mensajes.append({"role": "assistant", "content": respuesta})


if __name__ == "__main__":
    main()
