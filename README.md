# Auto Video Pipeline

Pipeline con **Playwright** para automatizar la creación de videos: graba en video las sesiones del navegador mientras se ejecutan flujos definidos por pasos (navegar, hacer clic, escribir, esperar, etc.).

Incluye un flujo **Python + Playwright** que identifica la temática del nuevo video navegando al canal de YouTube que se pasa como parámetro.

## Requisitos

- **Python 3.12+** y pip (stack principal)

## Instalación

Stack **Python + Playwright** (recomendado):

```bash
pip install -e .
playwright install chromium
```

**Importante:** tras `pip install`, hay que ejecutar `playwright install chromium` (o `playwright install`) en el mismo entorno donde corres el script. Esa orden descarga Chromium; si no la ejecutas, verás *Executable doesn't exist* al lanzar el pipeline.

## Uso

### Pipeline Python: identificar temática desde un canal

Entra al canal indicado, toma los últimos 10 vídeos y elige uno al azar como tema. **Por defecto corre en segundo plano (headless)**; usa `--show` si quieres ver el navegador:

```bash
python scripts/run_channel_topic.py @nombre_canal
python scripts/run_channel_topic.py "https://www.youtube.com/@nombre_canal"
python scripts/run_channel_topic.py @nombre_canal --show   # con ventana
python scripts/run_channel_topic.py @nombre_canal --chrome-profile   # perfil Default
python scripts/run_channel_topic.py @nombre_canal --chrome-profile "Profile 1"   # perfil concreto (Chrome estable)
python scripts/run_channel_topic.py @nombre_canal --chrome-dev --chrome-profile "Profile 1"   # Chrome Dev, Profile 1
python scripts/run_channel_topic.py @nombre_canal --user-data-dir "C:\...\Chrome Dev\User Data" --chrome-profile "Profile 1"   # ruta completa (User Data + Profile)
```

**Perfil de Chrome:** con `--chrome-profile` usas tu Chrome (extensiones, cookies). Sin nombre = perfil **Default**. Con nombre = ese perfil: `--chrome-profile "Profile 1"`, `"Profile 2"`, etc. Con `--chrome-dev` usas la ruta de **Chrome Dev** (p. ej. `...\Chrome Dev\User Data`). Con `--user-data-dir` pasas la ruta de **User Data** (y sigues indicando el perfil con `--chrome-profile`). Debes **cerrar Chrome** (o al menos ese perfil) antes de ejecutar.

**Transcripcion:** la duracion maxima (segundos) se lee de `.env` (`TRANSCRIPT_MAX_SECONDS`, por defecto 60). Puedes copiar `.env.example` a `.env` y ajustarla. `--transcript-seconds` en CLI tiene prioridad sobre el .env.

Si no tienes el paquete instalado: `PYTHONPATH=src python scripts/run_channel_topic.py @nombre_canal`

### Paso 2: Generar el prompt narrativo en un `.txt` (sin abrir ChatGPT)

Despues de elegir video y obtener transcripcion (paso 1), genera el prompt de `narrative_master_prompt` (topic = titulo del video, context = transcripcion, total_parts desde `.env`) y lo guarda como `.txt` dentro de `./output`.

```bash
python scripts/run_script_pipeline.py --topic "Titulo del video" --context "Texto de la transcripcion..."
python scripts/run_script_pipeline.py --topic "..." --context-file transcript.txt
```

Opciones: `--topic` (titulo del video), `--context` (transcripcion en linea) o `--context-file` (transcripcion en archivo). Se construye el prompt con `total_parts` de `.env` (o `--total-parts N`) y se guarda en `./output`.

### Todo en uno: paso 1 + paso 2 (canal, transcripcion y prompt en `.txt`)

Un solo comando hace: canal -> elige video -> obtiene transcripcion -> genera el prompt narrativo -> lo guarda en `./output`.

```bash
python scripts/run_channel_topic_then_prompt.py @RecuerdosdeMaribel --user-data-dir "C:\...\ChromeAutomation" --chrome-profile "Default" --chrome-dev
```

Mismas opciones de perfil que en paso 1. Chrome debe estar cerrado.

### Listar extensiones de un perfil de Chrome

Lee del disco las extensiones instaladas en un perfil (Chrome puede estar abierto):

```bash
python scripts/list_chrome_extensions.py --chrome-dev --chrome-profile "Profile 1"
python scripts/list_chrome_extensions.py --chrome-profile "Profile 1"   # Chrome estable
python scripts/list_chrome_extensions.py -v   # Default + verbose (id, descripción)
```

---

## Estructura del proyecto

```
src/
  automation_intelligence/
    browser/          # Helpers Playwright (acciones, navegación, perfiles)
    config/           # Settings (.env, defaults, etc.)
    logging/          # Logger
    pipelines/        # Pipelines (channel_topic, script/chatgpt, etc.)
    prompts/          # Prompts (p. ej. narrative_master_prompt)
    transcript.py     # Utilidades de transcripción
```

