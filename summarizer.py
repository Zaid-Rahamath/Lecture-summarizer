import os
import numpy as np
import soundfile as sf
from scipy.signal import resample
import riva.client
import requests
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("NVIDIA_API_KEY")

TARGET_SAMPLE_RATE = 16000


# ---------- FILE INPUT HANDLING ----------

def get_notes_file():
    """Ask the user for a file, keep asking until they give a valid one."""
    while True:
        path = input("Enter the filename of your lecture notes (.txt, .pdf, .wav, .mp3): ").strip()
        path = path.strip('"').strip("'")
        if os.path.exists(path):
            return path
        print(f"Couldn't find '{path}' — make sure it's spelled right and in this folder. Try again.\n")


def read_text_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def read_pdf_file(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text


# ---------- AUDIO TRANSCRIPTION ----------

def load_and_resample(path):
    """Load any audio file and convert it to 16kHz mono, which NVIDIA's model requires."""
    audio, original_rate = sf.read(path)

    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if original_rate != TARGET_SAMPLE_RATE:
        num_samples = int(len(audio) * TARGET_SAMPLE_RATE / original_rate)
        audio = resample(audio, num_samples)

    audio_int16 = (audio * 32767).astype(np.int16)
    return audio_int16.tobytes()


def transcribe_audio(path):
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


# ---------- DISPATCHER ----------

def extract_text(path):
    """Pick the right method based on file extension: text, PDF, or audio."""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        return read_pdf_file(path)
    elif ext == ".txt":
        return read_text_file(path)
    elif ext in (".wav", ".mp3"):
        print("Detected audio file — transcribing first (this takes a bit longer)...")
        return transcribe_audio(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use .txt, .pdf, .wav, or .mp3")


# ---------- SUMMARIZATION ----------

def summarize(lecture_text):
    prompt = f"""You are an assistant that turns messy lecture notes into clean, exam-ready revision material.

Here are the raw notes:

{lecture_text}

Return your response in this exact structure:

## Summary
(2-3 sentence overview of what was covered)

## Key Points
(bulleted list of the most important facts/formulas/concepts)

## Likely Exam Focus
(anything the notes suggest will be tested)
"""

    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "nvidia/nemotron-3-super-120b-a12b",
        "messages": [{"role": "user", "content": prompt}]
    }

    max_retries = 2
    response = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            break
        except requests.exceptions.Timeout:
            print(f"Attempt {attempt} timed out after 60 seconds.")
            if attempt == max_retries:
                print("NVIDIA's server seems overloaded right now. Try again in a minute.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return None

    if response.status_code != 200:
        print(f"API returned an error — status code {response.status_code}")
        print(f"Response text: {response.text[:500]}")
        return None

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        print(f"Response wasn't valid JSON. Raw response: {response.text[:500]}")
        return None

    if "choices" not in data:
        print("Something went wrong. Full response below:")
        print(data)
        return None

    return data["choices"][0]["message"]["content"]


# ---------- MAIN (for standalone terminal use) ----------

def main():
    input_path = get_notes_file()

    print(f"\nReading {input_path}...")
    lecture_text = extract_text(input_path)

    if not lecture_text.strip():
        print("Couldn't extract any text from that file. Is it a scanned/image-based PDF, or silent audio?")
        return

    print("Sending to AI for summarization... (this takes a few seconds)\n")
    notes = summarize(lecture_text)

    if notes is None:
        return

    print(notes)

    save_choice = input("\nSave these notes to a file? (y/n): ").strip().lower()

    if save_choice == "y":
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}_summary.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(notes)
        print(f"Saved to: {output_path}")
    else:
        print("Not saved.")


if __name__ == "__main__":
    main()