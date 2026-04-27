## Descripción General

Proyecto de integración de un modelo de lenguaje local (LLM) ejecutado con **Ollama** y la plataforma de domótica **OpenHAB**, aplicado a la gestión inteligente de un centro educativo ficticio (IES Sequeros). El sistema permite controlar dispositivos domóticos mediante lenguaje natural, usando *function calling* (tools) y escucha reactiva de eventos SSE.

---

## Arquitectura del Sistema

```
┌─────────────┐     HTTP/REST      ┌──────────────┐
│   Ollama     │◄──────────────────►│   OpenHAB    │
│  (LLM local) │                    │  (Domótica)  │
└──────┬───────┘                    └──────┬───────┘
       │                                   │
       │  Librería ollama (Python)         │  API REST :8080
       │                                   │  SSE /rest/events
       ▼                                   ▼
┌──────────────────────────────────────────────┐
│          Script Python (Middleware)           │
│  - Chat interactivo con ventana de contexto  │
│  - Tools: actuar_openhab, listar_items       │
│  - Hilo SSE: escucha eventos en tiempo real  │
│  - Lógica reactiva de climatización          │
└──────────────────────────────────────────────┘
```

---

## Requisitos Previos

- **Docker** y **Docker Compose** instalados
- **Ollama** instalado (`curl -fsSL https://ollama.com/install.sh | sh`)
- **Python 3.10+** con pip
- Dependencias Python: `ollama`, `requests`
- Un modelo Ollama con soporte de **tools** (mínimo `qwen3.5:2b`)

---

## Estructura del Proyecto

```
proyecto-llm-openhab/
├── README.md                    # Este archivo
├── compose.yml                  # Docker Compose para OpenHAB
├── openhab_addons/              # Carpeta para complementos (vacía)
├── openhab_conf/                # Configuración de OpenHAB
│   └── items/
│       └── ies_sequeros.items   # Definición de dispositivos del IES
├── openhab_userdata/            # Datos persistentes de OpenHAB
├── scripts/
│   ├── 01_chat_basico.py        # Ejercicio 4: Chat con ventana de contexto
│   ├── 02_system_prompt.py      # Ejercicio 5-6: System prompt dinámico desde API
│   ├── 03_tool_luces.py         # Ejercicio 7: Tool de control de luces
│   ├── 04_listener_sse.py       # Ejercicio 10: Listener SSE básico
│   ├── 05_chat_completo.py      # Ejercicio 11: Chat + SSE integrado
│   └── 06_reactivo_clima.py     # Ejercicio 12: Lógica reactiva climatización
└── config.py                    # Variables compartidas (URL, TOKEN, MODELO)
```

---

## Plan de Ejecución por Fases

### FASE 1 — Infraestructura Docker + OpenHAB (Ejercicios 1-3)

**Objetivo:** Levantar OpenHAB en Docker y definir los dispositivos del IES Sequeros.

**Pasos:**

1. Crear las tres carpetas de volúmenes en la raíz del proyecto:
   - `openhab_addons/`
   - `openhab_conf/items/`
   - `openhab_userdata/`

2. Crear el fichero `compose.yml` con el siguiente contenido:

```yaml
services:
  openhab:
    image: "openhab/openhab:5.1.3"
    restart: always
    network_mode: host
    volumes:
      - "./openhab_addons:/openhab/addons"
      - "./openhab_conf:/openhab/conf"
      - "./openhab_userdata:/openhab/userdata"
    environment:
      CRYPTO_POLICY: "unlimited"
      OPENHAB_HTTP_PORT: "8080"
      OPENHAB_HTTPS_PORT: "8443"
      TZ: "Europe/Madrid"
```

3. Crear el fichero `openhab_conf/items/ies_sequeros.items` con la definición del centro educativo (grupos + bombillas). Contenido completo:

