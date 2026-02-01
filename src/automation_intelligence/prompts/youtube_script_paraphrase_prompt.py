"""Prompt template to lightly paraphrase a YouTube script."""

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


def build_youtube_script_paraphrase_prompt(trancript_original: str) -> str:
    """Fill the paraphrase prompt with the original transcript/script text.

    Note: placeholder name is kept as 'trancript_original' to match template.
    """
    return YOUTUBE_SCRIPT_PARAPHRASE_PROMPT.format(trancript_original=trancript_original or "")