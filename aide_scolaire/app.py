import streamlit as st
import stripe
from generer_pdf import generer_pdf
from ia_utils import generer_reponse_ia

# ============================================
# CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Tuteur Scolaire IA",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================
# SECRETS
# ============================================
try:
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
    URL_APP = st.secrets["MON_URL_STREAMLIT"]
    # Plusieurs prix pour les paliers
    PRIX = {
        "jour": st.secrets["STRIPE_PRICE_JOUR"],       # 2,99€
        "mois": st.secrets["STRIPE_PRICE_MOIS"],       # 9,99€
        "bac": st.secrets["STRIPE_PRICE_BAC"],         # 19,99€
    }
except KeyError as e:
    st.error(f"❌ Clé manquante dans secrets.toml : `{e.args[0]}`")
    st.stop()

# ============================================
# CONSTANTES
# ============================================
QUESTIONS_GRATUITES = 3

# ============================================
# INITIALISATION SESSION
# ============================================
defaults = {
    "est_abonne": False,
    "nb_questions_utilisees": 0,
    "pdf_buffer": None,
    "derniere_question": None,
    "derniere_matiere": None,
    "reponse_ia": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================
# VÉRIFICATION PAIEMENT STRIPE
# ============================================
qp = st.query_params
if "session_id" in qp:
    try:
        session = stripe.checkout.Session.retrieve(qp["session_id"])
        if session.payment_status == "paid":
            st.session_state.est_abonne = True
            st.success("✅ Paiement confirmé ! Accès débloqué.")
            st.query_params.clear()
        else:
            st.warning("⏳ En attente de confirmation du paiement...")
    except Exception as e:
        st.error(f"Erreur Stripe : {e}")

# ============================================
# CSS
# ============================================
st.markdown("""
<style>
    .offre-netflix {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 20px; padding: 2.5rem; text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .offre-netflix h2 { color: #E94560; font-size: 2rem; font-weight: 700; }
    .offre-netflix .prix { color: white; font-size: 4rem; font-weight: 900; margin: 0.5rem 0; }
    .offre-netflix .prix small { font-size: 1.2rem; font-weight: 400; color: #aaa; }
    .offre-netflix .features {
        display: flex; flex-wrap: wrap; justify-content: center;
        gap: 15px; margin: 1.5rem 0;
    }
    .offre-netflix .features span {
        background: rgba(255,255,255,0.08); padding: 8px 20px;
        border-radius: 50px; color: white; font-size: 0.9rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .badge-essai {
        background: #FEF3C7; color: #92400E; padding: 10px 20px;
        border-radius: 10px; text-align: center; font-weight: 600;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INTERFACE : NON ABONNÉ
# ============================================
if not st.session_state.est_abonne:
    restantes = QUESTIONS_GRATUITES - st.session_state.nb_questions_utilisees

    # --- PHASE 1 : ESSAI GRATUIT DISPONIBLE ---
    if restantes > 0:
        st.title("📚 Tuteur Scolaire IA")
        st.markdown("### Ton assistant intelligent pour toutes les matières")

        st.markdown(
            f'<div class="badge-essai">🎁 ESSAI GRATUIT — '
            f'{restantes} question(s) restante(s) sur {QUESTIONS_GRATUITES}</div>',
            unsafe_allow_html=True
        )

        with st.container():
            matiere = st.selectbox(
                "Matière",
                ["maths", "français", "anglais", "histoire", "sciences",
                 "physique", "philosophie", "autres"],
                key="matiere_essai"
            )
            question = st.text_area(
                "Ta question",
                height=150,
                placeholder="Ex : Explique-moi les fonctions affines simplement.",
                key="question_essai"
            )
            btn = st.button("🚀 Obtenir ma réponse gratuite", type="primary",
                            use_container_width=True)

        if btn:
            if not question.strip():
                st.warning("⚠️ Écris une question.")
            else:
                with st.spinner("🤖 L'IA réfléchit..."):
                    reponse = generer_reponse_ia(question, matiere)
                    st.session_state.reponse_ia = reponse
                    st.session_state.derniere_question = question
                    st.session_state.derniere_matiere = matiere
                    st.session_state.nb_questions_utilisees += 1

                    # PDF offert aussi pendant l'essai (argument de vente)
                    try:
                        st.session_state.pdf_buffer = generer_pdf(reponse, question, matiere)
                    except Exception as e:
                        st.error(f"PDF : {e}")

                st.rerun()

        # Affichage réponse + PDF
        if st.session_state.reponse_ia:
            st.markdown("---")
            st.markdown("### 📝 Réponse du Tuteur")
            st.write(st.session_state.reponse_ia)

            if st.session_state.pdf_buffer:
                st.download_button(
                    "📥 Télécharger en PDF",
                    data=st.session_state.pdf_buffer,
                    file_name="correction.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_essai"
                )

    # --- PHASE 2 : ESSAI ÉPUISÉ → OFFRES PAYANTES ---
    else:
        st.markdown("""
        <div class="offre-netflix">
            <h2>🎓 Tu as aimé ton essai ?</h2>
            <p style="color: #aaa; font-size: 1.1rem;">
                Débloque l'accès <b>illimité</b> et continue sans t'arrêter.
            </p>
            <div class="features">
                <span>📖 Toutes matières</span>
                <span>🕐 24/7</span>
                <span>🎯 Personnalisé</span>
                <span>📄 PDF inclus</span>
                <span>🧠 Gemini IA</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        st.markdown("### 💎 Choisis ta formule")

  
        col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### ⚡ Pass Journée")
    st.markdown("**2,99€**")
    st.caption("24h illimité — idéal avant un contrôle")
    st.link_button(
        "💳 Payer",
        LIENS_PAIEMENT["https://buy.stripe.com/7sYfZg5TVfmibjuaJq8g004"],
        use_container_width=True
    )

with col2:
    st.markdown("#### 🌟 Mensuel ⭐")
    st.markdown("**9,99€/mois**")
    st.caption("Le plus populaire — annulable en 1 clic")
    st.link_button(
        "💳 Payer",
        LIENS_PAIEMENT["https://buy.stripe.com/3cIdR8gyzfmifzKcRy8g005"],
        use_container_width=True,
        type="primary"
    )

with col3:
    st.markdown("#### 🎓 Pack Bac")
    st.markdown("**19,99€**")
    st.caption("3 mois d'accès — révisions complètes")
    st.link_button(
        "💳 Payer",
        LIENS_PAIEMENT["https://buy.stripe.com/aFadR8dmn3DA2MY04M8g006"],
        use_container_width=True
    )

       
        st.markdown("""
        <div style="text-align:center; margin-top:20px; color:#6B7280; font-size:0.9em;">
            🛡️ Paiement sécurisé par <b>Stripe</b><br>
            ⚡ Déblocage instantané
        </div>
        """, unsafe_allow_html=True)

        # Témoignages
        st.divider()
        st.markdown(
            "<h3 style='text-align:center;'>💬 Ils ont testé (4.9/5 ⭐)</h3>",
            unsafe_allow_html=True
        )
        a1, a2 = st.columns(2)
        with a1:
            st.info(
                "**⭐⭐⭐⭐⭐ « Sauvée pour le Bac ! »**\n\n"
                "*« L'IA m'a réexpliqué étape par étape sans me juger. »*\n\n"
                "— **Léa, 17 ans**"
            )
        with a2:
            st.info(
                "**⭐⭐⭐⭐⭐ « Rentabilisé en un soir »**\n\n"
                "*« Idéal pour débloquer les devoirs le soir. »*\n\n"
                "— **Marc, parent**"
            )
# ============================================
# INTERFACE : ABONNÉ
# ============================================
else:
    st.success("✅ Accès illimité débloqué")
    st.title("🎓 Mon Tuteur Scolaire")

    # PDF existant
    if st.session_state.pdf_buffer:
        st.markdown("### 📄 Dernière correction")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            st.info(f"📘 Matière : **{st.session_state.derniere_matiere.upper()}**")
        with c2:
            st.download_button(
                "📥 Télécharger",
                data=st.session_state.pdf_buffer,
                file_name=f"correction_{st.session_state.derniere_matiere}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dl_abo"
            )
        with c3:
            if st.button("🗑️ Effacer", use_container_width=True):
                st.session_state.pdf_buffer = None
                st.session_state.reponse_ia = None
                st.rerun()
        st.divider()

    # Nouvelle question
    st.markdown("### ✍️ Posez votre question")
    matiere = st.selectbox(
        "Matière",
        ["maths", "français", "anglais", "histoire", "sciences",
         "physique", "philosophie", "autres"],
        key="matiere_abo"
    )
    question = st.text_area(
        "Votre question",
        height=150,
        placeholder="Ex : Résoudre 2x + 5 = 13 et expliquer chaque étape.",
        key="question_abo"
    )
    btn = st.button("🚀 Obtenir la réponse", type="primary", use_container_width=True)

    if btn:
        if not question.strip():
            st.warning("⚠️ Écris une question.")
        else:
            with st.spinner("🤖 Analyse..."):
                reponse = generer_reponse_ia(question, matiere)
                st.session_state.reponse_ia = reponse
                st.session_state.derniere_question = question
                st.session_state.derniere_matiere = matiere
                try:
                    st.session_state.pdf_buffer = generer_pdf(reponse, question, matiere)
                except Exception as e:
                    st.error(f"PDF : {e}")

    if st.session_state.reponse_ia:
        st.markdown("---")
        st.markdown("### 📝 Réponse du Tuteur")
        st.write(st.session_state.reponse_ia)
        if st.session_state.pdf_buffer:
            st.download_button(
                "📥 Télécharger la correction en PDF",
                data=st.session_state.pdf_buffer,
                file_name="correction.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dl_abo_new"
            )

    st.divider()
    if st.button("🔄 Réinitialiser la session", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ============================================
# FONCTION CHECKOUT STRIPE
# ============================================
def _checkout(price_id, url_app):
    try:
        session = stripe.checkout.Session.create(
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",  # ou "subscription" pour le mensuel
            success_url=f"{url_app}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=url_app,
            payment_method_types=["card"],
            billing_address_collection="required",
            metadata={"product": "tuteur_scolaire_ia"}
        )
        st.markdown(f"""
        <div style="text-align:center; padding:2rem; background:#F0FDF4;
                    border-radius:10px; border:2px solid #10B981;">
            <h3>🔗 Clique sur le lien pour payer</h3>
            <br>
            <a href="{session.url}" target="_blank"
               style="background:#10B981; color:white; padding:15px 30px;
                      border-radius:10px; text-decoration:none; font-size:1.2em;">
                💳 Aller au paiement
            </a>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Erreur Stripe : {e}")
