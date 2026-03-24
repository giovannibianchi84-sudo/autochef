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
st.write("### 📸 Opzioni Caricamento")

st.write("### 📂 Oppure carica file")

# MIGLIORIA 3: limite massimo di 5 immagini
foto_galleria = st.file_uploader(
    "Scegli dalla galleria (max 5 foto)",
    type=["jpg", "png"],
    accept_multiple_files=True
)

# Controllo limite immagini
if foto_galleria and len(foto_galleria) > 5:
    st.warning("⚠️ Puoi caricare al massimo 5 immagini. Verranno usate solo le prime 5.")
    foto_galleria = foto_galleria[:5]

immagini_per_gemini = []

if foto_galleria:
    for f in foto_galleria:
        try:
            img_g = PIL.Image.open(f).convert('RGB')
            img_g.thumbnail((800, 800))
            immagini_per_gemini.append(img_g)
        except Exception:
            st.error(f"⚠️ Errore nel caricare l'immagine: {f.name}. Prova con un altro file.")

ingredienti_testo = st.text_area("O scrivi gli ingredienti qui:")

# --- GENERAZIONE ---
if st.button("👨‍🍳 GENERA 3 RICETTE"):
    if not immagini_per_gemini and not ingredienti_testo:
        st.warning("Aggiungi almeno una foto o un ingrediente!")
    else:
        with st.spinner("Lo Chef sta creando..."):

            # MIGLIORIA 2: prompt più strutturato e dettagliato
            prompt = f"""
Sei uno Chef stellato Michelin e Sommelier esperto.
Analizza gli ingredienti forniti (testo e/o immagini) e crea esattamente 3 ricette diverse.

Parametri:
- Porzioni: {n_persone} persone
- Dieta: {dieta}
- Ingredienti da escludere: {esclusioni if esclusioni else "nessuno"}

Per ciascuna ricetta usa ESATTAMENTE questo formato:

## 🍽️ [Nome della Ricetta]

**Difficoltà:** [Facile / Media / Difficile]
**Tempo di preparazione:** [X minuti]
**Tempo di cottura:** [X minuti]

### Ingredienti
- [ingrediente 1 con quantità]
- [ingrediente 2 con quantità]
...

### Procedimento
1. [Passo 1]
2. [Passo 2]
...

### 🍷 Abbinamento Vino
[Vino consigliato con breve spiegazione]

### 📊 Tabella Nutrizionale (per porzione)
| Calorie | Proteine | Carboidrati | Grassi |
|---------|----------|-------------|--------|
| XXX kcal | XX g | XX g | XX g |

---
"""

            contenuto = [prompt]
            if ingredienti_testo:
                contenuto.append(f"Ingredienti disponibili (testo): {ingredienti_testo}")
            if immagini_per_gemini:
                contenuto.extend(immagini_per_gemini)

            # MIGLIORIA 1+4: modello aggiornato + gestione errori specifica
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=contenuto
                )
                st.session_state.ricetta = response.text

            except Exception as e:
                errore = str(e)
                if "429" in errore:
                    st.error("⏳ Hai raggiunto il limite di richieste gratuite. Aspetta qualche minuto e riprova.")
                elif "404" in errore:
                    st.error("❌ Modello non trovato. Controlla di usare 'gemini-2.5-flash'.")
                elif "400" in errore:
                    st.error("⚠️ Richiesta non valida. Prova a ridurre il numero di immagini o la lunghezza del testo.")
                elif "500" in errore or "503" in errore:
                    st.error("🔧 Servizio Gemini temporaneamente non disponibile. Riprova tra poco.")
                else:
                    st.error(f"❌ Errore inaspettato: {errore}")

# --- RISULTATO E PDF ---
if st.session_state.ricetta:
    st.markdown("---")
    st.markdown(st.session_state.ricetta)

    # MIGLIORIA 1: PDF con supporto UTF-8 corretto
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Usa un font che supporta i caratteri italiani
        pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", size=11)

        for line in st.session_state.ricetta.split('\n'):
            # Rimuove i simboli markdown dal PDF
            line_clean = line.replace("**", "").replace("##", "").replace("#", "").replace("---", "")
            pdf.multi_cell(0, 8, line_clean)

        st.download_button(
            "📄 Scarica PDF",
            data=pdf.output(dest='S'),
            file_name="ricette_autochef.pdf",
            mime="application/pdf"
        )
    except Exception:
        # Fallback se il font DejaVu non è disponibile
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, st.session_state.ricetta.encode('latin-1', 'replace').decode('latin-1'))
        st.download_button(
            "📄 Scarica PDF",
            data=pdf.output(dest='S'),
            file_name="ricette_autochef.pdf",
            mime="application/pdf"
        )

    if st.button("🗑️ Nuova Ricetta"):
        st.session_state.ricetta = None
        st.rerun()
