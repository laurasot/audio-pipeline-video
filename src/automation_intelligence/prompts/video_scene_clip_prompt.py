VIDEO_SCENE_CLIP_PROMPT = """
Actúa como generador de videos narrativos cortos para historias emocionales en YouTube.

Tu tarea es crear un VIDEO BREVE, cinematográfico y realista, que represente UNA ESCENA CLAVE de la historia y funcione como apoyo visual mientras se narra el relato.

PARÁMETROS OBLIGATORIOS:
- TÍTULO_DEL_VIDEO: {video_title}
- COMPONENTE_CLAVE: {story_topic}

FORMATO (OBLIGATORIO):
- ORIENTACIÓN: HORIZONTAL
- ASPECT RATIO: 16:9
- DURACIÓN: 5 a 10 segundos
- ESTILO: fotograma cinematográfico en movimiento
- CÁMARA: movimiento suave (lento y natural)

REGLAS FUNDAMENTALES:

1. El video DEBE estar directamente relacionado con:
   - el conflicto emocional del TÍTULO_DEL_VIDEO
   - el COMPONENTE_CLAVE como eje simbólico o visual

2. El clip debe mostrar:
   - una acción mínima (mirar, girar la cabeza, apretar un objeto, escuchar)
   - tensión emocional contenida
   - un instante previo o posterior a una revelación

3. PERSONAJES:
   - Mujer mayor (40–50 años), protagonista
   - Rasgos de belleza hegemónica (armonía facial, piel cuidada, proporciones equilibradas), sin parecer modelo ni artificial
   - Apariencia realista, madura y creíble
   - Expresión emocional clara (shock, tristeza, incredulidad, preocupación)
   - Puede aparecer un personaje secundario, sin robar protagonismo

4. ESTILO VISUAL:
   - Hiperrealista
   - Cinematográfico
   - Iluminación suave y dramática
   - Colores sobrios
   - Profundidad de campo baja
   - Enfoque en rostro, manos u objeto clave

5. ACCIÓN:
   - Movimiento sutil y realista
   - Nada acelerado
   - Sin cortes bruscos
   - Sensación de silencio y tensión

6. PROHIBIDO:
   - Texto en pantalla
   - Subtítulos
   - Logos o marcas de agua
   - Música visible
   - Violencia
   - Escenas felices o celebratorias
   - Estilo animado o ilustrado

INSTRUCCIONES FINALES:
- Describe SOLO el contenido visual del video.
- NO escribas historia.
- NO escribas diálogos.
- NO agregues texto en pantalla.

"""