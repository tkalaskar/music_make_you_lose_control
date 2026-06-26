# music_make_you_lose_control

AI Music Composer turns a plain-English music idea into a playable WAV composition using a local or API-backed LLM.

## Problem Statement

Writing a melody from scratch is intimidating if you do not already know music theory or have access to a digital audio workstation. I wanted to build something that makes musical experimentation feel immediate: describe a mood, choose a style, and hear a rough musical idea within seconds.

The practical problem this solves is the gap between creative intent and musical output. A user may know they want "an upbeat electronic intro" or "a calm jazz loop", but not know how to translate that into notes, chords, rhythm, or audio. This project acts as a lightweight composition assistant that converts that intent into structured musical pieces and a playable sound preview.

## My Approach & Reasoning

I kept the architecture intentionally small and modular because the main engineering goal was fast iteration from prompt to sound. Instead of building a large backend service, I used Streamlit as the app layer so the input form, provider controls, audio player, and generated summary could live in one simple interface.

The core generation logic sits in `app/main.py` behind a `MusicLLM` class. This gives the app a single place to handle provider selection, model configuration, prompt construction, response cleanup, and fallback behavior. I chose this over scattering LLM calls directly through the Streamlit page because model providers changed during development: Groq was useful, but quota limits made a local fallback necessary. Keeping provider logic isolated made it straightforward to add Ollama without rewriting the UI.

For audio generation, I chose a simple synthesized WAV pipeline rather than MIDI export or a full audio engine. The goal was not studio-quality production; it was a working end-to-end prototype that proves an LLM can produce notes, chords, rhythm, and an audible result. `music21` handles note parsing, while `synthesizer`, `numpy`, and `scipy` render those frequencies into browser-playable audio.

I also added a random seed and variation controls because early generations felt too repetitive. The seed is passed into the local Ollama request and shown in the output so each run is traceable while still giving users fresh musical ideas.

## System Design Overview

The system follows a linear prompt-to-audio pipeline:

```text
User prompt + style + variation
        |
        v
Streamlit UI (app.py)
        |
        v
MusicLLM provider layer (Ollama by default, Groq optional)
        |
        v
Generated melody, harmony, rhythm, and summary
        |
        v
Note parsing and frequency conversion (music21)
        |
        v
WAV synthesis with rhythm durations
        |
        v
Streamlit audio playback
```

Key components:

- `app.py`: Streamlit interface for prompt input, style selection, provider selection, model selection, variation control, audio playback, and result display.
- `app/main.py`: LLM orchestration layer that supports Ollama and Groq, builds music-specific prompts, extracts notes/chords/durations, and keeps generations varied.
- `app/utils.py`: Music utility layer that converts note names to frequencies and renders a WAV byte stream.
- `requirements.txt`: Python dependencies for the app, LLM integrations, music parsing, and audio rendering.
- `Dockerfile`: Optional container entrypoint for running the Streamlit app.

Important tradeoffs:

- I favored a local-first LLM path over only using hosted APIs so the app remains usable when API quota is exhausted.
- I used simple text parsing for notes and chords instead of requiring strict JSON from the model, which keeps prompts flexible but needs cleanup logic.
- I rendered simple sine-wave audio rather than realistic instruments, which keeps the prototype lightweight but limits musical realism.

## Features

- Generate a melody from a natural language prompt.
- Choose a musical style such as Jazz, Rock, Pop, Classical, Country, or Electronic.
- Generate harmony chords to support the melody.
- Generate rhythm durations so the output does not sound like identical fixed-length notes.
- Render generated notes into playable WAV audio directly in the browser.
- Use free local inference through Ollama by default.
- Switch to Groq from the sidebar when an API-backed model is preferred.
- Control variation with a slider to reduce repetitive generations.
- Display the generated seed, melody, harmony, rhythm, and summary for transparency.

## Tech Stack & Why

