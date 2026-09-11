from google import genai
from google.genai import types

def initialiser_client_ia():
    try:
        cle_pour_ia = "AQ.Ab8RN6JTo1ZL0GixUW9G1pUnBlZFoQAbqn1EkNOrSt2c20GWYQ"
        return genai.Client(api_key=cle_pour_ia)
    except Exception as e:
        return None

def generer_reponse_ia(question, matiere="maths"):
    client = initialiser_client_ia()
    if not client:
        return "❌ Désolé, le service IA est temporairement indisponible."
    
    instructions = (
        "Tu es un tuteur scolaire IA hautement qualifié, pédagogue et bienveillant. "
        "Ton but est d'aider l'élève à comprendre ses leçons et exercices. "
        "1. Salue brièvement l'élève de manière encourageante.\n"
        "2. Explique clairement les concepts nécessaires.\n"
        "3. Propose une résolution détaillée, étape par étape.\n"
        "4. Utilise un langage clair et accessible.\n"
        "5. Termine par un petit conseil ou un mot d'encouragement."
    )
    
    try:
        reponse = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=instructions,
                temperature=0.3
            )
        )
        return reponse.text
    except Exception as e:
        return f"❌ Erreur IA : {str(e)}"