import streamlit as st
from google import genai
from google.genai import types

# Récupérer la clé depuis les secrets de Streamlit
try:
    api_key = st.secrets["GCP_API_KEY"]
    client = genai.Client(api_key=api_key)
except KeyError:
    client = None
except Exception:
    client = None

def generer_reponse_ia(question, matiere="maths"):
    # Sécurité si la clé n'est pas trouvée
    if not client:
        return "❌ Configuration incomplète : La clé `GCP_API_KEY` est manquante dans votre fichier `.streamlit/secrets.toml`."

    prompt_system = (
        f"Tu es un tuteur scolaire en {matiere} hautement qualifié, pédagogue et bienveillant. "
        "Tu aides les élèves à comprendre leurs leçons et exercices. "
        "Ne donne pas directement la réponse finale brute, mais explique le raisonnement étape par étape."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Modèle flash standard recommandé
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=prompt_system,
                temperature=0.7,
                max_output_tokens=2000
            ),
        )
        return response.text
    except Exception as e:
        return f"❌ Erreur IA Gemini : {str(e)}"









