TEMPLATES = {
    "summarize": "Tu es un assistant de synthèse. Résume le texte en français de façon concise.\n\nTexte:\n{TEXT}",
    "extract": "Tu es un assistant d'extraction. Retourne seulement les entités et chiffres utiles en JSON.\n\nTexte:\n{TEXT}",
    "qa": "Tu es un assistant de question/réponse. Réponds en français à partir du texte suivant.\n\nTexte:\n{TEXT}",
    "classify": "Tu es un assistant de classification. Retourne la catégorie la plus probable.\n\nTexte:\n{TEXT}",
}


def build_prompt(task: str, text: str) -> str:
    template = TEMPLATES.get(task, TEMPLATES["summarize"])
    return template.replace("{TEXT}", text)
