// Riferimenti agli elementi DOM
const elements = {
    fileInput: document.getElementById("fileInput"),
    uploadForm: document.getElementById("uploadForm"),
    videoPreview: document.getElementById("videoPreview"),
    previewSection: document.getElementById("previewSection"),
    conversionSection: document.getElementById("conversionSection"),
    convertBtn: document.getElementById("convertBtn"),
    formatSelect: document.getElementById("formatSelect"),
    resultSection: document.getElementById("resultSection"),
    downloadLink: document.getElementById("downloadLink"),
    textToSpeechForm: document.getElementById("textToSpeechForm"),
    textInput: document.getElementById("textInput"),
    languageSelect: document.getElementById("languageSelect"),
    audioResultSection: document.getElementById("audioResultSection"),
    audioDownloadLink: document.getElementById("audioDownloadLink"),
    spinner: document.createElement("div"), // Spinner dinamico
};

// Spinner Style
elements.spinner.className = "spinner";
elements.spinner.style.display = "none"; // Nascondi lo spinner inizialmente
document.body.appendChild(elements.spinner); // Aggiungi lo spinner alla pagina

// Mostra/Nascondi Spinner
const toggleSpinner = (show = true) => {
    elements.spinner.style.display = show ? "block" : "none";
};

// Disabilita/Abilita Pulsanti
const toggleButton = (button, disable = true) => {
    if (button) button.disabled = disable;
};

// Gestione anteprima video
elements.fileInput?.addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file && elements.videoPreview && elements.previewSection) {
        elements.videoPreview.src = URL.createObjectURL(file);
        elements.previewSection.style.display = "block";
        alert(`File "${file.name}" ready for upload!`);
    }
});

// Gestione upload file
elements.uploadForm?.addEventListener("submit", function (e) {
    e.preventDefault();
    const file = elements.fileInput.files[0];
    if (!file) {
        alert("Please select a file first!");
        return;
    }

    alert("Starting upload... Please wait.");
    toggleSpinner(true);

    const formData = new FormData();
    formData.append("file", file);

    fetch("/upload", {
        method: "POST",
        body: formData,
    })
    .then((response) => {
        toggleSpinner(false);
        if (!response.ok) {
            throw new Error("Upload failed");
        }
        return response.json();
    })
    .then((data) => {
        if (data.error) {
            throw new Error(data.error);
        }
        localStorage.setItem("uploadedFilePath", data.file_path);
        if (elements.conversionSection) {
            elements.conversionSection.style.display = "block";
        }
        alert(`"${file.name}" uploaded successfully! You can now convert it.`);
    })
    .catch((error) => {
        toggleSpinner(false);
        console.error("Upload error:", error);
        alert("Failed to upload file: " + error.message);
    });
});

// Gestione conversione video
elements.convertBtn?.addEventListener("click", function () {
    const uploadedFilePath = localStorage.getItem("uploadedFilePath");
    const format = elements.formatSelect?.value || "mp4";

    if (!uploadedFilePath) {
        alert("Please upload a file first");
        return;
    }

    alert(`Starting conversion to ${format.toUpperCase()}... Please wait.`);
    toggleSpinner(true);
    toggleButton(elements.convertBtn, true);

    fetch("/convert", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            input_file: uploadedFilePath,
            output_format: format,
        }),
    })
    .then((response) => {
        toggleSpinner(false);
        toggleButton(elements.convertBtn, false);
        if (!response.ok) {
            throw new Error("Conversion failed");
        }
        return response.json();
    })
    .then((data) => {
        if (data.error) {
            throw new Error(data.error);
        }
        if (elements.resultSection) {
            elements.resultSection.style.display = "block";
        }
        if (elements.downloadLink) {
            elements.downloadLink.href = `/download/${data.output_file}`;
            elements.downloadLink.download = data.output_file;
            elements.downloadLink.textContent = "Download Converted File";
        }
        alert(`Conversion to ${format.toUpperCase()} completed! You can now download your file.`);
    })
    .catch((error) => {
        toggleSpinner(false);
        toggleButton(elements.convertBtn, false);
        console.error("Conversion error:", error);
        alert("Failed to convert file: " + error.message);
    });
});

// Gestione generazione audio da testo
elements.textToSpeechForm?.addEventListener("submit", function (event) {
    event.preventDefault();
    const text = elements.textInput?.value || "";
    const language = elements.languageSelect?.value || "en";

    if (!text.trim()) {
        alert("Please enter some text.");
        return;
    }

    alert("Generating audio... Please wait.");
    toggleSpinner(true);
    toggleButton(elements.textToSpeechForm, true);

    fetch("/generate_audio", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            text: text,
            language: language,
        }),
    })
    .then((response) => {
        toggleSpinner(false);
        toggleButton(elements.textToSpeechForm, false);
        if (!response.ok) {
            throw new Error("Audio generation failed");
        }
        return response.json();
    })
    .then((data) => {
        if (data.error) {
            throw new Error(data.error);
        }
        if (elements.audioDownloadLink && elements.audioResultSection) {
            elements.audioDownloadLink.href = `/download/${data.audio_file}`;
            elements.audioDownloadLink.download = data.audio_file;
            elements.audioDownloadLink.textContent = "Download Generated Audio";
            elements.audioResultSection.style.display = "block";
        }
        alert("Audio generated successfully! You can now download it.");
    })
    .catch((error) => {
        toggleSpinner(false);
        toggleButton(elements.textToSpeechForm, false);
        console.error("Audio generation error:", error);
        alert("Failed to generate audio: " + error.message);
    });
});
