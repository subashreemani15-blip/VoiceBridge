console.log("voice bridge javascript loaded");
const voiceBtn = document.getElementById("voiceBtn");
const askBtn = document.getElementById("askBtn");
const questionBox = document.getElementById("question");
const language = document.getElementById("language");
const answerBox = document.getElementById("answer");
const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

voiceBtn.addEventListener("click", function () {

    if (!SpeechRecognition) {
        alert("Please use Google Chrome or Microsoft Edge.");
        return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = language.value === "ta" ? "ta-IN" : "en-IN";

    recognition.onstart = function () {
        voiceBtn.textContent = "Listening...";
    };

    recognition.onresult = function (event) {
        questionBox.value = event.results[0][0].transcript;
    };

    recognition.onerror = function (event) {
        alert("Voice recognition error: " + event.error);
    };

    recognition.onend = function () {
        voiceBtn.textContent = "🎤 Speak";
    };

    recognition.start();
});

// Ask VoiceBridge
askBtn.addEventListener("click", async function () {

    const question = questionBox.value.trim();

    if (!question) {
        alert("Please enter your question.");
        return;
    }

    answerBox.textContent = "Processing your question...";

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                language: language.value
            })
        });

        const data = await response.json();

        answerBox.textContent = data.answer;

    } catch (error) {
        answerBox.textContent =
            "Unable to connect. Please try again.";
    }
});
const audioFile = document.getElementById("audioFile");
const transcribeBtn = document.getElementById("transcribeBtn");
const speakBtn = document.getElementById("speakBtn");

transcribeBtn.addEventListener("click", async function () {
    console.log("Transcribe button clicked");

    if (!audioFile.files.length) {
        alert("Please select an audio file.");
        return;
    }

    const formData = new FormData();

    formData.append("audio", audioFile.files[0]);

    const selectedLanguage = language.value;

    // Send the selected language to Flask
    formData.append("language", selectedLanguage);

    answerBox.textContent = "Transcribing your audio...";

    try {
        const response = await fetch("/transcribe", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Transcription failed.");
        }

        questionBox.value = data.transcript;
        answerBox.textContent = "Speech successfully converted into text!";

    } catch (error) {
        answerBox.textContent = error.message;
    }
});
// Gnani Text-to-Speech
speakBtn.addEventListener("click", async function () {

    const text = answerBox.textContent.trim();

    if (!text) {
        alert("Please enter some text first.");
        return;
    }

    speakBtn.textContent = "Generating audio...";

    try {
        const response = await fetch("/speak", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: text ,language: language.value })
        });

        if (!response.ok) {
            throw new Error("Speech generation failed.");
        }

        const audioBlob = await response.blob();
        const audioURL = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioURL);

        audio.onended = function () {
            URL.revokeObjectURL(audioURL);
        };

        audio.play();

    } catch (error) {
        alert(error.message);
    } finally {
        speakBtn.textContent = "🔊 Speak Text";
    }
});