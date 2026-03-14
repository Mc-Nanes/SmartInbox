const form = document.getElementById("analysis-form");
const textarea = document.getElementById("email-text");
const fileInput = document.getElementById("email-file");
const dropzone = document.getElementById("dropzone");
const submitButton = document.getElementById("submit-button");
const clearButton = document.getElementById("clear-button");
const copyButton = document.getElementById("copy-button");
const charCount = document.getElementById("char-count");
const feedback = document.getElementById("feedback");
const emptyState = document.getElementById("empty-state");
const loadingState = document.getElementById("loading-state");
const resultCard = document.getElementById("result-card");
const resultCategory = document.getElementById("result-category");
const resultReason = document.getElementById("result-reason");
const resultReply = document.getElementById("result-reply");
const resultConfidence = document.getElementById("result-confidence");

const allowedExtensions = [".txt", ".pdf"];

function updateCharCount() {
  charCount.textContent = `${textarea.value.length} caracteres`;
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  loadingState.classList.toggle("hidden", !isLoading);
}

function showFeedback(message, kind) {
  feedback.textContent = message;
  feedback.className = "mt-6 rounded-2xl border px-4 py-3 text-sm";

  if (kind === "error") {
    feedback.classList.add("border-rose-400/30", "bg-rose-400/10", "text-rose-100");
  } else {
    feedback.classList.add("border-emerald-400/30", "bg-emerald-400/10", "text-emerald-100");
  }

  feedback.classList.remove("hidden");
}

function hideFeedback() {
  feedback.classList.add("hidden");
}

function resetResult() {
  emptyState.classList.remove("hidden");
  resultCard.classList.add("hidden");
  resultCategory.textContent = "";
  resultReason.textContent = "";
  resultReply.textContent = "";
  resultConfidence.textContent = "Não informado";
}

function validateForm() {
  const hasText = textarea.value.trim().length > 0;
  const file = fileInput.files[0];

  if (!hasText && !file) {
    showFeedback("Informe o texto do email ou envie um arquivo antes de analisar.", "error");
    return false;
  }

  if (file) {
    const lowerName = file.name.toLowerCase();
    const isAllowed = allowedExtensions.some((extension) => lowerName.endsWith(extension));
    if (!isAllowed) {
      showFeedback("Formato inválido. Envie apenas arquivos .txt ou .pdf.", "error");
      return false;
    }
  }

  hideFeedback();
  return true;
}

async function handleSubmit(event) {
  event.preventDefault();

  if (!validateForm()) {
    return;
  }

  setLoading(true);
  emptyState.classList.add("hidden");
  resultCard.classList.add("hidden");
  hideFeedback();

  const formData = new FormData();
  if (textarea.value.trim()) {
    formData.append("text", textarea.value.trim());
  }

  if (fileInput.files[0]) {
    formData.append("file", fileInput.files[0]);
  }

  try {
    const response = await fetch("/api/v1/analyze", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Não foi possível concluir a análise.");
    }

    resultCategory.textContent = data.category;
    resultReason.textContent = data.reason;
    resultReply.textContent = data.suggested_reply;
    resultConfidence.textContent = typeof data.confidence === "number"
      ? `${Math.round(data.confidence * 100)}%`
      : "Não informado";

    resultCard.classList.remove("hidden");
  } catch (error) {
    resetResult();
    showFeedback(error.message || "Erro inesperado ao analisar o email.", "error");
  } finally {
    setLoading(false);
  }
}

function handleClear() {
  form.reset();
  textarea.value = "";
  updateCharCount();
  hideFeedback();
  resetResult();
}

async function handleCopyReply() {
  const reply = resultReply.textContent.trim();
  if (!reply) {
    return;
  }

  try {
    await navigator.clipboard.writeText(reply);
    showFeedback("Resposta sugerida copiada com sucesso.", "success");
  } catch (_) {
    showFeedback("Não foi possível copiar a resposta.", "error");
  }
}

function handleDrop(event) {
  event.preventDefault();
  dropzone.classList.remove("border-cyan-400");

  const droppedFile = event.dataTransfer.files[0];
  if (droppedFile) {
    fileInput.files = event.dataTransfer.files;
  }
}

textarea.addEventListener("input", updateCharCount);
form.addEventListener("submit", handleSubmit);
clearButton.addEventListener("click", handleClear);
copyButton.addEventListener("click", handleCopyReply);

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("border-cyan-400");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("border-cyan-400");
});

dropzone.addEventListener("drop", handleDrop);

updateCharCount();
resetResult();
