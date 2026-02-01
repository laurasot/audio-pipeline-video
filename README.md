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

### Pipeline Python: generar prompt narrativo en un `.txt`

Este script tiene 2 modos:

- **All-in-one**: canal -> elige video -> obtiene transcripción -> genera prompt -> guarda `.txt`
- **Paso 2**: topic + context -> genera prompt -> guarda `.txt`

```bash
# All-in-one (canal -> transcripción -> prompt)
python scripts/run_channel1_script_pipeline.py --channel @nombre_canal
python scripts/run_channel1_script_pipeline.py --channel "https://www.youtube.com/@nombre_canal" --show
python scripts/run_channel1_script_pipeline.py --channel @nombre_canal --recent-videos-limit 10
python scripts/run_channel1_script_pipeline.py --channel @nombre_canal --full-transcript
python scripts/run_channel1_script_pipeline.py --channel @nombre_canal --transcript-seconds 90

# Paso 2 (topic + context -> prompt)
python scripts/run_channel1_script_pipeline.py --topic "Titulo del video" --context "Texto de la transcripcion..."
python scripts/run_channel1_script_pipeline.py --topic "..." --context-file transcript.txt
```

**Perfil de Chrome (all-in-one):** con `--chrome-profile` usas tu Chrome (cookies, etc.). Sin nombre = perfil **Default**. Con nombre = ese perfil: `--chrome-profile "Profile 1"`, `"Profile 2"`, etc. Con `--chrome-dev` usas la ruta de **Chrome Dev**. Con `--user-data-dir` pasas la ruta completa de **User Data**. Debes **cerrar Chrome** (o al menos ese perfil) antes de ejecutar.

**Transcripción (all-in-one):** por defecto toma segundos desde `.env` (`TRANSCRIPT_MAX_SECONDS`). Usa `--transcript-seconds` para cambiarlo o `--full-transcript` para transcribir todo el video.

### Canal 2: prompt para parafrasear guion (solo `YOUTUBE_SCRIPT_PARAPHRASE_PROMPT`)

Este script hace: canal -> elige video -> transcribe -> genera un `.txt` con el prompt `YOUTUBE_SCRIPT_PARAPHRASE_PROMPT`.

```bash
python scripts/run_channel2_paraphrase_prompt.py @nombre_canal --recent-videos-limit 10 --transcript-seconds 60
python scripts/run_channel2_paraphrase_prompt.py @nombre_canal --full-transcript
```

### Descargar imágenes y videos cortos de una persona (DuckDuckGo)

Instala el extra:

```bash
pip install -e ".[images]"
```

Uso:

```bash
python scripts/download_person_media.py "Scarlett Johansson" --num 12 --orientation horizontal
python scripts/download_person_media.py "Scarlett Johansson" --num 12 --orientation vertical
python scripts/download_person_media.py "Scarlett Johansson" --num 12 --orientation any

# Imágenes + videos cortos (descarga N imágenes y N videos)
python scripts/download_person_media.py "Scarlett Johansson" --num 12 --orientation horizontal --videos

# Videos más largos (hasta 2 minutos)
python scripts/download_person_media.py "Scarlett Johansson" --num 6 --videos --max-video-duration 120
```

Los videos se descargan usando **yt-dlp** (soporta YouTube, TikTok, Instagram, etc.). Por defecto solo descarga videos de hasta **60 segundos** (1 minuto).

Salida por defecto:
- Imágenes: `output/images/<persona>/`
- Videos: `output/videos/<persona>/`

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

