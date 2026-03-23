import streamlit as st
from google import genai
import PIL.Image
from fpdf import FPDF
import io

# --- API CONFIG (SICUREZZA) ---
CHIAVE_API = st.secrets["CHIAVE_GOOGLE"]
client = genai.Client(api_key=CHIAVE_API)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AUTOCHEF AI", page_icon="👨‍🍳", layout="centered")

# --- CSS LOOK PROFESSIONALE ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #e63946; color: white; font-weight: bold; border: none; }
    .stTextArea>div>div>textarea { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AUTOCHEF AI")

# --- INIZIALIZZAZIONE ---
if 'ricetta' not in st.session_state:
    st.session_state.ricetta = None

# --- INPUT ---
col1, col2 = st.columns(2)
with col1:
    n_persone = st.number_input("Persone", 1, 20, 2)
with col2:
    dieta = st.selectbox("Dieta", ["Onnivoro", "Vegetariano", "Vegano", "Senza Glutine"])

esclusioni = st.text_input("Escludi (es: aglio, noci)")

# --- FOTOCAMERA E CARICAMENTO ---
st.write("### 📸 Scatta una foto")
with st.expander("📸 Vuoi scattare una foto ora? Clicca qui"):
    foto_scattata = st.camera_input("Inquadra gli ingredienti")

st.write("### 📂 Oppure carica file")
foto_galleria = st.file_uploader("Scegli dalla galleria", type=["jpg", "png"], accept_multiple_files=True)

immagini_per_gemini = []

if foto_scattata:
    img_s = PIL.Image.open(foto_scattata).convert('RGB')
    immagini_per_gemini.append(img_s)

if foto_galleria:
    for f in foto_galleria:
        try:
            img_g = PIL.Image.open(f).convert('RGB')
            img_g.thumbnail((800, 800))
            immagini_per_gemini.append(img_g)
        except:
            st.error("Errore con una foto della galleria")

ingredienti_testo = st.text_area("O scrivi gli ingredienti qui:")

# --- GENERAZIONE ---
if st.button("👨‍🍳 GENERA 3 RICETTE"):
    if not immagini_per_gemini and not ingredienti_testo:
        st.warning("Aggiungi almeno una foto o un ingrediente!")
    else:
        with st.spinner("Lo Chef sta creando..."):
            prompt = f"Sei uno Chef stellato e Sommelier. Crea 3 ricette per {n_persone} persone, dieta {dieta}. Escludi: {esclusioni}. Per ogni ricetta: Titolo, Ingredienti, Procedimento, Vino, Tabella Nutrizionale."
            
            contenuto = [prompt]
            if ingredienti_testo: contenuto.append(f"Testo: {ingredienti_testo}")
            if immagini_per_gemini: contenuto.extend(immagini_per_gemini)

            try:
                response = client.models.generate_content(model='gemini-1.5-flash', contents=contenuto)
                st.session_state.ricetta = response.text
            except Exception as e:
                st.error(f"Errore: {e}")

# --- RISULTATO E PDF ---
if st.session_state.ricetta:
    st.markdown("---")
    st.markdown(st.session_state.ricetta)
    
    # Generazione PDF (Semplice)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, st.session_state.ricetta.encode('latin-1', 'replace').decode('latin-1'))
    
    st.download_button("📄 Scarica PDF", data=pdf.output(dest='S'), file_name="ricette.pdf")

    if st.button("🗑️ Nuova Ricetta"):
        st.session_state.ricetta = None
        st.rerun()
