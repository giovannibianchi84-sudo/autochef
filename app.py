import streamlit as st
from google import genai
from PIL import Image
from fpdf import FPDF
import io

# Configurazione estetica e stabilità
st.set_page_config(page_title="AUTOCHEF", page_icon="👨‍🍳", layout="centered")

# --- CSS PER LOOK PROFESSIONALE ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #e63946; color: white; font-weight: bold; border: none; }
    .stTextArea>div>div>textarea { border-radius: 10px; }
    .stNumberInput>div>div>input { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- API CONFIG ---
CHIAVE_API = st.secrets["CHIAVE_GOOGLE"]
client = genai.Client(api_key=CHIAVE_API)

# --- LOGICA DI RESET ---
def reset_app():
    st.session_state.clear()
    st.rerun()

# --- HEADER ---
st.title("🤖 AUTOCHEF")
st.info("Scatta una foto o scrivi gli ingredienti. Io penserò al resto.")

# --- INPUT ---
st.subheader("📸 1. Ingredienti")
foto_caricate = st.file_uploader("Carica foto", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)

ingredienti_testo = st.text_area(
    "Ingredienti aggiuntivi o lista manuale:", 
    placeholder="es: Ho anche dello zafferano e del riso venere...",
    help="Qui puoi aggiungere spezie o ingredienti non visibili in foto."
)

st.subheader("⚙️ 2. Personalizza")
c1, c2, c3 = st.columns([1,2,2])
with c1:
    persone = st.number_input("Persone", min_value=1, value=2)
with c2:
    dieta = st.multiselect("Dieta", ["Vegetariana", "Vegana", "Senza Glutine", "Senza Lattosio"])
with c3:
    esclusioni = st.text_input("Escludi", placeholder="es: no aglio")

# --- AZIONE ---
if st.button("✨ GENERA IL MENU"):
    if not foto_caricate and not ingredienti_testo:
        st.warning("Lo Chef ha bisogno di almeno un ingrediente!")
    else:
        with st.spinner('🍳 Lo Chef cucina e il Sommelier sceglie i vini...'):
            # Prompt evoluto: include le "basi" della cucina in automatico
            prompt_base = f"""
            Sei AUTOCHEF. Crea 3 RICETTE per {persone} persone.
            DIETA: {', '.join(dieta)} | ESCLUSIONI: {esclusioni}.
            IMPORTANTE: Assumi che l'utente abbia sempre sale, pepe, olio, aceto e spezie base.
            
            FORMATO PER OGNI RICETTA:
            - Titolo, Difficoltà, Tempo.
            - Tabella Ingredienti con dosi per {persone}.
            - Passaggi numerati con minuti di cottura precisi.
            - Tabella Nutrizionale (Cal, Pro, Carb, Fat).
            - 🍷 IL SOMMELIER CONSIGLIA: Abbinamento vino/bevanda.
            """
            
            contenuto = [prompt_base + f"\nTesto utente: {ingredienti_testo}"]
            if foto_caricate:
                for f in foto_caricate:
                    img = Image.open(f).convert('RGB')
                    img.thumbnail((1024, 1024))
                    contenuto.append(img)

            try:
                response = client.models.generate_content(
                    model='models/gemini-flash-latest',
                    config={'system_instruction': prompt_base},
                    contents=contenuto
                )
                st.session_state.risultato = response.text
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Errore: {e}")

# --- FOOTER (PDF & RESET) ---
if 'risultato' in st.session_state:
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", size=11)
            t = st.session_state.risultato.replace('**', '').replace('*', '-').encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 8, txt=t)
            st.download_button("📄 Scarica PDF", data=bytes(pdf.output()), file_name="menu_autochef.pdf")
        except: st.info("Generazione PDF...")
    with col_b:
        st.button("🧹 Nuova Ricetta", on_click=reset_app)