```
// ==============================================================
// IES SEQUEROS - MODELO COMPLETO CON ILUMINACIÓN
// ==============================================================

// RAÍZ
Group gIES           "Instituto de Educación Secundaria Sequeros"  ["Location"]

// EDIFICIOS
Group gEdificioPrincipal "Edificio Principal de Administración y Aulas" (gIES) ["Building"]
Group gExteriores        "Zonas Exteriores y Patios de Recreo"         (gIES) ["Outdoor"]

// ==========================================
// ADMINISTRACIÓN (EDIFICIO PRINCIPAL)
// ==========================================
Group gSecretaria      "Oficina de Secretaría"              (gEdificioPrincipal) ["Office"]
Group gDireccion       "Despacho de Dirección"              (gEdificioPrincipal) ["Office"]
Group gJefatura        "Despacho de Jefatura de Estudios"   (gEdificioPrincipal) ["Office"]
Group gConserjeria     "Puesto de Conserjería"              (gEdificioPrincipal) ["Entry"]
Group gSalaProfesores  "Sala de Reuniones de Profesores"    (gEdificioPrincipal) ["Office"]

// ==========================================
// PATIOS
// ==========================================
Group gPatioNorte  "Zona de Patio Norte"  (gExteriores)  ["Garden"]
Group gPatioSur    "Zona de Patio Sur"    (gExteriores)  ["Garden"]

// ==========================================
// BOMBILLAS (una por estancia) - Ejercicio 3
// ==========================================
Switch Luz_Secretaria      "Luz de Secretaría"              (gSecretaria)     ["Lightbulb", "Switch", "Bombilla", "Interruptor"]
Switch Luz_Direccion       "Luz de Dirección"               (gDireccion)      ["Lightbulb", "Switch", "Bombilla", "Interruptor"]
Switch Luz_Jefatura        "Luz de Jefatura"                (gJefatura)       ["Lightbulb", "Switch", "Bombilla", "Interruptor"]
Switch Luz_Conserjeria     "Luz de Conserjería"             (gConserjeria)    ["Lightbulb", "Switch", "Bombilla", "Interruptor"]
Switch Luz_SalaProfesores  "Luz de Sala de Profesores"      (gSalaProfesores) ["Lightbulb", "Switch", "Bombilla", "Interruptor"]
Switch Luz_PatioNorte      "Luz del Patio Norte"            (gPatioNorte)     ["Lightbulb", "Switch", "Bombilla", "Interruptor"]
Switch Luz_PatioSur        "Luz del Patio Sur"              (gPatioSur)       ["Lightbulb", "Switch", "Bombilla", "Interruptor"]

// ==========================================
// CLIMATIZACIÓN SALA PROFESORES - Ejercicio 8
// ==========================================
Group gHVAC_SalaProfesores "Aire Acondicionado Central" (gSalaProfesores) ["HVAC", "Equipment", "Climatizacion", "Equipo"]

Switch            AC_Power       "Estado AC"                    (gHVAC_SalaProfesores) ["Switch", "Power", "Interruptor", "Encendido"]
Number:Temperature AC_CurrentTemp "Temperatura Actual [%.1f °C]" (gHVAC_SalaProfesores) ["Measurement", "Temperature", "Medicion", "Temperatura"]
Number:Temperature AC_Setpoint    "Temperatura Objetivo [%.1f °C]" (gHVAC_SalaProfesores) ["Setpoint", "Temperature", "Consigna", "Temperatura"]
```

4. Levantar OpenHAB:
```bash
docker compose up -d
```

5. Esperar ~2 minutos y acceder a `http://localhost:8080`. Completar el asistente inicial (crear usuario admin). Verificar que los items aparecen en **Configuración → Items**.

6. Generar un **token API** en OpenHAB: **Perfil de Usuario → Token API → Crear nuevo Token API**. Guardar el token para usarlo en los scripts.

**Verificación:** En la interfaz web deben aparecer los 7 switches de luces + los 3 items de climatización.

---

### FASE 2 — Chat Básico con Ollama (Ejercicio 4)

**Objetivo:** Script Python con chat interactivo contra un modelo local, con ventana de contexto.

**Pasos:**

1. Instalar Ollama y descargar el modelo:
```bash
ollama pull qwen3.5:2b
```

2. Instalar la librería Python:
```bash
pip install ollama requests
```

3. Crear `config.py` con las variables compartidas:

```python
# config.py
OPENHAB_URL = "http://localhost:8080"
API_TOKEN = "oh.TU_TOKEN_AQUI"  # Reemplazar con el token generado en OpenHAB
HEADERS_REST = {
    "Authorization": f"Bearer oh.TU_TOKEN_AQUI",
    "Content-Type": "text/plain"
}
HEADERS_JSON = {
    "Authorization": f"Bearer oh.TU_TOKEN_AQUI",
    "Accept": "application/json"
}
MODELO = "qwen3.5:2b"
```

4. Crear `scripts/01_chat_basico.py`:

```python
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

        response = ollama.chat(
            model=MODELO,
            messages=mensajes,
            options={"num_ctx": 4096}
        )

        respuesta = response["message"]["content"]
        print(f"\nIA: {respuesta}\n")

        mensajes.append({"role": "assistant", "content": respuesta})

if __name__ == "__main__":
    main()
```

