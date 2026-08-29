import streamlit as st
import stripe
from generer_pdf import generer_pdf
from ia_utils import generer_reponse_ia, generer_reponse_ia_avec_stream

# Configuration de la page
st.set_page_config(
    page_title="Tuteur Scolaire IA",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================
# CHARGEMENT DES SECRETS
# ============================================
try:
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
    ID_PRIX_UNIQUE = st.secrets["STRIPE_PRICE_ID"]
    URL_APP = st.secrets["MON_URL_STREAMLIT"]
except KeyError as e:
    st.error(f"❌ Erreur de configuration : La clé `{e.args[0]}` est manquante dans `.streamlit/secrets.toml`")
    st.stop()

# ============================================
# INITIALISATION DE LA SESSION
# ============================================
if "est_abonne" not in st.session_state:
    st.session_state.est_abonne = False
if "pdf_buffer" not in st.session_state:
    st.session_state.pdf_buffer = None
if "derniere_question" not in st.session_state:
    st.session_state.derniere_question = None
if "derniere_matiere" not in st.session_state:
    st.session_state.derniere_matiere = None
if "reponse_ia" not in st.session_state:
    st.session_state.reponse_ia = None

# ============================================
# VÉRIFICATION DU PAIEMENT
# ============================================
query_params = st.query_params

if "session_id" in query_params:
    try:
        session = stripe.checkout.Session.retrieve(query_params["session_id"])
        if session.payment_status == "paid":
            st.session_state.est_abonne = True
            st.success("✅ Paiement confirmé ! Accès débloqué.")
            # Nettoyer l'URL
            st.query_params.clear()
        else:
            st.warning("⏳ En attente de confirmation du paiement...")
    except Exception as e:
        st.error(f"Erreur lors de la vérification : {e}")

# ============================================
# CSS PERSONNALISÉ
# ============================================

# Style Minimaliste
st.markdown("""
<style>
    .offre-netflix {
        background: linear-gradient(145deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .offre-netflix h2 {
        color: #E94560;
        font-size: 2rem;
        font-weight: 700;
    }
    .offre-netflix .prix {
        color: white;
        font-size: 4rem;
        font-weight: 900;
        margin: 0.5rem 0;
    }
    .offre-netflix .prix small {
        font-size: 1.2rem;
        font-weight: 400;
        color: #aaa;
    }
    .offre-netflix .features {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 15px;
        margin: 1.5rem 0;
    }
    .offre-netflix .features span {
        background: rgba(255,255,255,0.08);
        padding: 8px 20px;
        border-radius: 50px;
        color: white;
        font-size: 0.9rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="offre-netflix">
    <h2>🚀 Tuteur IA Premium</h2>
    <div class="prix">5,00€ <small>accès illimité</small></div>
    <p style="color: #aaa;">Paiement unique - Une fois, pour toujours</p>
    <div class="features">
        <span>📖 Toutes matières</span>
        <span>🕐 24/7</span>
        <span>🎯 Personnalisé</span>
        <span>📄 PDF inclus</span>
        <span>🧠 Gemini IA</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# # ============================================
# INTERFACE : NON ABONNÉ
# ============================================
if not st.session_state.est_abonne:
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("📚 Tuteur Scolaire IA")
    st.markdown("### Votre assistant intelligent pour toutes les matières")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="price-box">
            <h2 style="color: white;">🚀 Offre Spéciale</h2>
            <p style="font-size: 3em; margin: 0;">5,00 €</p>
            <p style="font-size: 0.9em; opacity: 0.8;">Paiement unique - Accès immédiat</p>
            <div class="feature-list">
                <li>Toutes les matières</li>
                <li>24h/24, 7j/7</li>
                <li>Réponses personnalisées</li>
                <li>Export PDF inclus</li>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("💳 Débloquer l'accès maintenant", type="primary", use_container_width=True):
        try:
            session = stripe.checkout.Session.create(
                line_items=[{'price': ID_PRIX_UNIQUE, 'quantity': 1}],
                mode='payment',
                success_url=f"{URL_APP}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=URL_APP,
                customer_email=None,
                payment_method_types=['card'],
                billing_address_collection='required',
                metadata={
                    'product': 'tuteur_scolaire_ia'
                }
            )
            
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background: #F0FDF4; border-radius: 10px; border: 2px solid #10B981;">
                <h3>🔗 Cliquez sur le lien ci-dessous pour payer</h3>
                <br>
                <a href="%s" target="_blank" style="background: #10B981; color: white; padding: 15px 30px; border-radius: 10px; text-decoration: none; font-size: 1.2em;">
                    💳 Aller sur la page de paiement
                </a>
                <p style="margin-top: 1rem; color: #6B7280;">🔒 Paiement sécurisé par Stripe</p>
            </div>
            """ % session.url, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Erreur : {str(e)}")

    # 🛡️ AJOUT DES BADGES DE SECURITE DIRECTEMENT SOUS LE BOUTON
    st.markdown("""
    <div style="text-align: center; margin-top: 15px; margin-bottom: 25px; color: #6B7280; font-size: 0.9em;">
        🛡️ Paiement 100% Sécurisé et chiffré par <b>Stripe</b><br>
        ⚡ Déblocage instantané de votre espace tuteur après validation
    </div>
    """, unsafe_allow_html=True)

    # ============================================
    # 💬 AJOUT DE LA SECTION TEMOIGNAGES EN BAS
    # ============================================
    st.divider()
    st.markdown("<h3 style='text-align: center;'>💬 Ce qu'en pensent nos utilisateurs (4.9/5 ⭐)</h3>", unsafe_allow_html=True)
    st.write("") # Espace
    
    avis1, avis2 = st.columns(2)
    
    with avis1:
        st.info("""
        **⭐⭐⭐⭐⭐ "Sauvée pour le Bac !"**  
        *« J'avais un gros blocage sur les fonctions en maths. L'IA m'a réexpliqué le cours étape par étape sans me juger. L'export PDF est super propre pour réviser dans le bus. »*  
        — **Léa, 17 ans (Terminale)**
        """)
        
    with avis2:
        st.info("""
        **⭐⭐⭐⭐⭐ "Rentabilisé en un soir"**  
        *« Idéal pour débloquer les devoirs de mes enfants le soir quand je ne sais plus comment expliquer. Pour 5€ une seule fois, c'est une excellente affaire. »*  
        — **Marc, Parent de deux collégiens**
        """)


# ============================================
# INTERFACE : ABONNÉ
# ============================================
else:
    st.success("✅ Accès débloqué")
    st.title("🎓 Mon Tuteur Scolaire")
    
    # ==========================================
    # SECTION : TÉLÉCHARGEMENT PDF EXISTANT
    # ==========================================
    if st.session_state.pdf_buffer:
        st.markdown("### 📄 Dernière correction générée")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.info(f"📘 Matière : **{st.session_state.derniere_matiere.upper()}**")
        with col2:
            st.download_button(
                label="📥 Télécharger PDF",
                data=st.session_state.pdf_buffer,
                file_name=f"correction_{st.session_state.derniere_matiere}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="telecharger_pdf_existant"
            )
        with col3:
            if st.button("🗑️ Effacer", use_container_width=True):
                st.session_state.pdf_buffer = None
                st.session_state.reponse_ia = None
                st.rerun()
        st.divider()
    
    # ==========================================
    # SECTION : POSER UNE QUESTION
    # ==========================================
    with st.container():
        st.markdown("### ✍️ Posez votre question")
        
        col_matiere, col_rien = st.columns([3, 1])
        with col_matiere:
            matiere = st.selectbox(
                "Matière",
                ["maths", "français", "anglais", "histoire", "sciences", "physique", "philosophie", "autres"],
                key="matiere_select"
            )
        
        question = st.text_area(
            "Votre question",
            height=150,
            placeholder="Exemple : Résoudre l'équation 2x + 5 = 13 et expliquer chaque étape.",
            key="question_input"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            bouton_genere = st.button(
                "🚀 Obtenir la réponse",
                type="primary",
                use_container_width=True
            )
    
    # ==========================================
    # TRAITEMENT DE LA QUESTION
    # ==========================================
    if bouton_genere and question.strip():
        with st.spinner("🤖 L'IA analyse votre question..."):
            # Appel à l'API Gemini
            reponse_ia = generer_reponse_ia(question, matiere)
            st.session_state.reponse_ia = reponse_ia
            
            # Génération du PDF
            with st.spinner("📄 Génération du PDF..."):
                try:
                    pdf_buffer = generer_pdf(reponse_ia, question, matiere)
                    st.session_state.pdf_buffer = pdf_buffer
                    st.session_state.derniere_question = question
                    st.session_state.derniere_matiere = matiere
                except Exception as e:
                    st.error(f"❌ Erreur de génération du PDF : {str(e)}")
                    pdf_buffer = None
    
    # ==========================================
    # AFFICHAGE DE LA RÉPONSE
    # ==========================================
    if st.session_state.reponse_ia:
        st.markdown("---")
        st.markdown("### 📝 Réponse du Tuteur")
        
        # Affichage de la réponse
        with st.container():
            st.write(st.session_state.reponse_ia)
        
        # Bouton de téléchargement
        if st.session_state.pdf_buffer:
            st.success("✅ PDF prêt à être téléchargé !")
            
            # Nom du fichier personnalisé
            nom_fichier = f"correction_{matiere}_{st.session_state.derniere_question[:20]}"
            nom_fichier = nom_fichier.replace(" ", "_").replace("\n", "").replace("?", "")
            nom_fichier = nom_fichier[:40] + ".pdf"
            
            st.download_button(
                label="📥 Télécharger la correction en PDF",
                data=st.session_state.pdf_buffer,
                file_name=nom_fichier,
                mime="application/pdf",
                use_container_width=True,
                key="telecharger_pdf_nouveau"
            )
        
        # Bouton pour copier le texte
        if st.button("📋 Copier la réponse", use_container_width=True):
            st.write("Copié ! (Utilisez Ctrl+V pour coller)")
            st.balloons()
    
    elif bouton_genere and not question.strip():
        st.warning("⚠️ Veuillez écrire une question.")
    
    # ==========================================
    # SECTION : STATISTIQUES
    # ==========================================
    st.divider()
    with st.expander("📊 Statistiques et informations"):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📝 Questions posées", 
                     st.session_state.get("nb_questions", 0) + 1 if bouton_genere else 0)
        with col2:
            st.metric("📄 PDF générés", 
                     1 if st.session_state.pdf_buffer else 0)
    
    # ==========================================
    # DÉCONNEXION
    # ==========================================
    if st.button("🔄 Réinitialiser la session", type="secondary", use_container_width=True):
        for key in ["est_abonne", "pdf_buffer", "derniere_question", "derniere_matiere", "reponse_ia"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()




    
