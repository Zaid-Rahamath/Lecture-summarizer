# 📘 Lecture Summarizer

An AI-powered study tool that turns lecture notes, PDFs, audio recordings, or YouTube lecture links into structured summaries — complete with key points and an exam-focus section.

Built with Streamlit as a first full-stack Python project.

## Features

- **Multiple input types**: upload `.txt`, `.pdf`, `.wav`, or `.mp3` files, or paste a YouTube link
- **AI-generated summaries**: key points, general notes, and a highlighted "exam focus" section
- **Dashboard**: study activity over time, content-type breakdown, summary length trends, and a day streak tracker
- **History**: browse and re-read past summaries, download any summary as Markdown
- **Custom UI**: dark themed interface with a background photo, animated cards, and a live clock

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Zaid-Rahamath/Lecture-summarizer.git
cd Lecture-summarizer
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:
- **Windows (PowerShell)**: `venv\Scripts\Activate.ps1`
- **Mac/Linux**: `source venv/bin/activate`

### 3. Install dependencies

```bash
pip install streamlit yt-dlp plotly pandas pypdf python-dotenv numpy soundfile scipy requests nvidia-riva-client
```

### 4. Add your API key

Copy the example env file:

```bash
cp .env.example .env
```

Then open `.env` and add your own NVIDIA API key:

```
NVIDIA_API_KEY=your_actual_key_here
```

Get a key at [build.nvidia.com](https://build.nvidia.com).

### 5. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Project Structure

```
lecture-summarizer/
├── app.py              # Main Streamlit UI
├── summarizer.py       # Text extraction + AI summarization logic
├── database.py         # SQLite storage for summary history
├── transcribe.py       # Audio transcription
├── assets/
│   └── bg-desk.jpg     # Background image
├── .env.example        # Template for your API key
└── .gitignore
```

## Notes

- On first run, a local SQLite database (`grimoire.db`) is created automatically to store your summary history — it isn't tracked in git, so each clone starts fresh.
- Audio transcription uses NVIDIA Riva; YouTube audio is downloaded via `yt-dlp`.

## About the Developer

Built by **Zaid** — this was my first full project, and building it meant learning a lot along the way: working with AI APIs, structuring a multi-file Python app, designing a custom UI in Streamlit, and using git/GitHub for the first time to ship it.

- GitHub: [@Zaid-Rahamath](https://github.com/Zaid-Rahamath)
