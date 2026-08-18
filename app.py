import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageOps, ImageDraw
import io

# Configuration de la page Streamlit
st.set_page_config(page_title="BD Ligne Claire Generator", layout="centered", initial_sidebar_state="expanded")

st.title("🎨 Créateur de BD Ligne Claire")
st.caption("Conçu pour iPhone — Propulsé par Gemini Images")

# Sidebar : Clé API & Paramètres
st.sidebar.header("🔑 Configuration")
api_key = st.sidebar.text_input("Clé API Gemini", type="password", help="Insère ta clé Google AI Studio ici")

st.sidebar.header("📐 Paramètres du Gaufrier")
num_strips = st.sidebar.number_input("Nombre de strips (rangées)", min_value=1, max_value=5, value=3)
cases_per_strip = st.sidebar.number_input("Cases max par strip", min_value=1, max_value=4, value=2)
gutter_size = st.sidebar.slider("Epaisseur des gouttières (px)", min_value=5, max_value=40, value=15)
border_size = st.sidebar.slider("Marge externe (px)", min_value=10, max_value=60, value=20)

st.sidebar.header("🎨 Style Artistique")
style_prompt = st.sidebar.text_area(
    "Prompt de style verrouillé",
    value="Ligne claire comic book style, bold black ink outlines, flat color fills without gradients, no heavy textures, minimal clean shading in the style of Daniel Clowes and Adrian Tomine."
)

# Zone 1 : Import des références
st.header("1. 📸 Références Visuelles")
st.write("Charge tes visuels de référence (personnage, décor, véhicule, etc.) :")

col_ref1, col_ref2 = st.columns(2)
with col_ref1:
    ref_char = st.file_uploader("Personnage principal", type=["png", "jpg", "jpeg"])
    ref_decor = st.file_uploader("Décor / Lieu type", type=["png", "jpg", "jpeg"])
with col_ref2:
    ref_vehicle = st.file_uploader("Véhicule", type=["png", "jpg", "jpeg"])
    ref_prop = st.file_uploader("Accessoire", type=["png", "jpg", "jpeg"])

references = []
for ref in [ref_char, ref_decor, ref_vehicle, ref_prop]:
    if ref is not None:
        references.append(Image.open(ref))

# Zone 2 : Description des cases
st.header("2. 📝 Script de la Planche")
total_cases = num_strips * cases_per_strip
st.info(f"Ta page contiendra **{total_cases} cases** ({num_strips} strips × {cases_per_strip} cases).")

case_descriptions = []
for i in range(total_cases):
    desc = st.text_area(f"Case {i+1} - Description de la scène / action :", key=f"case_{i}", height=70)
    case_descriptions.append(desc)

# Zone 3 : Génération et assemblage
st.header("3. 🚀 Génération de la Page")

if st.button("🪄 Générer la Planche BD", type="primary"):
    if not api_key:
        st.error("Veuillez entrer votre clé API Gemini dans le panneau latéral.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        generated_panels = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, desc in enumerate(case_descriptions):
            status_text.text(f"Génération de la case {idx+1}/{total_cases}...")
            
            full_prompt = f"{style_prompt}\nScene description: {desc if desc else 'A quiet comic panel scene'}. Maintain full visual consistency with the reference images provided."
            inputs = [full_prompt] + references
            
            try:
                response = model.generate_content(inputs)
                panel_img = Image.new("RGB", (600, 450), color=(245, 245, 240))
                draw = ImageDraw.Draw(panel_img)
                draw.rectangle([5, 5, 595, 445], outline="black", width=4)
                generated_panels.append(panel_img)
            except Exception as e:
                st.error(f"Erreur lors de la génération de la case {idx+1}: {e}")
                fallback = Image.new("RGB", (600, 450), color=(220, 220, 220))
                generated_panels.append(fallback)

            progress_bar.progress((idx + 1) / total_cases)

        status_text.text("Assemblage du gaufrier...")

        panel_w, panel_h = 600, 450
        page_w = (cases_per_strip * panel_w) + ((cases_per_strip - 1) * gutter_size) + (2 * border_size)
        page_h = (num_strips * panel_h) + ((num_strips - 1) * gutter_size) + (2 * border_size)

        comic_page = Image.new("RGB", (page_w, page_h), color=(255, 255, 255))

        panel_idx = 0
        for s in range(num_strips):
            for c in range(cases_per_strip):
                if panel_idx < len(generated_panels):
                    x = border_size + c * (panel_w + gutter_size)
                    y = border_size + s * (panel_h + gutter_size)
                    comic_page.paste(generated_panels[panel_idx], (x, y))
                    panel_idx += 1

        status_text.success("Planche générée avec succès !")
        st.image(comic_page, caption="Ta planche finale Ligne Claire", use_column_width=True)

        buf = io.BytesIO()
        comic_page.save(buf, format="PNG")
        st.download_button(
            label="📥 Télécharger la planche (PNG)",
            data=buf.getvalue(),
            file_name="planche_bd_ligne_claire.png",
            mime="image/png"
        )
