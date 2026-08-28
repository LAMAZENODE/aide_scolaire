import streamlit as st
import stripe

st.set_page_config(page_title="Tuteur Scolaire IA", page_icon="📚", layout="centered")

# Sécurité : Vérifie que le fichier secrets.toml contient bien les clés nécessaires
try:
    stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
    ID_PRIX_UNIQUE = st.secrets["STRIPE_PRICE_ID"]
    URL_APP = st.secrets["MON_URL_STREAMLIT"]
except KeyError as e:
    st.error(f"❌ Erreur de configuration : La clé `{e.args[0]}` est manquante dans votre fichier `.streamlit/secrets.toml`")
    st.stop()

est_abonne = False
query_params = st.query_params

# Vérification du paiement Stripe via l'URL de retour
if "session_id" in query_params:
    try:
        session = stripe.checkout.Session.retrieve(query_params["session_id"])
        if session.payment_status == "paid":
            est_abonne = True
    except Exception:
        st.error("Impossible de vérifier le statut du paiement.")

# --- INTERFACE 1 : L'utilisateur n'a pas encore payé ---
if not est_abonne:
    st.title("📚 Tuteur Scolaire IA")
    st.markdown("### Votre assistant pour toutes les matières")
    
    st.markdown("""
    <div style="background: #F3F4F6; padding: 20px; border-radius: 10px; border-left: 5px solid #10B981;">
        <h4>🚀 Offre Spéciale</h4>
        <p style="font-size: 2em; color: #10B981;">5,00 €</p>
        <ul>
            <li>✅ Toutes les matières</li>
            <li>✅ 24h/24, 7j/7</li>
            <li>✅ Paiement unique</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("💳 Débloquer l'accès", type="primary", use_container_width=True):
        try:
            session = stripe.checkout.Session.create(
                line_items=[{'price': ID_PRIX_UNIQUE, 'quantity': 1}],
                mode='payment',
                success_url=f"{URL_APP}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=URL_APP,
            )
            st.markdown(f"### [🔗 Cliquer ici pour payer]({session.url})")
            st.caption("🔒 Paiement sécurisé par Stripe")
        except Exception as e:
            st.error(f"Erreur lors de la création de la session Stripe: {e}")

# --- INTERFACE 2 : L'accès est validé (Paiement réussi) ---
else:
    st.success("✅ Accès débloqué")
    st.title("🎓 Mon Tuteur Scolaire")
    
    matiere = st.selectbox(
        "Sélectionnez la matière",
        ["maths", "francais", "anglais", "histoire", "sciences", "autres"]
    )
    
    question = st.text_area(
        "✍️ Posez votre question :", 
        height=300,
        placeholder="Ex: Résoudre 2x + 5 = 13"
    )

    if st.button("🚀 Obtenir la réponse", type="primary", use_container_width=True):
        if question.strip():
            with st.spinner("🔄 L'IA analyse votre question..."):
                from ia_utils import generer_reponse_ia
                reponse = generer_reponse_ia(question, matiere)
                
                st.markdown("### 📝 Réponse :")
                st.write(reponse)
        else:
            st.warning("⚠️ Veuillez poser une question.")


    