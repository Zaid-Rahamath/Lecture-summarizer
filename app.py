import streamlit as st
import streamlit.components.v1 as components
import tempfile
import base64
import os
import yt_dlp
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

from summarizer import extract_text, summarize
from database import init_db, save_summary, get_all_summaries, get_summary_count_by_date, get_source_type_breakdown

init_db()

st.set_page_config(page_title="Lecture Summarizer", page_icon="📘", layout="centered")


@st.cache_data
def load_bg_image_b64():
    """Read the background photo once and cache it as base64 for CSS embedding."""
    with open(os.path.join(os.path.dirname(__file__), "assets", "bg-desk.jpg"), "rb") as f:
        return base64.b64encode(f.read()).decode()


bg_image_b64 = load_bg_image_b64()

STYLE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    /* ---- Color tokens ---- */
    --c-bg: #2541B2;
    --c-bg-mid: #6D3FA8;
    --c-panel: #151E38;
    --c-coral: #FF6B5B;
    --c-orange: #FFA35C;
    --c-blue: #6C7AE0;
    --c-cyan: #4FD1E8;
    --c-text: #F1F3FA;
    --c-text-dim: #8A93B8;

    /* ---- Spacing scale ---- */
    --sp-xs: 6px;
    --sp-sm: 12px;
    --sp-md: 18px;
    --sp-lg: 26px;
    --sp-xl: 36px;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-image:
        linear-gradient(180deg, rgba(5, 4, 10, 0.5) 0%, rgba(5, 4, 10, 0.3) 45%, rgba(5, 4, 10, 0.55) 100%),
        url("data:image/jpeg;base64,__BG_IMAGE_B64__");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}

#MainMenu, footer, header {visibility: hidden;}

/* ---- Pin the flip-clock iframe to the actual top-right corner of the viewport ---- */
iframe {
    position: fixed !important;
    top: 14px !important;
    right: 22px !important;
    width: 110px !important;
    height: 32px !important;
    z-index: 9999 !important;
    border: none !important;
    background: transparent !important;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes borderGlow {
    0%, 100% { box-shadow: 0 0 26px rgba(255, 107, 91, 0.25), 0 0 0 1px rgba(255, 107, 91, 0.35) inset; }
    50% { box-shadow: 0 0 46px rgba(255, 163, 92, 0.4), 0 0 0 1px rgba(255, 163, 92, 0.5) inset; }
}
@keyframes inputPulse {
    0%, 100% { box-shadow: 0 0 0 rgba(79, 209, 232, 0.0); }
    50% { box-shadow: 0 0 24px rgba(79, 209, 232, 0.45); }
}

@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; transition: none !important; }
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 3.2rem;
    text-align: center;
    margin-bottom: 0;
    letter-spacing: -0.5px;
    animation: fadeInUp 0.6s ease both;
}
.hero-title .word-1 {
    color: #FFFFFF;
    text-shadow: 0 2px 20px rgba(0, 0, 0, 0.4);
}
.hero-title .word-2 {
    color: #C7D2FE;
    text-shadow: 0 2px 20px rgba(0, 0, 0, 0.4);
}

.hero-sub {
    text-align: center;
    color: #FFFFFF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 1.8rem;
    opacity: 0.8;
    text-shadow: 0 1px 12px rgba(0, 0, 0, 0.4);
    animation: fadeInUp 0.6s ease 0.1s both;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.25);
}
.stTabs [data-baseweb="tab"] {
    color: rgba(255, 255, 255, 0.65);
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    padding: 10px 4px;
    text-shadow: 0 1px 8px rgba(0, 0, 0, 0.35);
    transition: color 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #FFFFFF;
}
.stTabs [aria-selected="true"] {
    color: #FFFFFF !important;
    border-bottom: 2px solid var(--c-orange) !important;
}

/* ---- Drag & drop upload zone ---- */
[data-testid="stFileUploader"] {
    background: rgba(10, 8, 30, 0.4);
    border: 1.5px dashed rgba(79, 209, 232, 0.5);
    border-radius: 18px;
    padding: 4px;
    transition: all 0.35s ease;
    position: relative;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--c-cyan);
    box-shadow: 0 0 30px rgba(79, 209, 232, 0.25);
    background: rgba(10, 8, 30, 0.55);
    transform: translateY(-2px);
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    font-family: 'Inter', sans-serif;
    color: var(--c-text);
}
[data-testid="stFileUploaderDropzoneInstructions"]::before {
    content: "📥  ";
}