**Verificación:** El chat mantiene coherencia entre turnos (recuerda lo dicho anteriormente).

---

### FASE 3 — System Prompt Dinámico desde OpenHAB (Ejercicios 5-6)

**Objetivo:** Obtener la estructura del sistema domótico vía API REST y construir el system prompt automáticamente.

**Pasos:**

1. Crear `scripts/02_system_prompt.py` que:
   - Haga `GET` a `http://localhost:8080/rest/items` con el token JWT.
   - Parsee el JSON de respuesta.
   - Construya un system prompt que describa las estancias, dispositivos y sus nombres técnicos.
   - Inicie un chat con ese system prompt.

2. Lógica clave para construir el prompt:

```python
import requests
import ollama
import json

OPENHAB_URL = "http://localhost:8080"
API_TOKEN = "oh.TU_TOKEN_AQUI"
MODELO = "qwen3.5:2b"

def obtener_items():
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}
    response = requests.get(f"{OPENHAB_URL}/rest/items", headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()
    return []

def construir_system_prompt(items):
    resumen = "Dispositivos del sistema domótico del IES Sequeros:\n"
    for item in items:
        nombre = item.get("name", "")
        etiqueta = item.get("label", "")
        tipo = item.get("type", "")
        estado = item.get("state", "")
        tags = item.get("tags", [])
        grupo = ", ".join([g for g in item.get("groupNames", [])])
        resumen += f"- {nombre} | Etiqueta: {etiqueta} | Tipo: {tipo} | Estado: {estado} | Grupos: {grupo} | Tags: {tags}\n"

    return (
        "Eres el gestor inteligente del sistema domótico del IES Sequeros. "
        "Conoces todos los dispositivos del centro y puedes responder preguntas sobre ellos. "
        "Responde siempre en español, de forma concisa.\n\n"
        f"{resumen}"
    )

def main():
    items = obtener_items()
    system_prompt = construir_system_prompt(items)

    mensajes = [{"role": "system", "content": system_prompt}]

    print("Chat con contexto domótico (escribe 'salir' para terminar)\n")

    while True:
        entrada = input("Tú: ")
        if entrada.lower() == "salir":
            break

        mensajes.append({"role": "user", "content": entrada})

        response = ollama.chat(
            model=MODELO,
            messages=mensajes,
            options={"num_ctx": 4096}
        )

        respuesta = response["message"]["content"]
        print(f"\nIA: {respuesta}\n")
        mensajes.append({"role": "assistant", "content": respuesta})

if __name__ == "__main__":
    main()
```

**Verificación:** Preguntar "¿cuántas bombillas hay?" o "¿qué estancias existen?" y obtener respuestas coherentes.

---

### FASE 4 — Tool de Control de Luces (Ejercicio 7)

**Objetivo:** Definir una herramienta (function calling) para encender/apagar luces vía la API REST de OpenHAB.

**Pasos:**

1. Crear `scripts/03_tool_luces.py` que incluya:
   - La función `ejecutar_actuador(device, value)` que hace POST a `/rest/items/{device}`.
   - La definición JSON Schema de la herramienta `actuar_openhab`.
   - La función `listar_items()` como segunda herramienta.
   - El bucle de chat que detecta `tool_calls` y ejecuta las funciones correspondientes.

2. Definición de las herramientas:

```python
herramientas = [
    {
        'type': 'function',
        'function': {
            'name': 'actuar_openhab',
            'description': 'Controla dispositivos del IES (luces ON/OFF, clima con números). Usa nombres técnicos de Item.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'device': {'type': 'string', 'description': 'Nombre técnico del item, ej: Luz_Direccion'},
                    'value': {'type': 'string', 'description': 'Valor a enviar: ON, OFF, o un número'},
                },
                'required': ['device', 'value'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'listar_items_openhab',
            'description': 'Obtiene la lista completa de dispositivos, nombres técnicos y estados actuales.',
            'parameters': {'type': 'object', 'properties': {}},
        },
    }
]
```

3. System prompt clave (debe indicar explícitamente la traducción encender=ON, apagar=OFF):

```python
system_prompt = (
    "Eres el gestor inteligente del sistema domótico del IES Sequeros. "
    "Controlas dispositivos mediante openHAB. "
    "REGLAS IMPORTANTES:\n"
    "- Para luces SIEMPRE usa ON (encender) y OFF (apagar) en MAYÚSCULAS.\n"
    "- Para temperaturas usa valores numéricos.\n"
    "- Usa los nombres técnicos exactos de los items.\n"
    "Items de luces disponibles: Luz_Secretaria, Luz_Direccion, Luz_Jefatura, "
    "Luz_Conserjeria, Luz_SalaProfesores, Luz_PatioNorte, Luz_PatioSur.\n"
    "Items de clima: AC_Power (ON/OFF), AC_CurrentTemp (lectura), AC_Setpoint (número)."
)
```

