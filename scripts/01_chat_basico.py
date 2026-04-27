import ollama

MODELO = "qwen3.5:2b"

def main():
    mensajes = [
        {
            "role": "system",
            "content": (
                "Eres un asistente de gestión de un centro educativo. "
                "Respondes de forma concisa y amable en español."
            )
        }
    ]

    print("Chat básico con Ollama (escribe 'salir' para terminar)\n")

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