/* ---- YouTube link input: glows once it has a value ---- */
.stTextInput>div>div>input {
    background: rgba(10, 8, 30, 0.45);
    color: var(--c-text);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    font-family: 'JetBrains Mono', monospace;
    transition: all 0.3s ease;
}
.stTextInput>div>div>input:focus {
    box-shadow: 0 0 22px rgba(108, 122, 224, 0.4);
    border: 1px solid var(--c-blue);
}
.stTextInput>div>div>input:not(:placeholder-shown) {
    border: 1px solid var(--c-cyan);
    animation: inputPulse 2.2s ease-in-out infinite;
}

/* ---- Buttons: neumorphic + gradient ---- */
.stButton>button {
    background: linear-gradient(90deg, var(--c-coral), var(--c-orange));
    color: #16121A;
    border-radius: 12px;
    padding: 0.65em 2em;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    letter-spacing: 0.3px;
    border: none;
    transition: all 0.25s ease;
    box-shadow:
        0 4px 18px rgba(255, 107, 91, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.25),
        inset 0 -2px 6px rgba(0, 0, 0, 0.15);
}
.stButton>button:hover {
    box-shadow:
        0 0 30px rgba(255, 163, 92, 0.5),
        inset 0 1px 0 rgba(255, 255, 255, 0.3),
        inset 0 -2px 6px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
}
.stButton>button:active {
    transform: translateY(0);
}

.stDownloadButton>button {
    border-radius: 12px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    border: 1px solid rgba(79, 209, 232, 0.4);
    transition: all 0.25s ease;
}
.stDownloadButton>button:hover {
    box-shadow: 0 0 24px rgba(79, 209, 232, 0.3);
    transform: translateY(-2px);
}

/* ---- Glass cards (general notes) ---- */
.tome-card {
    background: rgba(10, 8, 30, 0.5);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 18px;
    padding: var(--sp-lg);
    margin-bottom: var(--sp-md);
    animation: fadeInUp 0.5s ease both;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
.tome-card:hover {
    transform: translateY(-3px);
    border-color: rgba(255, 255, 255, 0.28);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
}
.tome-card h4 {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--c-orange);
    margin-top: 0;
    letter-spacing: 0.2px;
}
.tome-card p, .tome-card li {
    color: var(--c-text);
    line-height: 1.65;
}

/* ---- Signature element: Exam Focus, glowing animated border ---- */
.exam-focus {
    background: linear-gradient(135deg, rgba(10, 8, 30, 0.6), rgba(30, 15, 20, 0.55));
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 18px;
    padding: var(--sp-lg);
    margin-top: var(--sp-md);
    animation: fadeInUp 0.5s ease both, borderGlow 3.5s ease-in-out infinite;
    position: relative;
}
.exam-focus h4 {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--c-orange);
    margin-top: 0;
    font-size: 1.15rem;
}
.exam-focus p, .exam-focus li {
    color: #FFF3EC;
    line-height: 1.65;
}

/* ---- Key points: color-coded, icon-led, expand-on-hover ---- */
.key-point {
    background: rgba(79, 209, 232, 0.06);
    border-left: 3px solid var(--c-cyan);
    border-radius: 10px;
    padding: 10px 16px;
    margin-bottom: 8px;
    color: var(--c-text);
    transition: all 0.2s ease;
}
.key-point:hover {
    background: rgba(79, 209, 232, 0.12);
    transform: translateX(4px);
    border-left-width: 5px;
}

/* ---- Stat cards: neumorphic ---- */
.stat-card {
    background: rgba(10, 8, 30, 0.5);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.06),
        inset 0 -8px 20px rgba(0, 0, 0, 0.25),
        0 6px 16px rgba(0, 0, 0, 0.3);
    transition: transform 0.25s ease;
    animation: fadeInUp 0.5s ease both;
}
.stat-card:hover {
    transform: translateY(-3px);
}
.stat-number {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem;
    color: var(--c-orange);
    font-weight: 700;
}
.stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--c-text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ---- History feed ---- */
.history-item {
    background: rgba(10, 8, 30, 0.45);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-left: 3px solid var(--c-blue);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: all 0.2s ease;
    animation: fadeInUp 0.4s ease both;
}
.history-item:hover {
    background: rgba(10, 8, 30, 0.6);
    transform: translateX(4px);
}
.history-item .h-name {
    color: var(--c-orange);
    font-weight: 700;
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
}
.history-item .h-date {
    color: var(--c-text-dim);
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
}

