import os
import numpy as np
import soundfile as sf
from scipy.signal import resample
import riva.client
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")

TARGET_SAMPLE_RATE = 16000

def load_and_resample(path):
    """Load any audio file and convert it to 16kHz mono, which NVIDIA's model requires."""
    audio, original_rate = sf.read(path)

    # If stereo, average the channels down to mono
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    # Resample to 16kHz if it isn't already
    if original_rate != TARGET_SAMPLE_RATE:
        num_samples = int(len(audio) * TARGET_SAMPLE_RATE / original_rate)
        audio = resample(audio, num_samples)

    # Convert to 16-bit PCM format, which is what the model expects
    audio_int16 = (audio * 32767).astype(np.int16)
    return audio_int16.tobytes()

def transcribe(path):
    audio_bytes = load_and_resample(path)

    auth = riva.client.Auth(
        uri="grpc.nvcf.nvidia.com:443",
        use_ssl=True,
        metadata_args=[
            ["function-id", "d3fe9151-442b-4204-a70d-5fcc597fd610"],
            ["authorization", f"Bearer {api_key}"],
        ],
    )
    asr_service = riva.client.ASRService(auth)

    config = riva.client.RecognitionConfig(
        encoding=riva.client.AudioEncoding.LINEAR_PCM,
        sample_rate_hertz=TARGET_SAMPLE_RATE,
        language_code="en-US",
        max_alternatives=1,
        enable_automatic_punctuation=True,
    )

    response = asr_service.offline_recognize(audio_bytes, config)

    full_transcript = ""
    for result in response.results:
        full_transcript += result.alternatives[0].transcript + " "

    return full_transcript.strip()

if __name__ == "__main__":
    print("Transcribing test_audio.wav...\n")
    text = transcribe("test_audio.wav")
    print("Transcript:")
    print(text)