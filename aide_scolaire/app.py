import streamlit as st
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import stripe
import json
import os
from ia_utils import generer_reponse_ia

# ============================================
# CONFIG
# ============================================
st.set_page_config(
    page_title="Tuteur Scolaire ",
    page_icon="📚",
    layout="centered"
)

# ============================================
# CONFIGURATION STRIPE
# ============================================
stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", "")

# Détecter le retour après paiement Stripe
params = st.query_params
if params.get("paiement") == "succes":
    st.session_state.abonne = True
    st.session_state.email_deja_essaye = False
    st.session_state.email_verifie = None
    st.balloons()
    st.success("🎉 Merci ! Votre abonnement est actif.")
    st.query_params.clear()
elif params.get("paiement") == "annule":
    st.warning("⚠️ Paiement annulé. Vous pouvez réessayer.")
    st.query_params.clear()

# ============================================
# GESTION DES ESSAIS (FICHIER SERVEUR)
# ============================================
FICHIER_ESSAIS = "essais_utilises.json"

def charger_essais():
    """Lit le fichier des essais déjà utilisés."""
    if not os.path.exists(FICHIER_ESSAIS):
        return {}
    try:
        with open(FICHIER_ESSAIS, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def sauver_essais(data):
    """Écrit le fichier des essais."""
    with open(FICHIER_ESSAIS, "w") as f:
        json.dump(data, f, indent=2)

def email_a_deja_essaye(email: str) -> bool:
    """Vérifie si un email a déjà consommé son essai gratuit."""
    essais = charger_essais()
    return email.strip().lower() in essais

def enregistrer_essai(email: str):
    """Marque un email comme ayant utilisé son essai."""
    essais = charger_essais()
    essais[email.strip().lower()] = datetime.now().isoformat()
    sauver_essais(essais)

# ============================================
# COOKIES
# ============================================
cookie_manager = stx.CookieManager(key="cookies_essai")

DUREE_ESSAI_JOURS = 7
MAX_QUESTIONS_ESSAI = 1

# ============================================
# SESSION
# ============================================
if "compteur_rerun" not in st.session_state:
    st.session_state.compteur_rerun = 0
st.session_state.compteur_rerun += 1

for k, v in [
    ("essai_actif", False),
    ("date_debut_essai", None),
    ("questions_posees", 0),
    ("abonne", False),
    ("reponse_a_afficher", None),
    ("question_a_afficher", None),
    ("email_essai", None),
    ("cookies_charges", False),
    ("email_deja_essaye", False),
    ("email_verifie", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================
# HELPERS
# ============================================
def jours_restants():
    if not st.session_state.date_debut_essai:
        return 0
    fin = st.session_state.date_debut_essai + timedelta(days=DUREE_ESSAI_JOURS)
    return max(0, (fin - datetime.now()).days)

def questions_restantes():
    return max(0, MAX_QUESTIONS_ESSAI - st.session_state.questions_posees)

def acces_autorise():
    if st.session_state.abonne:
        return True
    if not st.session_state.essai_actif:
        return False
    if jours_restants() <= 0:
        return False
    if questions_restantes() <= 0:
        return False
    return True

def demarrer_essai(email: str):
    """Démarre l'essai pour un email donné (déjà vérifié en amont)."""
    m = datetime.now()
    st.session_state.essai_actif = True
    st.session_state.date_debut_essai = m
    st.session_state.questions_posees = 0
    st.session_state.email_essai = email.strip().lower()
    st.session_state.reponse_a_afficher = None
    st.session_state.question_a_afficher = None
    cookie_manager.set(
        "essai_debut",
        m.isoformat(),
        expires_at=m + timedelta(days=DUREE_ESSAI_JOURS),
        key="set_essai_cookie"
    )

def creer_lien_paiement(price_id: str, mode: str = "subscription"):
    """
    Crée une session Stripe Checkout.
    mode : "subscription" (abonnement) ou "payment" (paiement unique)
    """
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode=mode,
            success_url="http://localhost:8501/?paiement=succes",
            cancel_url="http://localhost:8501/?paiement=annule",
        )
        return session.url
    except Exception as e:
        st.error(f"❌ Erreur Stripe : {e}")
        return None

# ============================================
# RESTAURATION COOKIE (avec attente du chargement)
# ============================================
cookies = cookie_manager.get_all()

if not st.session_state.cookies_charges:
    if cookies is not None:
        st.session_state.cookies_charges = True

if st.session_state.cookies_charges and not st.session_state.essai_actif and not st.session_state.abonne:
    c = cookies.get("essai_debut")
    if c:
        try:
            d = datetime.fromisoformat(c)
            if datetime.now() - d < timedelta(days=DUREE_ESSAI_JOURS):
                st.session_state.essai_actif = True
                st.session_state.date_debut_essai = d
        except Exception:
            pass

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.header("📊 Statut")
    if st.session_state.abonne:
        st.success("✅ Premium — illimité")
    elif st.session_state.essai_actif:
        st.info(f"🎁 Essai — {questions_restantes()} question(s)")
    else:
        st.error("🔒 Aucun accès")

# ============================================
# DEBUG (à retirer plus tard)
# ============================================
st.write(f"### 🔄 Reruns : {st.session_state.compteur_rerun}")
st.caption(f"debug → essai={st.session_state.essai_actif} · "
           f"questions={st.session_state.questions_posees} · "
           f"acces={acces_autorise()} · abonne={st.session_state.abonne} · "
           f"email_deja_essaye={st.session_state.email_deja_essaye}")

# ============================================
# PAGE
# ============================================
st.title("📚 Tuteur Scolaire ")
st.markdown("---")

# ---------- CAS 1 : pas d'essai ----------
if not st.session_state.essai_actif and not st.session_state.abonne:

    # Sous-cas A : l'email a déjà été vérifié et a déjà consommé son essai
    if st.session_state.email_deja_essaye:
        st.error("🔒 Cet email a déjà utilisé l'essai gratuit. Passez au paiement ci-dessous.")

        st.markdown("### 🚀 Choisissez votre formule")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### ⏰ Jour")
            st.markdown("### **2,99 €** / jour")
            st.markdown("""
            - ✅ 1 jour d'accès
            - ✅ Toutes les matières
            - ✅ Idéal pour réviser
            """)
            if st.button("💳 Acheter — Jour", key="abo_jour_A",
                         use_container_width=True):
                url = creer_lien_paiement(st.secrets["STRIPE_PRICE_JOUR"],
                                          mode="payment")
                if url:
                    st.markdown(f"[👉 **Cliquez ici pour payer**]({url})")

        with col2:
            st.markdown("#### 📅 Mois")
            st.markdown("### **9,99 €** / mois")
            st.markdown("""
            - ✅ 30 jours d'accès
            - ✅ Questions illimitées
            - ✅ Annulable
            """)
            if st.button("💳 Acheter — Mois", key="abo_mois_A",
                         type="primary", use_container_width=True):
                url = creer_lien_paiement(st.secrets["STRIPE_PRICE_MOIS"])
                if url:
                    st.markdown(f"[👉 **Cliquez ici pour payer**]({url})")

        with col3:
            st.markdown("#### 🎓 BAC ⭐")
            st.markdown("### **49,99 €** / an")
            st.markdown("""
            - ✅ **Toute l'année**
            - ✅ **Spécial BAC**
            - ✅ Meilleure offre
            """)
            if st.button("💳 Acheter — BAC", key="abo_bac_A",
                         use_container_width=True):
                url = creer_lien_paiement(st.secrets["STRIPE_PRICE_BAC"])
                if url:
                    st.markdown(f"[👉 **Cliquez ici pour payer**]({url})")

        st.caption("💳 Paiement sécurisé par Stripe · Annulable à tout moment")

    # Sous-cas B : formulaire d'essai normal
    else:
        st.markdown("### 🎓 Bienvenue sur votre tuteur !")
        st.markdown("""
        Posez **n'importe quelle question** dans **toutes les matières** :
        - 📐 Maths · 📖 Français · 🏛️ Histoire · ⚗️ Physique · 🧬 SVT · 🌍 Anglais…

        **Essai gratuit :**
        - ✅ **7 jours** d'accès
        - ✅ **1 question gratuite**
        """)

        with st.form("form_essai"):
            email = st.text_input("📧 Votre email (pour activer l'essai) :",
                                  placeholder="exemple@email.com")
            submit = st.form_submit_button("🎁 Démarrer l'essai gratuit",
                                           type="primary",
                                           use_container_width=True)

        if submit:
            if not email or "@" not in email or "." not in email:
                st.warning("⚠️ Entrez un email valide.")
            elif email_a_deja_essaye(email):
                # Mémoriser pour que le clic suivant sur un bouton de paiement
                # ne réaffiche PAS le formulaire d'essai
                st.session_state.email_deja_essaye = True
                st.session_state.email_verifie = email.strip().lower()
                st.rerun()
            else:
                enregistrer_essai(email)
                demarrer_essai(email)
                st.rerun()

# ---------- CAS 2 : essai épuisé ----------
elif not acces_autorise() and not st.session_state.abonne:
    st.error("## 🔒 Votre essai gratuit est terminé")

    if st.session_state.reponse_a_afficher:
        with st.expander("📖 Revoir ma dernière réponse", expanded=False):
            st.caption(f"Question : {st.session_state.question_a_afficher}")
            st.markdown(st.session_state.reponse_a_afficher)

    st.markdown("### 🚀 Choisissez votre formule")

    col1, col2, col3 = st.columns(3)

    # --- FORMULE JOUR ---
    with col1:
        st.markdown("#### ⏰ Jour")
        st.markdown("### **2,99 €** / jour")
        st.markdown("""
        - ✅ 1 jour d'accès
        - ✅ Toutes les matières
        - ✅ Idéal pour réviser
        """)
        if st.button("💳 Acheter — Jour", key="abo_jour", use_container_width=True):
            url = creer_lien_paiement(st.secrets["STRIPE_PRICE_JOUR"], mode="payment")
            if url:
                st.markdown(f"[👉 **Cliquez ici pour payer**]({url})")

    # --- FORMULE MOIS ---
    with col2:
        st.markdown("#### 📅 Mois")
        st.markdown("### **9,99 €** / mois")
        st.markdown("""
        - ✅ 30 jours d'accès
        - ✅ Questions illimitées
        - ✅ Annulable
        """)
        if st.button("💳 Acheter — Mois", key="abo_mois", type="primary",
                     use_container_width=True):
            url = creer_lien_paiement(st.secrets["STRIPE_PRICE_MOIS"])
            if url:
                st.markdown(f"[👉 **Cliquez ici pour payer**]({url})")

    # --- FORMULE BAC ---
    with col3:
        st.markdown("#### 🎓 BAC ⭐")
        st.markdown("### **49,99 €** / an")
        st.markdown("""
        - ✅ **Toute l'année**
        - ✅ **Spécial BAC**
        - ✅ Meilleure offre
        """)
        if st.button("💳 Acheter — BAC", key="abo_bac", use_container_width=True):
            url = creer_lien_paiement(st.secrets["STRIPE_PRICE_BAC"])
            if url:
                st.markdown(f"[👉 **Cliquez ici pour payer**]({url})")

    st.caption("💳 Paiement sécurisé par Stripe · Annulable à tout moment")

# ---------- CAS 3 : accès OK ----------
else:
    if st.session_state.abonne:
        st.success("✅ Premium — illimité")
    else:
        st.success(f"🎁 Essai — {questions_restantes()} question restante")

    if st.session_state.reponse_a_afficher:
        st.markdown("### 📖 Réponse")
        st.caption(f"Question : {st.session_state.question_a_afficher}")
        st.markdown(st.session_state.reponse_a_afficher)
        st.markdown("---")

    st.markdown("### 💬 Posez votre question")
    with st.form("form_question"):
        question = st.text_area(
            "Votre question :",
            height=120,
            placeholder="Ex: Résous x+8=7 · Explique la photosynthèse · Traduis 'hello' …"
        )
        submit = st.form_submit_button("🚀 Envoyer", type="primary",
                                       use_container_width=True)

    if submit:
        if not question.strip():
            st.warning("⚠️ Écrivez une question avant d'envoyer.")
        elif not acces_autorise():
            st.error("🔒 Essai terminé.")
        else:
            with st.spinner("🤔 L'IA réfléchit à votre question..."):
                reponse = generer_reponse_ia(question)

            st.session_state.question_a_afficher = question
            st.session_state.reponse_a_afficher = reponse

            if not st.session_state.abonne:
                st.session_state.questions_posees += 1

            st.markdown("### 📖 Réponse du tuteur")
            st.markdown(reponse)