/* ---- Section eyebrow labels for consistent hierarchy ---- */
.section-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #FFFFFF;
    text-shadow: 0 1px 10px rgba(0, 0, 0, 0.4);
    margin: var(--sp-lg) 0 var(--sp-xs) 0;
    opacity: 0.85;
}
</style>
"""

st.markdown(STYLE_CSS.replace("__BG_IMAGE_B64__", bg_image_b64), unsafe_allow_html=True)

components.html("""
<style>
    html, body {
        margin: 0;
        background: transparent;
        overflow: hidden;
    }
    .clock-wrap {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 2px;
        font-family: 'Space Grotesk', sans-serif;
    }
    .flip-digit {
        perspective: 200px;
    }
    .flip-digit .card {
        display: inline-block;
        font-size: 1.25rem;
        font-weight: 700;
        color: #FFFFFF;
        text-shadow: 0 0 10px rgba(199, 210, 254, 0.55), 0 1px 6px rgba(0,0,0,0.5);
        transform-origin: 50% 100%;
        transition: transform 0.2s ease-in;
        will-change: transform;
    }
    .flip-digit:nth-child(3) .card,
    .flip-digit:nth-child(4) .card {
        color: #C7D2FE;
    }
    .colon {
        font-size: 1.1rem;
        font-weight: 700;
        color: #FFA35C;
        text-shadow: 0 0 8px rgba(255, 163, 92, 0.6);
        animation: blink 1.4s steps(1) infinite;
        padding: 0 1px;
    }
    @keyframes blink { 50% { opacity: 0.25; } }
</style>
<div class="clock-wrap" id="clock"></div>
<script>
    function pad(n) { return n.toString().padStart(2, '0'); }

    function getDigits() {
        const now = new Date();
        let h = now.getHours() % 12;
        if (h === 0) h = 12;
        const hh = pad(h);
        const mm = pad(now.getMinutes());
        return [hh[0], hh[1], mm[0], mm[1]];
    }

    function buildClock() {
        const digits = getDigits();
        const el = document.getElementById('clock');
        el.innerHTML =
            '<span class="flip-digit" data-val="' + digits[0] + '"><span class="card">' + digits[0] + '</span></span>' +
            '<span class="flip-digit" data-val="' + digits[1] + '"><span class="card">' + digits[1] + '</span></span>' +
            '<span class="colon">:</span>' +
            '<span class="flip-digit" data-val="' + digits[2] + '"><span class="card">' + digits[2] + '</span></span>' +
            '<span class="flip-digit" data-val="' + digits[3] + '"><span class="card">' + digits[3] + '</span></span>';
    }

    function flipTo(wrapper, newVal) {
        const card = wrapper.querySelector('.card');
        wrapper.dataset.val = newVal;
        card.style.transition = 'transform 0.2s ease-in';
        card.style.transform = 'rotateX(-90deg)';
        const onFlipOut = function () {
            card.removeEventListener('transitionend', onFlipOut);
            card.textContent = newVal;
            card.style.transition = 'none';
            card.style.transform = 'rotateX(90deg)';
            requestAnimationFrame(function () {
                card.style.transition = 'transform 0.2s ease-out';
                card.style.transform = 'rotateX(0deg)';
            });
        };
        card.addEventListener('transitionend', onFlipOut, { once: true });
    }

    function tick() {
        const digits = getDigits();
        const wrappers = document.querySelectorAll('.flip-digit');
        wrappers.forEach(function (w, i) {
            if (w.dataset.val !== digits[i]) {
                flipTo(w, digits[i]);
            }
        });
    }

    buildClock();
    setInterval(tick, 1000);
