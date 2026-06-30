TEMPLATES = {
    "summarize": (
        "Tu es un assistant de synthese. Resume le texte en francais de facon concise.\n\n"
        "Texte:\n{TEXT}"
    ),
    "extract": (
        "Tu es un assistant d'extraction. Retourne seulement les entites et chiffres utiles en JSON.\n\n"
        "Texte:\n{TEXT}"
    ),
    "qa": (
        "Tu es un assistant de question/reponse. Reponds en francais a partir du texte suivant.\n\n"
        "Texte:\n{TEXT}"
    ),
    "classify": (
        "Tu es un assistant de classification. Classe le texte dans une seule categorie parmi: "
        "support, finance, technique, juridique, autre. Retourne seulement la categorie.\n\n"
        "Texte:\n{TEXT}"
    ),
}


def build_prompt(task: str, text: str) -> str:
    template = TEMPLATES.get(task, TEMPLATES["summarize"])
    return template.replace("{TEXT}", text)
