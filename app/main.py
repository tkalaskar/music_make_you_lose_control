import os
import json
import random
import re
import urllib.error
import urllib.request

from langchain_groq import ChatGroq


NOTE_TOKEN = r"[A-Ga-g][#b]?[0-8]"
NOTE_RE = re.compile(rf"\b({NOTE_TOKEN})\b")
CHORD_RE = re.compile(rf"\b({NOTE_TOKEN}(?:-{NOTE_TOKEN}){{2,3}})\b")
DURATION_RE = re.compile(r"\b\d+(?:\.\d+)?\b")


class MusicLLM:
    def __init__(
        self,
        temperature=0.7,
        provider=None,
        model_name=None,
        ollama_base_url=None,
        seed=None,
    ):
        self.temperature = temperature
        self.provider = (provider or os.getenv("LLM_PROVIDER") or "ollama").lower()
        self.seed = seed or random.SystemRandom().randint(1, 2_147_483_647)
        self.ollama_base_url = (
            ollama_base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        ).rstrip("/")
        self.llm = None

        if self.provider == "ollama":
            self.model_name = model_name or os.getenv("OLLAMA_MODEL") or "llama3.2:latest"
        elif self.provider == "groq":
            self.model_name = model_name or os.getenv("GROQ_MODEL") or "groq/compound"
            self.llm = ChatGroq(
                temperature=temperature,
                groq_api_key=os.getenv("GROQ_API_KEY"),
                model_name=self.model_name,
            )
        else:
            raise ValueError("LLM provider must be 'ollama' or 'groq'.")

    def _chat(self, instruction, user_prompt):
        if self.provider == "groq":
            response = self.llm.invoke(
                [("system", instruction), ("human", user_prompt)]
            )
            return response.content.strip()

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": 0.95,
                "top_k": 50,
                "seed": self.seed,
            },
        }
        request = urllib.request.Request(
            f"{self.ollama_base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama model '{self.model_name}' failed: {details}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not connect to Ollama. Start Ollama and pull a local model "
                f"with: ollama pull {self.model_name}"
            ) from exc

        message = data.get("message", {})
        content = message.get("content", "").strip()
        if not content:
            raise RuntimeError("The local Ollama model returned an empty response.")
        return content

    def _normalize_note(self, note):
        letter = note[0].upper()
        accidental = note[1] if len(note) == 3 else ""
        octave = note[-1]
        return f"{letter}{accidental}{octave}"

    def _notes_from_text(self, text, fallback):
        notes = [self._normalize_note(note) for note in NOTE_RE.findall(text)]
        return " ".join(notes) if notes else fallback

    def _chords_from_text(self, text, fallback):
        chords = []
        for chord in CHORD_RE.findall(text):
            notes = [self._normalize_note(note) for note in chord.split("-")]
            chords.append("-".join(notes))
        return " ".join(chords) if chords else fallback

    def _durations_from_text(self, text, note_count):
        rhythm_text = NOTE_RE.sub(" ", text)
        durations = DURATION_RE.findall(rhythm_text)
        if durations:
            return " ".join(durations[:note_count])

        pattern = ["1.0", "0.5", "0.5", "1.0"]
        return " ".join(pattern[index % len(pattern)] for index in range(note_count))

    def generate_notes(self, user_prompt, style=None):
        return self.generate_melody(user_prompt, style)

    def generate_melody(self, user_prompt, style=None):
        style_text = f" in a {style} style" if style else ""
        response = self._chat(
            "You are a music composer. Return only space separated note names.",
            (
                f"Generate an 8 to 16 note melody{style_text} based on this input: "
                f"{user_prompt}. Variation seed: {self.seed}. "
                "Use a distinct contour, range, and ending for this seed. "
                "Use the format: C4 D4 E4 G4 A4 B4 C5."
            ),
        )
        return self._notes_from_text(response, "C4 D4 E4 G4 A4 G4 E4 C4")

    def generate_harmony(self, melody, style=None):
        style_text = f" for {style}" if style else ""
        response = self._chat(
            "You are a music arranger. Return only space separated triads.",
            (
                f"Create harmony chords{style_text} for this melody: "
                f"{melody}. Variation seed: {self.seed}. "
                "Use this exact format: C4-E4-G4 F4-A4-C5."
            ),
        )
        return self._chords_from_text(response, "C4-E4-G4 F4-A4-C5 G4-B4-D5")

    def generate_rhythm(self, melody, style=None):
        note_count = max(1, len(NOTE_RE.findall(melody)))
        style_text = f" in a {style} feel" if style else ""
        response = self._chat(
            "You are a rhythm arranger. Return only space separated beat durations.",
            (
                f"Suggest rhythm durations{style_text} for this melody: "
                f"{melody}. Variation seed: {self.seed}. "
                "Use this exact format: 1.0 0.5 0.5 2.0."
            ),
        )
        return self._durations_from_text(response, note_count)

    def adapt_style(self, style, melody, harmony, rhythm):
        return self._chat(
            "You are a concise music producer.",
            (
                f"Adapt to {style} style:\n"
                f"Melody: {melody}\n"
                f"Harmony: {harmony}\n"
                f"Rhythm: {rhythm}\n"
                f"Variation seed: {self.seed}\n"
                "Output a single short composition summary."
            ),
        )
