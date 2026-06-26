import streamlit as st
import os
from app.main import MusicLLM
from app.utils import *
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Music Composer", page_icon="🎵", layout="centered")
st.title("AI Music Composer")

st.markdown("Generate music using AI by describing a prompt.")

music_input = st.text_input("Describe the music you want to compose")
style = st.selectbox("Choose a style",["Jazz","Rock","Pop","Classical","Country","Electronic"])
provider_label = st.sidebar.selectbox("LLM provider",["Local Ollama (free)","Groq"])
provider = "ollama" if provider_label == "Local Ollama (free)" else "groq"
default_model = (
    os.getenv("OLLAMA_MODEL", "llama3.2:latest")
    if provider == "ollama"
    else os.getenv("GROQ_MODEL", "groq/compound")
)
model_name = st.sidebar.text_input("Model",value=default_model,key=f"{provider}_model")
temperature = st.sidebar.slider("Variation",0.2,1.4,0.9,0.1)

if st.button("Generate Music") and music_input:
    try:
        generator = MusicLLM(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
        )

        with st.spinner("Generating..."):
            melody = generator.generate_melody(music_input,style)
            harmony = generator.generate_harmony(melody,style)
            rhythm = generator.generate_rhythm(melody,style)

            composition = generator.adapt_style(style,melody,harmony,rhythm)

            melody_notes = melody.split()
            melody_freqs = note_to_freq(melody_notes)

            harmony_chords = harmony.split()
            harmony_notes= []
            for chor in harmony_chords:
                harmony_notes.extend(chor.split("-"))

            harmony_freqs = note_to_freq(harmony_notes)

            all_freqs = melody_freqs + harmony_freqs
            wav_bytes = generate_wav_bytes_notes_freqs(all_freqs,rhythm.split())

        st.audio(BytesIO(wav_bytes),format="audio/wav")

        st.success("🎉 Done! 🎉")

        with st.expander("Composition Summary"):
            st.text(
                f"Seed: {generator.seed}\n"
                f"Melody: {melody}\n"
                f"Harmony: {harmony}\n"
                f"Rhythm: {rhythm}\n\n"
                f"{composition}"
            )
    except Exception as exc:
        st.error(str(exc))