4. Flujo de procesamiento de tools:

```python
response = ollama.chat(model=MODELO, messages=mensajes, tools=herramientas)

if response.message.tool_calls:
    mensajes.append(response.message.model_dump())
    for tool in response.message.tool_calls:
        if tool.function.name == 'actuar_openhab':
            resultado = ejecutar_actuador(
                tool.function.arguments['device'],
                tool.function.arguments['value']
            )
        elif tool.function.name == 'listar_items_openhab':
            resultado = listar_items()

        mensajes.append({'role': 'tool', 'content': resultado, 'name': tool.function.name})

    # Segunda llamada para respuesta final al usuario
    final = ollama.chat(model=MODELO, messages=mensajes)
    print(f"IA: {final.message.content}")
    mensajes.append({'role': 'assistant', 'content': final.message.content})
else:
    print(f"IA: {response.message.content}")
```

**Verificación:** Decir "enciende la luz de dirección" y verificar en la interfaz de OpenHAB que `Luz_Direccion` pasa a ON.

---

### FASE 5 — Aire Acondicionado (Ejercicios 8-9)

**Objetivo:** Añadir climatización a la Sala de Profesores y crear una página de simulación.

**Pasos:**

1. Los items de climatización ya están incluidos en el fichero `.items` de la Fase 1 (AC_Power, AC_CurrentTemp, AC_Setpoint). Si no aparecen, reiniciar OpenHAB.

2. Crear una página de simulación en OpenHAB:
   - Ir a **Administración → Configuración → Pages**.
   - Crear nueva página tipo "Layout Page".
   - Añadir una fila con 3-4 columnas.
   - Columna 1: **Slider Card** vinculado a `AC_Setpoint` (temperatura objetivo, rango 15-30).
   - Columna 2: **Label Card** mostrando `AC_Setpoint` con formato `%.1f °C`.
   - Columna 3: **Slider Card** o **Stepper Card** vinculado a `AC_CurrentTemp` (simulador de sensor, rango -10 a 45).
   - Columna 4: **Label Card** o **Toggle Card** mostrando `AC_Power`.

3. Activar "Run mode" y probar que al mover el slider de temperatura actual, el valor se actualiza en Items.

**Verificación:** Los 3 items de climatización aparecen con valores modificables desde la página.

---

### FASE 6 — Listener SSE (Ejercicios 10-11)

**Objetivo:** Escuchar eventos de OpenHAB en tiempo real y combinar con el chat del usuario.

**Pasos:**

1. Crear `scripts/04_listener_sse.py` (listener independiente para probar):

```python
import requests
import json

OPENHAB_URL = "http://localhost:8080"
API_TOKEN = "oh.TU_TOKEN_AQUI"

def listener():
    url = f"{OPENHAB_URL}/rest/events"
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Accept': 'text/event-stream'
    }

    print(f"Conectando a {url}...")

    with requests.get(url, headers=headers, stream=True, timeout=None) as r:
        for line in r.iter_lines():
            if not line:
                continue
            decoded = line.decode('utf-8')
            if decoded.startswith("data:"):
                try:
                    data = json.loads(decoded[5:])
                    if data.get("type") == "ItemStateChangedEvent":
                        item = data["topic"].split("/")[2]
                        payload = json.loads(data["payload"])
                        valor = payload.get("value")
                        antiguo = payload.get("oldValue")
                        print(f"[SSE] {item}: {antiguo} → {valor}")
                except json.JSONDecodeError:
                    continue

if __name__ == "__main__":
    listener()
```

2. Crear `scripts/05_chat_completo.py` que combine:
   - El chat con tools de la Fase 4.
   - Un hilo (`threading.Thread`) ejecutando el listener SSE.
   - Una función centralizada `chat_con_ia(texto, es_evento=False)` que reciba tanto entrada del usuario como eventos del sistema.

**Verificación:** Al modificar un valor en la página de OpenHAB, aparece el evento en la consola del script sin bloquear la entrada del usuario.

---

### FASE 7 — Lógica Reactiva de Climatización (Ejercicio 12)

**Objetivo:** Cuando la temperatura supere 30°C o baje de 15°C, el sistema debe encender el AC automáticamente.

**Pasos:**

1. Crear `scripts/06_reactivo_clima.py` — versión final con toda la lógica integrada.

