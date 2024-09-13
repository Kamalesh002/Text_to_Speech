import os
import base64
import streamlit as st
from gtts import gTTS
import io
from pydub import AudioSegment
import time
import docx
from PyPDF2 import PdfReader

# File extension handlers
def handle_txt(file):
    return file.read().decode('utf-8')

def handle_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def handle_docx(file):
    doc = docx.Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# File type handlers mapping
file_handlers = {
    "txt": handle_txt,
    "pdf": handle_pdf,
    "docx": handle_docx
}

def cleanup(text):
    import re
    # Removes URLs
    text = re.sub(r'http\S+|www.\S+', ' ', text, flags=re.MULTILINE)
    # Removes LaTeX formulas
    text = re.sub(r'\$\$.*?\$\$', ' ', text, flags=re.MULTILINE)
    text = re.sub(r'\$.+?\$', ' ', text, flags=re.MULTILINE)
    # Removes code snippets
    text = re.sub(r'(```.*?```)', ' ', text, flags=re.DOTALL)
    # Removes special characters from markdown syntax
    text = re.sub(r'(\*\*|\*|__|_|>|\"|~~|``|`|#|\[|\]|\(|\)|!\[|\])', ' ', text)
    return text

def text_to_audio(text, language='en', cleanup_hook=None):
    clean = cleanup_hook or cleanup
    text = clean(text)
    if text.strip():
        tts = gTTS(text=text, lang=language, slow=False)
        mp3_buffer = io.BytesIO()
        tts.write_to_fp(mp3_buffer)

        mp3_buffer.seek(0)

        # Convert MP3 to WAV and make it mono
        audio = AudioSegment.from_file(mp3_buffer, format="mp3").set_channels(1)

        # Extract audio properties
        sample_rate = audio.frame_rate
        sample_width = audio.sample_width

        # Export audio to WAV in memory buffer
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")

        return {
            "bytes": wav_buffer.getvalue(),
            "sample_rate": sample_rate,
            "sample_width": sample_width
        }
    else:
        return None

def auto_play(audio):
    if audio:
        audio_bytes = audio["bytes"]
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        audio_html = f"""
            <audio controls>
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)

st.title("Text to Speech Converter")

# File uploader
uploaded_file = st.file_uploader("Upload a text file (TXT, PDF, DOCX)", type=["txt", "pdf", "docx"])

if uploaded_file:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension in file_handlers:
        text = file_handlers[file_extension](uploaded_file)
        st.text_area("Extracted Text", text)
        
        # Convert text to speech
        if st.button("Convert to Speech"):
            audio = text_to_audio(text)
            if audio:
                auto_play(audio)
            else:
                st.error("Failed to convert text to speech.")
    else:
        st.error("Unsupported file type.")
