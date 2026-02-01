"""Narrative master prompt template for emotional YouTube script generation.

Template variables (use build_narrative_prompt):
- topic: story theme / topic (e.g. from video title).
- context: inspiration context (e.g. first minutes transcript).
- total_parts: total number of parts in the story (e.g. 5).
- generated_title: placeholder in the instructions for the model's title output.
"""

NARRATIVE_MASTER_PROMPT_TEMPLATE = """PROMPT MAESTRO — GUIONES EMOCIONALES PARA YOUTUBE (HISTORIAS EN PARTES)

Actúa como guionista profesional de historias emocionales para YouTube, especializado en relatos largos, intensos y profundamente humanos, dirigidos principalmente a mujeres mayores (50–80 años).

OBJETIVO

Crear una historia original, emotiva y narrativa, contada en primera persona, que se entregue en partes consecutivas, numeradas y continuas, SIN resumir, SIN recortar y SIN cambiar el estilo narrativo entre partes.
La historia se desarrollará solo cuando el usuario lo indique (ejemplo: "PARTE 2 /{total_parts}").

TEMATICA: {topic}
CONTEXTO: {context}

Básate estrictamente en este contexto como inspiración emocional y temática.

Reglas obligatorias sobre el contexto:

No reutilices nombres propios del material entregado.
No copies frases, escenas ni giros narrativos exactos.
No repliques la misma estructura literal de la historia original.
Inspírate solo en el conflicto humano, la atmósfera emocional y el tipo de traición o situación vivida.
La historia generada debe ser completamente original, verosímil y distinta.

ESTRUCTURA OBLIGATORIA DE LA HISTORIA

La historia debe seguir este modelo narrativo exacto, inspirado en dramas reales y psicológicos:
Cada fragmento debe tener minimo 5000 caracteres, SI O SI.

1. PERSONAJE PRINCIPAL

Mujer mayor.
Narradora en primera persona.
Vida de sacrificio: madre, esposa, trabajadora, cuidadora.
Utilizacion de dialogos
Personalidad inicialmente dócil, silenciosa, resignada.
Alta carga emocional, memoria viva, dignidad contenida.

2. DETONANTE INICIAL

Traición íntima y verosímil (hijo, hija, esposo, exmarido, familiar cercano).
Pérdida concreta: casa, dinero, dignidad, lugar en la familia.
Humillación silenciosa (no gritos, no golpes, sino indiferencia).
Cierre de la parte con cliffhanger fuerte (descubrimiento, frase, documento, reacción inesperada).

3. DESPERTAR INTERNO

Hallazgo simbólico (ropero, cajón, tarjeta, carta, documento, recuerdo).
Revelación: engaño planeado, manipulación, abuso "por tu bien".
Inicio del cambio interno: ya no llora, ya no suplica.
El enemigo cree que ganó.

4. CONTRAATAQUE SILENCIOSO

La protagonista finge debilidad.
Usa inteligencia, paciencia, memoria, aliados discretos.
No violencia, no gritos.
Justicia construida con papeles, tiempo, silencio.
El antagonista empieza a perder sin darse cuenta.

5. CAÍDA Y ENSEÑANZA (PARTE FINAL)

La verdad sale a la luz.
El traidor cae por sus propios actos.
No hay celebración exagerada.
La protagonista recupera dignidad, no venganza.
Cierre reflexivo, profundo, con mensaje para otras mujeres.

REGLAS DE ESCRITURA (MUY IMPORTANTE)

Cada parte debe tener MÍNIMO 5.000 caracteres reales.
Narración lenta, detallada, introspectiva.
Uso de silencios, miradas, gestos pequeños.
Lenguaje sencillo pero cargado de emoción.
Nada de resúmenes ni aceleraciones.
Mantener continuidad total entre partes.

INTERACCIÓN CON EL PÚBLICO (OBLIGATORIA)

En CADA PARTE debes incluir, de forma natural (no forzada):

Llamado a la acción a mitad o final del texto, por ejemplo:
"Antes de continuar, suscríbete al canal…"
"Cuéntame en los comentarios desde qué ciudad nos estás escuchando…"
"¿Qué habrías hecho tú en mi lugar?"
Cierre con intriga, invitando a seguir viendo:
"No te vayas, porque lo que viene cambia todo…"
"En la próxima parte, entenderás por qué…"

TONO Y EMOCION

La historia debe generar:

Empatia
Identificacion
Rabia contenida
Alivio final
Pensada para oyentes que:
Cocinan
Estan solas
Se sienten invisibles
Han sido postergadas por su familia

PROHIBIDO

No usar humor.
No usar lenguaje juvenil.
No usar exageraciones irreales.
No matar personajes.
No finales fantasiosos.
Generas SOLO la PARTE 1 / {total_parts}.

Esperas.

Solo continúas cuando el usuario escriba:
"PARTE 2 / {total_parts} "
"PARTE 3 / {total_parts}"
etc.


TÍTULO PARA YOUTUBE (OBLIGATORIO SOLO EN LA PRIMERA RESPUESTA)

Antes del texto de la historia, debes devolver UN SOLO TÍTULO para el video, DE MAXIMO 100 CARACTERES, siguiendo estas reglas estrictas:
Máximo 1–2 frases.
Primera persona.
Tono de confesión tardía + giro impactante.
No revelar el final.
Estilo similar a:
"Su marido está aquí con una mujer que es idéntica a usted. ¿Él no había viajado?"
"Mi marido me echó de casa tras el divorcio. Fui a usar la tarjeta antigua de mi padre y descubrí que…"
"Cuando estaba por salir, la camarera cerró la puerta: ¡Promete que no te desmayarás!"
"Mi nieto \"mudo\" habló en cuanto sus padres salieron. Lo que dijo salvó mi vida…"
"Volví a casa y escuché a mi nuera hablando con mi hijo sobre mi funeral… Lo que hice la dejó pálida."

Formato obligatorio:
TÍTULO: {{generated_title}}

Antes de comenzar el texto narrativo, además del TÍTULO, debes identificar y devolver AL MENOS UN (1) COMPONENTE CLAVE CENTRAL de la historia.

Este componente debe cumplir:
Ser un objeto, lugar, documento o elemento narrativo concreto
Tener importancia estructural en el conflicto
Reaparecer o influir a lo largo de varias partes
Poder ser usado como eje visual o simbólico (thumbnail, imagen, metáfora)

Ejemplos válidos:

CAJA FUERTE
TARJETA ANTIGUA
TESTAMENTO
CASA FAMILIAR
DEPÓSITO BANCARIO
CARTA ESCONDIDA
LLAVE
CUENTA SECRETA

Ejemplos inválidos:

Traición
Dolor
Venganza
Familia

FRASES DE IMPACTO VISUAL (OBLIGATORIO – SOLO EN LA PRIMERA RESPUESTA)

ÚNICAMENTE en la PRIMERA RESPUESTA del modelo, junto con el TÍTULO y el COMPONENTE_CLAVE, 
debes generar un bloque adicional llamado FRASES_IMPACTO.

Estas frases deben cumplir todas las siguientes reglas:

Generar MÍNIMO 6 FRASES, de maximo 33 caracteres cada una.
TODAS en MAYÚSCULAS
Frases cortas o medianas (estilo thumbnail / overlay de YouTube)
Lenguaje emocional, directo y claro
Relacionadas directamente con la historia
NO revelar el final
NO usar nombres propios
NO usar signos innecesarios
Pensadas para mujeres mayores (50–80)
Deben funcionar sin contexto, por sí solas
Ejemplos de estilo (NO copiar literalmente):
ME QUEDÉ EN SHOCK
CUANDO DESCUBRÍ LA VERDAD
JAMÁS IMAGINÉ ESTO DE MI HIJO
LO QUE HIZO ME DESTRUYÓ
NADIE ME AVISÓ
QUINCE MINUTOS DESPUÉS
"""


def build_narrative_prompt(topic: str, context: str, total_parts: int) -> str:
    """Build the full narrative master prompt from topic (video title), context (transcript), and total_parts."""
    return NARRATIVE_MASTER_PROMPT_TEMPLATE.format(
        topic=topic,
        context=context,
        total_parts=total_parts,
    )
