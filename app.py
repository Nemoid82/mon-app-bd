import streamlit as st
from google import genai
from google.genai import types
from PIL import Image, ImageDraw
import io

st.set_page_config(page_title="BD Ligne Claire Generator", layout="centered")

st.title("🎨 Créateur de BD Ligne Claire")
st.caption("Conçu pour iPhone — Propulsé par Imagen 3 via Gemini API")

st.sidebar.header("🔑 Configuration")
api_key = st.sidebar.text_input("Clé API Gemini", type="password")

st.sidebar.header("📐 Paramètres du Gaufrier")
num_strips = st.sidebar.number_input("Nombre de strips", min_value=1, max_value=5, value=3)
cases_per_strip = st.sidebar.number_input("Cases max par strip", min_value=1, max_value=4, value=2)
gutter_size = st.sidebar.slider("Largeur gouttière (px)", min_value=5, max_value=40, value=15)
border_size = st.sidebar.slider("Marge externe (px)", min_value=10, max_value=60, value=20)

st.sidebar.header("🎨 Style Artistique")
style_prompt = st.sidebar.text_area(
    "Prompt de style",
    value="Ligne claire comic book panel style, bold black ink outlines, flat color fills, no gradients, clean drawing in the style of Daniel Clowes and Adrian Tomine."
)

st.header("1. 📝 Script des cases")
total_cases = num_strips * cases_per_strip
st.info(f"Page de **{total_cases} cases** ({num_strips} strips × {cases_per_strip} cases).")

case_descriptions = []
for i in range(total_cases):
    desc = st.text_area(f"Case {i+1} :", key=f"case_{i}", height=70)
    case_descriptions.append(desc)

st.header("2. 🚀 Génération")

if st.button("🪄 Générer la Planche BD", type="primary"):
    if not api_key:
        st.error("Renseigne ta clé API dans le panneau latéral.")
    else:
        # Initialisation du nouveau client Google GenAI
        client = genai.Client(api_key=api_key)

        generated_panels = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, desc in enumerate(case_descriptions):
            status_text.text(f"Génération de la case {idx+1}/{total_cases}...")
            
            full_prompt = f"{style_prompt} Detailed scene: {desc if desc else 'A quiet panel'}"
            
            try:
                # Modèle officiel de génération d'images Google
                result = client.models.generate_images(
                    model='imagen-3.0-generate-002',
                    prompt=full_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="4:3",
                        output_mime_type="image/png"
                    )
                )
                
                # Extraction de l'image générée
                for generated_image in result.generated_images:
                    image_bytes = generated_image.image.image_bytes
                    panel_img = Image.open(io.BytesIO(image_bytes))
                    generated_panels.append(panel_img)

            except Exception as e:
                st.error(f"Erreur case {idx+1}: {e}")
                # Image grise de secours en cas d'erreur
                fallback = Image.new("RGB", (600, 450), color=(220, 220, 220))
                generated_panels.append(fallback)

            progress_bar.progress((idx + 1) / total_cases)

        status_text.text("Assemblage du gaufrier...")

        # Dimensions et assemblage de la planche
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
                    # Redimensionnement propre
                    img = generated_panels[panel_idx].resize((panel_w, panel_h))
                    comic_page.paste(img, (x, y))
                    panel_idx += 1

        status_text.success("Planche générée !")
        st.image(comic_page, caption="Ta planche finale BD", use_column_width=True)

        buf = io.BytesIO()
        comic_page.save(buf, format="PNG")
        st.download_button("📥 Télécharger la planche", data=buf.getvalue(), file_name="planche_bd.png", mime="image/png")
