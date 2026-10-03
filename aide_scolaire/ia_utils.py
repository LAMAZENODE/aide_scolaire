from google import genai
from google.genai import types
import streamlit as st
import time


# ============================================
# LISTE DES MODÈLES À ESSAYER (fallback)
# ============================================
# Si le premier modèle est saturé, on essaie le suivant.
MODELES = [
    "gemini-3.6-flash",   # votre modèle principal
    "gemini-3.5-flash",   # fallback 1
    "gemini-2.0-flash",   # fallback 2 (plus ancien mais stable)
]


def initialiser_client_ia():
    """Crée le client Google GenAI avec la clé API."""
    try:
        cle = st.secrets["GEMINI_API_KEY"]
        return genai.Client(api_key=cle)
    except KeyError:
        st.error("❌ Clé API Gemini manquante dans secrets.toml")
        return None
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation : {e}")
        return None


def _construire_instructions(matiere: str) -> str:
    """Le 'system prompt' : les règles que l'IA doit suivre."""
    return (
        f"Tu es un tuteur scolaire IA pédagogue, spécialisé en {matiere}. "
        "Structure ta réponse :\n"
        "1. Introduction encourageante\n"
        "2. Concepts clés\n"
        "3. Résolution étape par étape\n"
        "4. Exemple concret\n"
        "5. Conclusion\n\n"
        "Adapte ton langage au niveau collège/lycée."
    )


def generer_reponse_ia(question: str, matiere: str = "maths") -> str:
    """
    Génère une réponse avec :
    - 3 tentatives par modèle (retry)
    - Délai croissant entre les tentatives (1s, 2s, 4s)
    - Fallback sur d'autres modèles si le premier échoue
    
    ⚠️ LÈVE UNE EXCEPTION en cas d'échec total.
    → Comme ça, app.py sait que ça a échoué et ne décompte PAS la question.
    """
    client = initialiser_client_ia()
    if not client:
        raise RuntimeError("Client IA indisponible")

    instructions = _construire_instructions(matiere)
    derniere_erreur = None

    # ---- BOUCLE 1 : on essaie chaque modèle ----
    for modele in MODELES:

        # ---- BOUCLE 2 : on réessaie 3 fois le même modèle ----
        for tentative in range(3):
            try:
                # Appel à l'API Gemini
                reponse = client.models.generate_content(
                    model=modele,
                    contents=question,
                    config=types.GenerateContentConfig(
                        system_instruction=instructions,
                        temperature=0.3,
                        max_output_tokens=2048,
                    ),
                )

                # Succès : on retourne la réponse
                if reponse and reponse.text:
                    return reponse.text

                # Réponse vide : on retente
                derniere_erreur = "Réponse vide"
                time.sleep(1)
                continue

            except Exception as e:
                msg = str(e)
                derniere_erreur = msg

                # --- CAS 1 : surcharge (503) → on attend et on retente ---
                if "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower():
                    time.sleep(2 ** tentative)  # 1s, 2s, 4s
                    continue

                # --- CAS 2 : quota dépassé → inutile de retenter, on abandonne ---
                if "quota" in msg.lower() or "429" in msg:
                    raise RuntimeError("Quota API dépassé. Réessayez plus tard.")

                # --- CAS 3 : clé invalide → inutile de retenter ---
                if "API_KEY" in msg or "permission" in msg.lower():
                    raise RuntimeError("Clé API Gemini invalide.")

                # --- CAS 4 : autre erreur → on passe au modèle suivant ---
                break

    # Si on arrive ici : tous les modèles ont échoué
    raise RuntimeError(f"L'IA est momentanément indisponible. ({derniere_erreur})")