| Technology | Why it was used |
| --- | --- |
| Python | Strong ecosystem for quick AI prototypes, audio processing, and readable application logic. |
| Streamlit | Fastest path to an interactive app without building a separate frontend and backend. |
| Ollama | Provides a free local LLM option and avoids hosted API quota limits. |
| Groq | Optional hosted inference path for users who have a Groq API key and want API-backed generation. |
| music21 | Converts symbolic note names like `C4` or `F#5` into musical pitch data. |
| numpy | Efficient array handling for generated audio samples. |
| scipy | Writes generated sample arrays into WAV format. |
| synthesizer | Lightweight oscillator-based audio synthesis for quick playback. |
| python-dotenv | Loads local `.env` configuration without hardcoding secrets. |
| Docker | Gives the project a portable deployment path for the Streamlit app. |

## Challenges & How I Solved Them

The first major issue was Groq quota exhaustion. The original app depended on Groq, so a quota error blocked the entire experience. I solved this by adding a provider layer and making Ollama the default path. This keeps the app usable locally while preserving Groq as an optional provider.

The second issue was dependency and API drift. The LangChain import path used by the original code no longer matched the installed package versions. I simplified the provider calls and moved the app toward a clearer `MusicLLM` abstraction so provider-specific details stay contained.

Another bug was that `generate_melody()` did not return a value, which caused the downstream harmony, rhythm, and audio pipeline to receive invalid input. I fixed the method and added cleanup logic that extracts valid note tokens from model output.

The audio renderer also had a real runtime bug: the synthesizer volume argument was accidentally passed a waveform enum instead of a numeric volume. I corrected the synth initialization and added a guard for empty note lists so failures are easier to understand.

Finally, early outputs sounded too similar. The model could generate different text, but the audio renderer flattened everything into equal half-second notes, and style only affected the summary. I fixed this by passing style into melody, harmony, and rhythm generation, adding a per-run seed, and making WAV generation honor the rhythm durations.

## What I'd Do Differently

I would pin dependency versions more tightly. This project exposed how quickly LLM libraries can shift APIs, and a production-ready version should use tested version ranges or a lock file.

I would move model outputs to a stricter schema. Regex cleanup works for a prototype, but structured JSON output validated with Pydantic would make melody, harmony, and rhythm parsing more reliable.

I would add automated tests around note extraction, rhythm parsing, and WAV generation. These are the places where small bugs can silently produce bad audio.

I would improve musical realism with MIDI export, instrument samples, or a more capable synthesis engine. The current sine-wave output is useful for proof of concept, but it is not meant to sound production-ready.

I would also add a Docker Compose setup for Ollama networking. The current Dockerfile runs the app, but local model serving needs explicit configuration when the app runs inside a container.

## Setup & Usage

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd AI-Music-Composer
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Set up Ollama for free local generation

Install Ollama, then pull the default model:

```bash
ollama pull llama3.2:latest
```

Make sure Ollama is running before using the local provider.

### 5. Optional environment configuration

Create a `.env` file if you want to override defaults:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:latest
OLLAMA_BASE_URL=http://localhost:11434
```

For Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=groq/compound
```

### 6. Run the Streamlit app

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, usually:

```text
http://localhost:8501
```

### 7. Generate music

1. Enter a prompt, for example `upbeat synth melody for a game intro`.
2. Select a style.
3. Keep `Local Ollama (free)` selected to avoid API quota limits.
4. Adjust the `Variation` slider if needed.
5. Click `Generate Music`.
6. Listen to the generated audio and inspect the melody, harmony, rhythm, seed, and summary.

## Docker Usage

Build the image:

```bash
docker build -t ai-music-composer .
```

Run the container on Docker Desktop for macOS or Windows:

```bash
docker run -p 8501:8501 ai-music-composer
```

The Dockerfile defaults `OLLAMA_BASE_URL` to `http://host.docker.internal:11434`, which lets the container reach Ollama running on your host machine in Docker Desktop.

On Linux, add the host gateway mapping:

```bash
docker run --add-host=host.docker.internal:host-gateway -p 8501:8501 ai-music-composer
```

To use Groq instead of local Ollama:

```bash
docker run -p 8501:8501 \
  -e LLM_PROVIDER=groq \
  -e GROQ_API_KEY=your_groq_api_key_here \
  -e GROQ_MODEL=groq/compound \
  ai-music-composer
```

If your Ollama server is somewhere else, override the base URL:

```bash
docker run -p 8501:8501 \
  -e OLLAMA_BASE_URL=http://your-ollama-host:11434 \
  ai-music-composer
```

