import streamlit as st
from datetime import datetime, timedelta
import extra_streamlit_components as stx
import stripe
import json
import os
import sqlite3
from ia_utils import generer_reponse_ia

# ============================================
# CONFIG
# ============================================
st.set_page_config(
    page_title="Tuteur Scolaire",
    page_icon="📚",
    layout="centered"
)

# ============================================
# CONFIGURATION STRIPE
# ============================================
stripe.api_key = st.secrets.get("STRIPE_SECRET_KEY", "")

# ============================================
# BASE DE DONNÉES (SQLite persistante)
# ============================================
DB_PATH = "tuteur.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS essais (
            email TEXT PRIMARY KEY,
            date_debut TEXT NOT NULL,
            questions_posees INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS abonnements (
            email TEXT PRIMARY KEY,
            stripe_session_id TEXT,
            formule TEXT,
            date_achat TEXT,
            date_expiration TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_essai(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT date_debut, questions_posees FROM essais WHERE email = ?",
              (email.strip().lower(),))
    row = c.fetchone()
    conn.close()
    return row

def creer_essai(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO essais (email, date_debut, questions_posees) VALUES (?, ?, 0)",
              (email.strip().lower(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def incrementer_questions(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE essais SET questions_posees = questions_posees + 1 WHERE email = ?",
              (email.strip().lower(),))
    conn.commit()
    conn.close()

def email_a_deja_essaye(email: str) -> bool:
    return get_essai(email) is not None

def get_abonnement(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT formule, date_expiration FROM abonnements WHERE email = ?",
              (email.strip().lower(),))
    row = c.fetchone()
    conn.close()
    return row

def enregistrer_abonnement(email: str, session_id: str, formule: str, duree_jours: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    expiration = (datetime.now() + timedelta(days=duree_jours)).isoformat()
    c.execute("""INSERT OR REPLACE INTO abonnements
                 (email, stripe_session_id, formule, date_achat, date_expiration)
                 VALUES (?, ?, ?, ?, ?)""",
              (email.strip().lower(), session_id, formule,
               datetime.now().isoformat(), expiration))
    conn.commit()
    conn.close()

# ============================================
# COOKIES
# ============================================
cookie_manager = stx.CookieManager(key="cookies_essai")

DUREE_ESSAI_JOURS = 7
MAX_QUESTIONS_ESSAI = 3  # ← passé de 1 à 3

# ============================================
# SESSION
# ============================================
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
# VÉRIFICATION RETOUR STRIPE (SÉCURISÉE)
# ============================================
params = st.query_params
if params.get("paiement") == "succes":
    session_id = params.get("session_id")
    if not session_id:
        st.error("❌ Session de paiement introuvable.")
    else:
        try:
            # On interroge Stripe pour vérifier RÉELLEMENT le paiement
            checkout = stripe.checkout.Session.retrieve(session_id)
            if checkout.payment_status == "paid":
                email_client = checkout.customer_details.email if checkout.customer_details else None
                if email_client:
                    # Déterminer la durée selon la formule
                    duree = 1
                    if checkout.amount_total >= 4999:
                        duree = 365
                    elif checkout.amount_total >= 999:
                        duree = 30
                    enregistrer_abonnement(email_client, session_id, "stripe", duree)
                    st.session_state.abonne = True
                    st.session_state.email_essai = email_client.strip().lower()
                    st.balloons()
                    st.success("🎉 Merci ! Votre abonnement est actif.")
                else:
                    st.error("❌ Email client introuvable dans la session Stripe.")
            else:
                st.warning("⚠️ Le paiement n'a pas été confirmé par Stripe.")
        except Exception as e:
            st.error(f"❌ Erreur de vérification Stripe : {e}")
    st.query_params.clear()
elif params.get("paiement") == "annule":
    st.warning("⚠️ Paiement annulé. Vous pouvez réessayer.")
    st.query_params.clear()

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
    cookie_manager.set("essai_email", email.strip().lower(),
                       expires_at=m + timedelta(days=DUREE_ESSAI_JOURS),
                       key="set_email_cookie")

def creer_lien_paiement(price_id: str, mode: str = "subscription"):
    try:
        session = stripe.checkout.Session.create(
            line_items=[{"price": price_id, "quantity": 1}],
            mode=mode,
            success_url="http://localhost:8501/?paiement=succes&session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8501/?paiement=annule",
        )
        return session.url
    except Exception as e:
        st.error(f"❌ Erreur Stripe : {e}")
        return None

# ============================================
# RESTAURATION COOKIE (avec email)
# ============================================
cookies = cookie_manager.get_all()
if not st.session_state.cookies_charges and cookies is not None:
    st.session_state.cookies_charges = True

if st.session_state.cookies_charges and not st.session_state.essai_actif and not st.session_state.abonne:
    c_debut = cookies.get("essai_debut")
    c_email = cookies.get("essai_email")
    if c_debut and c_email:
        try:
            d = datetime.fromisoformat(c_debut)
            if datetime.now() - d < timedelta(days=DUREE_ESSAI_JOURS):
                # Récupérer l'état réel depuis la BDD
                row = get_essai(c_email)
                if row:
                    st.session_state.essai_actif = True
                    st.session_state.date_debut_essai = d
                    st.session_state.email_essai = c_email
                    st.session_state.questions_posees = row[1]
        except Exception:
            pass

# Vérifier si un abonnement existe en BDD
if st.session_state.email_essai and not st.session_state.abonne:
    abo = get_abonnement(st.session_state.email_essai)
    if abo:
        expiration = datetime.fromisoformat(abo[1])
        if expiration > datetime.now():
            st.session_state.abonne = True

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
# PAGE
# ============================================
st.title("📚 Tuteur Scolaire")
st.markdown("---")

# ---------- CAS 1 : pas d'essai ----------
if not st.session_state.essai_actif and not st.session_state.abonne:

    if st.session_state.email_deja_essaye:
        st.error("🔒 Cet email a déjà utilisé l'essai gratuit. Passez au paiement ci-dessous.")
        # ... (bloc paiement identique à votre code original)
        # [Je l'omets ici pour lisibilité — gardez votre bloc col1/col2/col3]

    else:
        st.markdown("### 🎓 Bienvenue sur votre tuteur !")
        st.markdown(f"""
        Posez **n'importe quelle question** dans **toutes les matières**.

        **Essai gratuit :**
        - ✅ **{DUREE_ESSAI_JOURS} jours** d'accès
        - ✅ **{MAX_QUESTIONS_ESSAI} questions gratuites**
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
                st.session_state.email_deja_essaye = True
                st.session_state.email_verifie = email.strip().lower()
                st.rerun()
            else:
                creer_essai(email)
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
    # ... (votre bloc col1/col2/col3 de paiement)

# ---------- CAS 3 : accès OK ----------
else:
    if st.session_state.abonne:
        st.success("✅ Premium — illimité")
    else:
        st.success(f"🎁 Essai — {questions_restantes()} question(s) restante(s)")

    if st.session_state.reponse_a_afficher:
        st.markdown("### 📖 Réponse")
        st.caption(f"Question : {st.session_state.question_a_afficher}")
        st.markdown(st.session_state.reponse_a_afficher)
        st.markdown("---")

    st.markdown("### 💬 Posez votre question")
    with st.form("form_question"):
        question = st.text_area("Votre question :", height=120,
                                placeholder="Ex: Résous x+8=7 · Explique la photosynthèse…")
        submit = st.form_submit_button("🚀 Envoyer", type="primary",
                                       use_container_width=True)

    if submit:
        if not question.strip():
            st.warning("⚠️ Écrivez une question avant d'envoyer.")
        elif not acces_autorise():
            st.error("🔒 Essai terminé.")
        else:
            # ⚠️ CORRECTION CLÉ : ne décompter QUE si l'IA répond correctement
            reponse = None
            erreur = None
            with st.spinner("🤔 L'IA réfléchit à votre question..."):
                try:
                    reponse = generer_reponse_ia(question)
                    # Détecter les faux succès (503 encapsulé dans une string)
                    if reponse is None or "503" in str(reponse) or "UNAVAILABLE" in str(reponse):
                        erreur = "L'IA est momentanément indisponible."
                        reponse = None
                except Exception as e:
                    erreur = str(e)
                    reponse = None

            if erreur or not reponse:
                st.error(f"⚠️ {erreur or 'Erreur inconnue'}. "
                         f"**Votre question n'a pas été décomptée.** Réessayez dans un instant.")
            else:
                st.session_state.question_a_afficher = question
                st.session_state.reponse_a_afficher = reponse

                if not st.session_state.abonne:
                    st.session_state.questions_posees += 1
                    incrementer_questions(st.session_state.email_essai)

                st.markdown("### 📖 Réponse du tuteur")
                st.markdown(reponse)
