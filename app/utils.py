import music21
import numpy as np
import io
from scipy.io.wavfile import write as write_wav
from synthesizer import Synthesizer,Waveform

def note_to_freq(note_list):
    freqs=[]

    for note in note_list:
        try:
            note=music21.note.Note(note)
            freqs.append(note.pitch.frequency)
        except:
            continue
    return freqs


def generate_wav_bytes_notes_freqs(notes_freqs,durations=None):
    if not notes_freqs:
        raise RuntimeError("No playable notes were generated.")

    synth = Synthesizer(osc1_waveform=Waveform.sine,osc1_volume=0.8,use_osc2=False)
    sample_rate = 44100
    beat_seconds = 0.35
    if durations:
        parsed_durations = []
        for duration in durations:
            try:
                parsed_durations.append(max(0.1,min(float(duration),4.0)) * beat_seconds)
            except ValueError:
                continue
    else:
        parsed_durations = []

    if not parsed_durations:
        parsed_durations = [0.5]

    audio_parts = []
    gap = np.zeros(int(sample_rate * 0.03),dtype=np.float32)
    for index,freq in enumerate(notes_freqs):
        duration = parsed_durations[index % len(parsed_durations)]
        note_audio = synth.generate_constant_wave(freq,duration).astype(np.float32)
        fade_len = min(int(sample_rate * 0.01),len(note_audio) // 2)
        if fade_len:
            fade_in = np.linspace(0.0,1.0,fade_len)
            fade_out = np.linspace(1.0,0.0,fade_len)
            note_audio[:fade_len] *= fade_in
            note_audio[-fade_len:] *= fade_out
        audio_parts.extend([note_audio,gap])

    audio=np.concatenate(audio_parts)
    buffer = io.BytesIO()
    write_wav(buffer, sample_rate, audio.astype(np.float32))

    return buffer.getvalue()




