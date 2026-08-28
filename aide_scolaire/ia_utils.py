from google import genai
from google.genai import types
import streamlit as st

def initialiser_client_ia():
    """Initialise le client Google GenAI avec la clé API depuis les secrets"""
    try:
        # Récupérer la clé depuis les secrets Streamlit
        cle_pour_ia = st.secrets["GEMINI_API_KEY"]
        return genai.Client(api_key=cle_pour_ia)
    except KeyError:
        st.error("❌ Clé API Gemini manquante dans secrets.toml")
        return None
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation du client IA : {str(e)}")
        return None

def generer_reponse_ia(question, matiere="maths"):
    """
    Génère une réponse pédagogique pour un élève
    
    Args:
        question (str): La question posée par l'élève
        matiere (str): La matière (maths, francais, anglais, etc.)
    
    Returns:
        str: La réponse générée par l'IA
    """
    client = initialiser_client_ia()
    if not client:
        return "❌ Désolé, le service IA est temporairement indisponible. Veuillez réessayer plus tard."
    
    # Instructions système détaillées
    instructions = (
        "Tu es un tuteur scolaire IA hautement qualifié, pédagogue et bienveillant. "
        "Ton but est d'aider l'élève à comprendre ses leçons et exercices.\n\n"
        "Structure ta réponse comme suit :\n"
        "1. **Introduction** : Salue brièvement l'élève de manière encourageante.\n"
        "2. **Concepts clés** : Explique clairement les notions nécessaires à la compréhension.\n"
        "3. **Résolution** : Propose une résolution détaillée, étape par étape.\n"
        "4. **Exemples** : Donne un exemple concret si pertinent.\n"
        "5. **Conclusion** : Termine par un conseil pratique ou un mot d'encouragement.\n\n"
        "Adapte ton langage au niveau collège/lycée. Sois clair, structuré et accessible."
    )
    
    try:
        # Appel à l'API Gemini avec google-genai
        reponse = client.models.generate_content(
            model='gemini-2.0-flash-exp',  # ou 'gemini-1.5-flash' selon disponibilité
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=instructions,
                temperature=0.3,  # Réponses plus précises et cohérentes
                max_output_tokens=2048,  # Limite la longueur
                top_p=0.95,
                top_k=40
            )
        )
        
        # Vérifier que la réponse contient du texte
        if reponse and reponse.text:
            return reponse.text
        else:
            return "❌ L'IA n'a pas pu générer de réponse. Veuillez reformuler votre question."
            
    except Exception as e:
        # Gestion des erreurs spécifiques
        error_msg = str(e)
        if "API_KEY" in error_msg or "permission" in error_msg.lower():
            return "❌ Erreur d'authentification : Vérifiez votre clé API Gemini."
        elif "quota" in error_msg.lower():
            return "❌ Quota API dépassé. Veuillez réessayer plus tard."
        else:
            return f"❌ Erreur IA : {error_msg}"

def generer_reponse_ia_avec_stream(question, matiere="maths"):
    """
    Version avec streaming pour afficher la réponse progressivement
    """
    client = initialiser_client_ia()
    if not client:
        yield "❌ Désolé, le service IA est temporairement indisponible."
        return
    
    instructions = (
        "Tu es un tuteur scolaire IA. Donne une réponse claire, structurée et pédagogique "
        "adaptée au niveau collège/lycée."
    )
    
    try:
        reponse = client.models.generate_content_stream(
            model='gemini-2.0-flash-exp',
            contents=question,
            config=types.GenerateContentConfig(
                system_instruction=instructions,
                temperature=0.3
            )
        )
        
        for chunk in reponse:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"❌ Erreur : {str(e)}"