</script>
""", height=1)

st.markdown('<div class="hero-title"><span class="word-1">Lecture</span> <span class="word-2">Summarizer</span></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Turn any lecture into exam-ready knowledge</div>', unsafe_allow_html=True)



def download_youtube_audio(url, output_path):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path.replace(".wav", ""),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


SOURCE_ICONS = {"pdf": "📄", "txt": "📝", "wav": "🎧", "mp3": "🎧", "youtube": "▶"}


def render_notes(notes):
    """Render the AI's markdown-ish output as styled cards."""
    sections = [s for s in notes.split("##") if s.strip()]
    for i, section in enumerate(sections):
        section = section.strip()
        title, *body = section.split("\n", 1)
        body_text = body[0].strip() if body else ""
        title_clean = title.strip()
        delay = f'style="animation-delay:{i * 0.08:.2f}s"'

        if "exam" in title_clean.lower():
            st.markdown(f'<div class="exam-focus" {delay}><h4>🎯 {title_clean}</h4>{body_text}</div>', unsafe_allow_html=True)
        elif "key" in title_clean.lower():
            points_html = "".join(
                f'<div class="key-point">✦ {line.strip("-• ").strip()}</div>'
                for line in body_text.split("\n") if line.strip()
            )
            st.markdown(f'<div class="tome-card" {delay}><h4>🔑 {title_clean}</h4>{points_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="tome-card" {delay}><h4>📖 {title_clean}</h4><p>{body_text}</p></div>', unsafe_allow_html=True)


# ---------- MAIN NAVIGATION ----------
main_tab1, main_tab2 = st.tabs(["📝 Summarize", "📊 Dashboard"])

with main_tab1:
    tab1, tab2 = st.tabs(["📁 Upload File", "▶ YouTube Link"])

    input_path = None
    source_name = None

    with tab1:
        uploaded_file = st.file_uploader("Drop your notes (.txt, .pdf, .wav, .mp3)", type=["txt", "pdf", "wav", "mp3"])
        if uploaded_file is not None:
            suffix = os.path.splitext(uploaded_file.name)[1]
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_file.write(uploaded_file.read())
            temp_file.close()
            input_path = temp_file.name
            source_name = uploaded_file.name

    with tab2:
        yt_url = st.text_input("Paste a YouTube lecture link", placeholder="https://youtube.com/watch?v=...")
        if yt_url and st.button("Download audio"):
            with st.spinner("Channeling audio from the link..."):
                temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_wav.close()
                try:
                    download_youtube_audio(yt_url, temp_wav.name)
                    st.session_state["input_path"] = temp_wav.name
                    st.session_state["source_name"] = yt_url
                    st.success("Audio ready — click Generate Summary below.")
                except Exception as e:
                    st.error(f"Couldn't pull that video: {e}")

    if "input_path" in st.session_state and input_path is None:
        input_path = st.session_state["input_path"]
        source_name = st.session_state.get("source_name", "youtube_audio")

    st.write("")

    if input_path and st.button("Generate Summary"):
        with st.spinner("Reading your content..."):
            try:
                lecture_text = extract_text(input_path)
            except Exception as e:
                st.error(f"Couldn't process that file: {e}")
                lecture_text = None

        if lecture_text and lecture_text.strip():
            with st.spinner("The AI is thinking..."):
                notes = summarize(lecture_text)

            if notes is None:
                st.error("The AI didn't respond. Check your VS Code terminal for the exact error message.")
            else:
                source_type = os.path.splitext(input_path)[1].replace(".", "") or "youtube"
                save_summary(source_name or "unknown", source_type, notes)

                render_notes(notes)
                st.download_button("⬇ Download as Markdown", data=notes, file_name="lecture_notes.md", mime="text/markdown")
        elif lecture_text is not None:
            st.warning("Couldn't extract any readable text/audio from that input.")

