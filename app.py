from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from gnani.tts import GnaniTTSClient
from google import genai
import requests
import os
import tempfile

load_dotenv()

app = Flask(__name__)

GNANI_API_KEY = os.getenv("GNANI_API_KEY_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

#Configure the SDK using the existing API key

if GNANI_API_KEY:
    os.environ["GNANI_API_KEY"] = GNANI_API_KEY

tts_client = GnaniTTSClient()

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/ask", methods=["POST"])
def ask():

    if not gemini_client:
        return jsonify({"answer": "Gemini API key is missing."}), 500

    data = request.get_json(silent=True) or {}

    question = data.get("question", "").strip()
    language = data.get("language", "en")

    if not question:
        return jsonify({"answer": "Please enter a question."}), 400

    if language == "ta":
        language_instruction = "Respond in Tamil using Tamil script."
    else:
        language_instruction = "Respond in English."

    prompt = f"""
    You are VoiceBridge, a helpful assistant for government
    schemes and public services in India.

    Instructions:
    - {language_instruction}
    - Use simple language.
    - Give clear and concise answers.
    - Do not invent scheme names, eligibility rules,
      benefits, amounts or deadlines.
    - If information is uncertain, say so.
    - Recommend checking the relevant official
      government website for the latest details.
    - Never make final eligibility decisions.

    User question: {question}
    """

    try:
      try:
        print("Trying Gemini 3.8 Flash...")

        response = gemini_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

      except Exception as primary_error:
        print("Primary model unavailable:", str(primary_error))
        print("Switching to Gemini 3.5 Flash-Lite...")

        response = gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        answer = response.text or "Sorry, I couldn't generate an answer."

        return jsonify({"answer": answer})

    except Exception as e:
        print("GEMINI ERROR:", type(e).__name__, str(e))

        return jsonify({
        "answer": "Our AI service is temporarily busy. Please try again."
    }), 503


@app.route("/transcribe", methods=["POST"])
def transcribe():
    
    print("Transcription function called")

    if "audio" not in request.files:
        return jsonify({"error": "No audio file received"}), 400

    audio = request.files["audio"]

    if not GNANI_API_KEY:
        return jsonify({"error": "API key not configured"}), 500

    url = "https://api.vachana.ai/stt/v3"

    headers = {
    "X-API-Key-ID": GNANI_API_KEY
    }

    files = {
    "audio_file": (
        audio.filename,
        audio.stream,
        audio.content_type
       )
    }

    language = request.form.get("language", "en")
    language_code = "ta-IN" if language == "ta" else "en-IN"

    data = {
    "language_code": language_code,
    "preferred_language": language_code,
    "format": "transcribe",
    "itn_native_numerals": "true"
    }

    try:
        print("Connecting to Gnani STT...")

        response = requests.post(
          url,
          headers=headers,
          files=files,
          data=data,
          timeout=60
       )

        print("Status Code:", response.status_code)
        response.raise_for_status()

        result = response.json()
        print("Gnani STT Response:", result)

        print("Transcription successful!")

        return jsonify({
        "transcript": result.get("transcript", "")
       })

    except Exception as e:

        print("STT ERROR:", type(e).__name__, str(e))

        return jsonify({
         "error": "Gnani transcription failed."
        }), 500


@app.route("/speak", methods=["POST"])
def speak():

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    selected_language = data.get("language", "en")

    if not text:
        return jsonify({"error": "Please enter some text"}), 400

    if not GNANI_API_KEY:
        return jsonify({"error": "API key not configured"}), 500

    audio_path = None

    try:
        print("Connecting to Gnani TTS...")

        fd, audio_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        if selected_language == "ta":
            voice_name = "Asmita"
            language_code = "ta-IN"
        else:
            voice_name = "Shlok"
            language_code = "en-IN"

        tts_client.synthesize(
            text,
            voice=voice_name,
            model="timbre-v2.5",
            language=language_code,
            output_file=audio_path
        )

        print("TTS audio generated successfully!")

        response = send_file(
            audio_path,
            mimetype="audio/wav",
            as_attachment=False
        )

        response.call_on_close(
            lambda: os.path.exists(audio_path) and os.remove(audio_path)
        )

        return response

    except Exception as e:
        print("TTS ERROR:", type(e).__name__, str(e))

        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({
            "error": "Speech generation failed. Check terminal."
        }), 500

if __name__ == "__main__":
    app.run(debug=True)