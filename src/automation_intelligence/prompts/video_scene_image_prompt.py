VIDEO_SCENE_IMAGE_PROMPT = """
Actúa como generador de imágenes narrativas para videos de historias emocionales en YouTube.

Tu tarea es crear una imagen cinematográfica y realista que represente UNA ESCENA CLAVE de la historia, pensada para mostrarse mientras se narra el relato.

PARÁMETROS OBLIGATORIOS:
- TÍTULO_DEL_VIDEO: {video_title}
- COMPONENTE_CLAVE: {story_topic}
- image horizontal.

REGLAS FUNDAMENTALES:

1. La imagen DEBE estar directamente relacionada con:
   - el TÍTULO_DEL_VIDEO (conflicto emocional principal)
   - el COMPONENTE_CLAVE (objeto, lugar o elemento central de la historia)

2. La imagen debe representar:
   - un momento de tensión
   - una revelación silenciosa
   - una humillación contenida
   - una conversación incómoda
   - o un instante previo a un giro importante

3. PERSONAJES:
   - Mujer mayor (40–50 años), protagonista
   - Rasgos de belleza hegemónica (armonía facial, piel cuidada, proporciones equilibradas), sin parecer modelo ni artificial
   - Apariencia realista, madura y creíble
   - Expresión emocional clara (shock, tristeza, incredulidad, miedo contenido)
   - Puede aparecer otro personaje secundario (familiar, empleado, camarero, funcionario), pero la mujer es el foco visual

4. ESTILO VISUAL:
   - Fotografía hiperrealista
   - Estilo cinematográfico
   - Iluminación suave pero dramática
   - Colores sobrios y realistas
   - Profundidad de campo baja
   - Enfoque en rostros y gestos

5. COMPOSICIÓN:
- ORIENTACIÓN: HORIZONTAL
- ASPECT RATIO: 16:9
   - Escena natural, no posada
   - Gestos pequeños (miradas, manos tensas, susurros)
   - El COMPONENTE_CLAVE puede aparecer:
     - explícitamente (objeto visible)
     - o implícitamente (sugerido visualmente)

6. PROHIBIDO:
   - Texto sobre la imagen
   - Estilo ilustración o caricatura
   - Exageraciones irreales
   - Violencia explícita
   - Escenas felices o celebratorias

DESCRIBE SOLO LA ESCENA VISUAL.
NO escribas historia.
NO escribas diálogo.
NO agregues texto ni títulos.
"""