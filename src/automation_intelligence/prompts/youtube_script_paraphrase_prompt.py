YOUTUBE_SCRIPT_PARAPHRASE_PROMPT = """
Actúa como editor profesional de guiones para videos de YouTube.

Te entregaré un GUION ORIGINAL.  
Tu tarea es REESCRIBIRLO LIGERAMENTE cumpliendo estrictamente estas reglas:

OBJETIVO:
- Mantener exactamente el MISMO TEMA y la MISMA HISTORIA.
- Conservar una EXTENSIÓN MUY SIMILAR (cantidad de caracteres aproximada).
- Variar solo ligeramente la redacción: sinónimos, estructura de frases

GUION ORIGINAL:
{trancript_original}

"""