2. En el listener SSE, filtrar solo eventos de `AC_CurrentTemp`:

```python
eventos_criticos = ["AC_CurrentTemp"]
if item in eventos_criticos:
    valor_limpio = str(valor).split(" ")[0]
    temperatura = float(valor_limpio)

    if temperatura > 30 or temperatura < 15:
        mensaje = (
            f"ALERTA: La temperatura actual es {temperatura}°C. "
            "Si el aire acondicionado (AC_Power) está apagado, enciéndelo con ON "
            "y programa la temperatura objetivo (AC_Setpoint) a 22. "
            "Si ya está encendido, no hagas nada."
        )
        chat_con_ia(mensaje, es_evento=True)
    elif 15 <= temperatura <= 30:
        mensaje = (
            f"La temperatura actual es {temperatura}°C (rango normal). "
            "Si el aire acondicionado (AC_Power) está encendido, apágalo con OFF."
        )
        chat_con_ia(mensaje, es_evento=True)
```

3. El system prompt debe incluir reglas claras sobre climatización:

```python
system_prompt = (
    "Eres el gestor inteligente del IES Sequeros. "
    "REGLAS DE CLIMATIZACIÓN:\n"
    "- Si la temperatura (AC_CurrentTemp) supera 30°C → encender AC_Power con ON y poner AC_Setpoint a 22.\n"
    "- Si la temperatura baja de 15°C → encender AC_Power con ON y poner AC_Setpoint a 22.\n"
    "- Si la temperatura está entre 15°C y 30°C → apagar AC_Power con OFF.\n"
    "- SIEMPRE usa ON/OFF en MAYÚSCULAS para AC_Power.\n"
    "- SIEMPRE usa valores numéricos para AC_Setpoint.\n"
    "Items disponibles: Luz_Secretaria, Luz_Direccion, Luz_Jefatura, "
    "Luz_Conserjeria, Luz_SalaProfesores, Luz_PatioNorte, Luz_PatioSur, "
    "AC_Power, AC_CurrentTemp, AC_Setpoint."
)
```

**Verificación:**
- En la página de OpenHAB, mover el slider de `AC_CurrentTemp` a 35°C.
- En la consola del script debe aparecer el evento SSE, la IA debe decidir encender el AC.
- En la interfaz de OpenHAB, `AC_Power` debe pasar a ON y `AC_Setpoint` a 22.
- Mover el slider a 25°C → la IA debe apagar el AC.

---

## Notas Técnicas Importantes

**Sobre el modelo:** `qwen3.5:2b` es el mínimo recomendado para function calling. Modelos más pequeños como `qwen2.5:1.5b` no distinguen correctamente ON/OFF. Si el equipo lo permite, usar `qwen3.5:4b` o superior para mejor fiabilidad.

**Sobre el token:** El token JWT de OpenHAB se genera una vez y se reutiliza en todos los scripts. Si caduca, generar uno nuevo desde el perfil de usuario.

**Sobre los eventos SSE:** La conexión SSE es unidireccional y persistente. Si se pierde, el script debe reconectarse automáticamente (bucle `while True` con `time.sleep(5)` en el `except`).

**Sobre la ventana de contexto:** Con `num_ctx: 4096` se tienen ~4000 tokens de memoria. En conversaciones largas los mensajes antiguos se "olvidan". Para producción se implementaría un sistema de resumen o poda del historial.

---

## Comandos Rápidos de Referencia

```bash
# Levantar OpenHAB
docker compose up -d

# Ver logs de OpenHAB
docker compose logs -f openhab

# Instalar modelo en Ollama
ollama pull qwen3.5:2b

# Verificar modelo
ollama list

# Probar modelo manualmente
ollama run qwen3.5:2b

# Consultar items por API
curl -s http://localhost:8080/rest/items \
  -H "Authorization: Bearer oh.TU_TOKEN" | python3 -m json.tool

# Encender una luz por API
curl -X POST http://localhost:8080/rest/items/Luz_Direccion \
  -H "Authorization: Bearer oh.TU_TOKEN" \
  -H "Content-Type: text/plain" \
  -d "ON"
```

---

## Criterios de Evaluación (RA3)

| Criterio | Ejercicios |
|----------|-----------|
| a) Caracterización del NLP | Fases 2-3: chat con contexto y system prompt |
| c) Potencial y limitaciones | Fase 7: limitaciones de modelos pequeños con tools |
| d) Factibilidad de técnicas | Fases 4-5: function calling para control domótico |
| g) Sistema orientado a tarea | Fases 6-7: sistema reactivo completo |
