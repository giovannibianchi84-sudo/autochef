import streamlit as st
from google import genai
import PIL.Image
from fpdf import FPDF
import io

# --- API CONFIG (SICUREZZA) ---
# Usa i Secrets di Streamlit per la chiave API
CHIAVE_API = st.secrets["CHIAVE_GOOGLE"]
client = genai.Client(api_key=CHIAVE_API)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AUTOCHEF AI", page_icon="👨‍🍳", layout="centered")

# --- CSS PER LOOK PROFESSIONALE (FIXATO) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #e63946; color: white; font-weight: bold; border: none; }
    .stTextArea>div>div>textarea { border-radius: 10px; }
    .stNumberInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 AUTOCHEF AI")
st.subheader("Trasforma i tuoi ingredienti in capolavori!")

# --- INIZIALIZZAZIONE SESSIONE ---
if 'ricetta' not in st.session_state:
    st.session_state.ricetta = None

# --- INPUT UTENTE ---
col1, col2 = st.columns(2)
with col1:
    n_persone = st.number_input("Per quante persone?", min_value=1, max_value=20, value=2)
with col2:
    dieta = st.selectbox("Regime alimentare", ["Onnivoro", "Vegetariano", "Vegano", "Chetogenico", "Senza Glutine"])

esclusioni = st.text_input("Ingredienti da escludere (es: cipolla, arachidi)")

# --- CARICAMENTO FOTO (SISTEMA ANTI-AXIOS) ---
st.write("📸 **Carica le foto degli ingredienti o del frigo**")
foto_caricate = st.file_uploader("Puoi caricare fino a 4 foto", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# Lista per le immagini pulite e ridimensionate
immagini_per_gemini = []

if foto_caricate:
    cols = st.columns(len(foto_caricate))
    for i, f in enumerate(foto_caricate):
        try:
            # Pulizia e ridimensionamento immediato (Simula lo screenshot)
            img = PIL.Image.open(f).convert('RGB')
            img.thumbnail((800, 800)) # Riduce il peso per evitare errori di rete
            cols[i].image(img, use_container_width=True)
            immagini_per_gemini.append(img)
        except Exception as e:
            st.error(f"Errore tecnico sulla foto {i+1}")

ingredienti_testo = st.text_area("Oppure scrivi qui gli ingredienti che hai a disposizione:")

# --- LOGICA DI GENERAZIONE ---
if st.button("👨‍🍳 GENERA 3 PROPOSTE GOURMET"):
    if not immagini_per_gemini and not ingredienti_testo:
        st.warning("Per favore, carica una foto o scrivi almeno un ingrediente!")
    else:
        with st.spinner("Lo Chef sta analizzando gli ingredienti..."):
            prompt_base = f"""Sei uno Chef stellato esperto in cucina creativa e sommelier. 
            Analizza gli ingredienti (dalle foto o dal testo) e proponi 3 ricette diverse per {n_persone} persone, 
            seguendo una dieta {dieta}. Escludi tassativamente: {esclusioni}.
            
            Per ogni ricetta fornisci:
            1. Titolo accattivante.
            2. Lista ingredienti dettagliata.
            3. Procedimento sintetico ma chiaro.
            4. Abbinamento vino ideale (Sommelier).
            5. Tabella nutrizionale approssimativa (Calorie, Proteine, Carboidrati, Grassi).
            
            Usa un tono professionale e invitante."""

            # Prepariamo il contenuto per Gemini
            contenuto = [prompt_base]
            if ingredienti_testo:
                contenuto.append(f"Ingredienti scritti dall'utente: {ingredienti_testo}")
            if immagini_per_gemini:
                contenuto.extend(immagini_per_gemini)

            try:
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=contenuto
                )
                st.session_state.ricetta = response.text
            except Exception as e:
                st.error(f"Errore di comunicazione con lo Chef: {e}")

# --- VISUALIZZAZIONE RISULTATO E PDF ---
if st.session_state.ricetta:
    st.markdown("---")
    st.markdown(st.session_state.ricetta)
    
    # Generazione PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, st.session_state.ricetta.encode('latin-1', 'replace').decode('latin-1'))
    
    pdf_output = io.BytesIO()
    pdf_data = pdf.output(dest='S')
    pdf_output.write(pdf_data)
    pdf_output.seek(0)
    
    st.download_button(
        label="📄 Scarica Ricette in PDF",
        data=pdf_output,
        file_name="autochef_ricette.pdf",
        mime="application/pdf"
    )

    if st.button("🗑️ Reset e Nuova Ricetta"):
        st.session_state.ricetta = None
        st.rerun()
