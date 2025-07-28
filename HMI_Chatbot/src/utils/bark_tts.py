# src/utils/bark_tts.py
import os
import torch
import numpy as np
from scipy.io.wavfile import write as write_wav
from bark import SAMPLE_RATE, generate_audio, preload_models

class BarkTTS:
    def __init__(self):
        preload_models()
    
    def synthesize(self, text, output_path="bark_output.wav"):
        audio_array = generate_audio(text)
        write_wav(output_path, SAMPLE_RATE, audio_array)
        return output_path