with main_tab2:
    all_summaries = get_all_summaries()

    if not all_summaries:
        st.markdown('<div class="tome-card"><h4>📊 No data yet</h4><p>Summarize a few lectures first — your stats and history will show up here.</p></div>', unsafe_allow_html=True)
    else:
        total_count = len(all_summaries)

        date_counts = get_summary_count_by_date()
        active_days = len(date_counts)

        # Study streak: consecutive days up to today/most recent with at least one summary
        streak = 0
        if date_counts:
            days = sorted({d for d, _ in date_counts})
            day_set = set(days)
            cursor_day = datetime.fromisoformat(days[-1]).date()
            while cursor_day.isoformat() in day_set:
                streak += 1
                cursor_day = cursor_day - timedelta(days=1)

        col1, col2, col3, col4 = st.columns(4, gap="medium")
        with col1:
            st.markdown(f'<div class="stat-card" style="animation-delay:0.0s"><div class="stat-number">{total_count}</div><div class="stat-label">Total Summaries</div></div>', unsafe_allow_html=True)

        type_breakdown = get_source_type_breakdown()
        most_common_type = max(type_breakdown, key=lambda x: x[1])[0] if type_breakdown else "-"
        with col2:
            st.markdown(f'<div class="stat-card" style="animation-delay:0.05s"><div class="stat-number">{most_common_type.upper()}</div><div class="stat-label">Most Used Format</div></div>', unsafe_allow_html=True)

        with col3:
            st.markdown(f'<div class="stat-card" style="animation-delay:0.1s"><div class="stat-number">{active_days}</div><div class="stat-label">Active Days</div></div>', unsafe_allow_html=True)

        with col4:
            st.markdown(f'<div class="stat-card" style="animation-delay:0.15s"><div class="stat-number">🔥{streak}</div><div class="stat-label">Day Streak</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-eyebrow">◆ Activity</div>', unsafe_allow_html=True)

        chart_col1, chart_col2 = st.columns(2, gap="medium")

        # Chart 1: activity over time
        with chart_col1:
            if date_counts:
                df_dates = pd.DataFrame(date_counts, columns=["Date", "Summaries"])
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(
                    x=df_dates["Date"], y=df_dates["Summaries"],
                    mode="lines+markers",
                    line=dict(color="#FF6B5B", width=3),
                    marker=dict(color="#FFA35C", size=8),
                    fill="tozeroy",
                    fillcolor="rgba(255, 107, 91, 0.15)"
                ))
                fig1.update_layout(
                    title="Study Activity Over Time",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#F1F3FA", family="Inter"),
                    title_font=dict(color="#FFA35C", family="Space Grotesk", size=15),
                    xaxis=dict(gridcolor="rgba(138,147,184,0.15)"),
                    yaxis=dict(gridcolor="rgba(138,147,184,0.15)"),
                    height=300,
                    margin=dict(t=50, b=30)
                )
                st.plotly_chart(fig1, width='stretch')

        # Chart 2: source type breakdown
        with chart_col2:
            if type_breakdown:
                df_types = pd.DataFrame(type_breakdown, columns=["Type", "Count"])
                fig2 = go.Figure(data=[go.Pie(
                    labels=df_types["Type"],
                    values=df_types["Count"],
                    hole=0.55,
                    marker=dict(colors=["#4FD1E8", "#FFA35C", "#FF6B5B", "#6C7AE0", "#8A93B8"])
                )])
                fig2.update_layout(
                    title="Content Type Breakdown",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#F1F3FA", family="Inter"),
                    title_font=dict(color="#FFA35C", family="Space Grotesk", size=15),
                    height=300,
                    margin=dict(t=50, b=30)
                )
                st.plotly_chart(fig2, width='stretch')

        # Chart 3: summary length trend (derived on the fly from stored notes — no schema change)
        length_rows = [
            (row[4].split("T")[0] if "T" in row[4] else row[4], len(row[3].split()))
            for row in all_summaries
        ]
        if length_rows:
            df_len = pd.DataFrame(length_rows, columns=["Date", "Words"]).groupby("Date", as_index=False).mean()
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=df_len["Date"], y=df_len["Words"],
                marker=dict(color="#6C7AE0", line=dict(color="#4FD1E8", width=1)),
            ))
            fig3.update_layout(
                title="Average Summary Length (words)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F1F3FA", family="Inter"),
                title_font=dict(color="#FFA35C", family="Space Grotesk", size=15),
                xaxis=dict(gridcolor="rgba(138,147,184,0.15)"),
                yaxis=dict(gridcolor="rgba(138,147,184,0.15)"),
                height=280,
                margin=dict(t=50, b=30)
            )
            st.plotly_chart(fig3, width='stretch')

        # History feed
        st.markdown('<div class="section-eyebrow">◆ Recent Summaries</div>', unsafe_allow_html=True)
        for i, row in enumerate(all_summaries[:10]):
            _, name, stype, notes, created_at = row
            display_date = created_at.split("T")[0] if "T" in created_at else created_at
            icon = SOURCE_ICONS.get(stype.lower(), "📚")
            st.markdown(
                f'<div class="history-item" style="animation-delay:{i * 0.04:.2f}s">'
                f'<span class="h-name">{icon} {name}</span> '
                f'<span class="h-date">· {stype.upper()} · {display_date}</span></div>',
                unsafe_allow_html=True
            )
            with st.expander("View notes"):
                st.markdown(notes)