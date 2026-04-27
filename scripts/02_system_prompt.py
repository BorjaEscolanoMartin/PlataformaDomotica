import requests
import ollama
import sys
sys.path.insert(0, ".")
from config import OPENHAB_URL, HEADERS_JSON, MODELO

def obtener_items():
    response = requests.get(f"{OPENHAB_URL}/rest/items", headers=HEADERS_JSON, timeout=10)
    if response.status_code == 200:
        return response.json()
    return []

def construir_system_prompt(items):
    luces = [i for i in items if i.get("type") == "Switch" and "Lightbulb" in i.get("tags", [])]
    clima = [i for i in items if i.get("type") in ("Switch", "Number:Temperature") and i.get("name", "").startswith("AC_")]
    estancias = [i for i in items if i.get("type") == "Group" and i.get("tags", []) not in (["Location"], ["Building"], ["Outdoor"])]

    def estado(item):
        s = item.get("state", "NULL")
        return s if s != "NULL" else "desconocido"

    luces_txt = "\n".join(f"  - {i['name']} ({i.get('label','')}) → {estado(i)}" for i in luces)
    clima_txt = "\n".join(f"  - {i['name']} ({i.get('label','')}) → {estado(i)}" for i in clima)
    estancias_txt = "\n".join(f"  - {i['name']} ({i.get('label','')})" for i in estancias)

    return (
        "Eres el gestor inteligente del sistema domótico del IES Sequeros. "
        "Responde siempre en español, de forma concisa.\n\n"
        f"LUCES ({len(luces)} en total):\n{luces_txt}\n\n"
        f"CLIMATIZACIÓN:\n{clima_txt}\n\n"
        f"ESTANCIAS:\n{estancias_txt}"
    )

def main():
    print("Obteniendo dispositivos desde OpenHAB...")
    items = obtener_items()

    if not items:
        print("Error: no se pudieron obtener los items de OpenHAB. ¿Está corriendo el contenedor?")
        return

    print(f"  {len(items)} items cargados.\n")
    system_prompt = construir_system_prompt(items)
    mensajes = [{"role": "system", "content": system_prompt}]

    print("Chat con contexto domótico (escribe 'salir' para terminar)\n")

    while True:
        entrada = input("Tú: ")
        if entrada.lower() == "salir":
            break

        mensajes.append({"role": "user", "content": entrada})

        print("\nIA: ", end="", flush=True)
        respuesta = ""
        for chunk in ollama.chat(
            model=MODELO,
            messages=mensajes,
            options={"num_ctx": 4096},
            think=False,
            stream=True
        ):
            token = chunk["message"]["content"]
            print(token, end="", flush=True)
            respuesta += token
        print("\n")

        mensajes.append({"role": "assistant", "content": respuesta})

if __name__ == "__main__":
    main()
