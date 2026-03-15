const form = document.getElementById("analysis-form");
const textarea = document.getElementById("email-text");
const fileInput = document.getElementById("email-file");
const fileSummary = document.getElementById("file-summary");
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
const resultConfidenceBadge = document.getElementById("result-confidence-badge");
const resultCategoryBadge = document.getElementById("result-category-badge");
const resultStatusNote = document.getElementById("result-status-note");
const exampleButtons = document.querySelectorAll(".example-button");

const allowedExtensions = [".txt", ".pdf"];
const defaultFileSummary = "Nenhum arquivo selecionado.";
let isLoading = false;

const examples = {
  status: "Olá, poderia nos informar o status da regularização do cadastro do cliente e a previsão de conclusão? Precisamos atualizar a área responsável ainda hoje.",
  support: "Bom dia, estamos com erro ao acessar o sistema interno desde o início da manhã. Podem verificar a falha e orientar o próximo passo?",
  documentation: "Segue em anexo a documentação solicitada para continuidade da análise. Caso precisem de algo adicional, por favor nos sinalizem.",
  gratitude: "Obrigado pelo apoio no fechamento desta demanda. estamos à disposição para futuras colaborações. Tenha um ótimo dia!",
};

function getSelectedFile() {
  return fileInput.files && fileInput.files.length > 0 ? fileInput.files[0] : null;
}

function hasTypedText() {
  return textarea.value.trim().length > 0;
}

function updateCharCount() {
  charCount.textContent = `${textarea.value.length} caracteres`;
}

function formatFileSize(sizeInBytes) {
  if (sizeInBytes < 1024) {
    return `${sizeInBytes} B`;
  }
  if (sizeInBytes < 1024 * 1024) {
    return `${(sizeInBytes / 1024).toFixed(1)} KB`;
  }
  return `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function setStatusNote(label, kind = "idle") {
  resultStatusNote.textContent = label;

  if (kind === "idle") {
    delete resultStatusNote.dataset.kind;
  } else {
    resultStatusNote.dataset.kind = kind;
  }
}

function setViewState({ showEmpty, showLoading, showResult }) {
  emptyState.classList.toggle("hidden", !showEmpty);
  loadingState.classList.toggle("hidden", !showLoading);
  resultCard.classList.toggle("hidden", !showResult);
}

function updateDropzoneState() {
  const hasFile = Boolean(getSelectedFile());
  dropzone.classList.toggle("is-file-selected", hasFile);
}

function updateFileSummary() {
  const file = getSelectedFile();
  if (!file) {
    fileSummary.textContent = defaultFileSummary;
    updateDropzoneState();
    return;
  }
  fileSummary.textContent = `${file.name} - ${formatFileSize(file.size)}`;
  updateDropzoneState();
}

function updateSubmitButtonState() {
  const hasValidInput = hasTypedText() || Boolean(getSelectedFile());
  submitButton.disabled = isLoading || !hasValidInput;
}

function setLoading(nextIsLoading) {
  isLoading = nextIsLoading;
  updateSubmitButtonState();
  clearButton.disabled = isLoading;
  copyButton.disabled = isLoading || !resultReply.textContent.trim();
}

function showFeedback(message, kind = "info", context = "general") {
  feedback.textContent = message;
  feedback.dataset.kind = kind;
  feedback.dataset.context = context;
  feedback.classList.remove("hidden");
}

function hideFeedback() {
  feedback.classList.add("hidden");
  feedback.textContent = "";
  delete feedback.dataset.kind;
  delete feedback.dataset.context;
}

function hasFeedbackContext(context) {
  return !feedback.classList.contains("hidden") && feedback.dataset.context === context;
}

function applyCategoryVisual(category) {
  resultCategoryBadge.textContent = category;
  resultCategoryBadge.dataset.category = category === "Produtivo" ? "productive" : "unproductive";
}

function resetResult() {
  setViewState({ showEmpty: true, showLoading: false, showResult: false });
  resultCategory.textContent = "";
  resultReason.textContent = "";
  resultReply.textContent = "";
  resultCategoryBadge.textContent = "Categoria";
  delete resultCategoryBadge.dataset.category;
  resultConfidenceBadge.textContent = "Confiança: Não informado";
  copyButton.disabled = true;
  setStatusNote("Aguardando entrada", "idle");
}

function renderResult(data) {
  setViewState({ showEmpty: false, showLoading: false, showResult: true });
  resultCategory.textContent = data.category;
  resultReason.textContent = data.reason;
  resultReply.textContent = data.suggested_reply;
  applyCategoryVisual(data.category);

  const confidenceLabel = typeof data.confidence === "number"
    ? `${Math.round(data.confidence * 100)}%`
    : "Não informado";

  resultConfidenceBadge.textContent = `Confiança: ${confidenceLabel}`;
  copyButton.disabled = false;
  setStatusNote("Concluído", "success");
}

function isAllowedFile(file) {
  const lowerName = file.name.toLowerCase();
  return allowedExtensions.some((extension) => lowerName.endsWith(extension));
}

function validateForm() {
  const file = getSelectedFile();

  if (file && !isAllowedFile(file)) {
    showFeedback("Formato inválido. Envie apenas arquivos .txt ou .pdf.", "error", "validation");
    setStatusNote("Erro", "error");
    return false;
  }

  return true;
}

function setSelectedFile(file) {
  if (!file) {
    fileInput.value = "";
    updateFileSummary();
    return;
  }

  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  fileInput.files = dataTransfer.files;
  updateFileSummary();
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return { detail: text };
}

function syncCombinedContentHint() {
  if (getSelectedFile() && hasTypedText()) {
    showFeedback("Texto e arquivo presentes. Se enviar ambos, os dois conteúdos serão analisados em conjunto.", "info", "combined-input");
    return;
  }

  if (hasFeedbackContext("combined-input")) {
    hideFeedback();
  }
}

async function handleSubmit(event) {
  event.preventDefault();

  if (!validateForm()) {
    return;
  }

  const file = getSelectedFile();
  const textProvided = hasTypedText();

  if (file && textProvided) {
    showFeedback("Texto e arquivo presentes. Se enviar ambos, os dois conteúdos serão analisados em conjunto.", "info", "combined-input");
  } else {
    hideFeedback();
  }

  setViewState({ showEmpty: false, showLoading: true, showResult: false });
  setStatusNote("Processando", "loading");
  setLoading(true);

  const formData = new FormData();
  if (textProvided) {
    formData.append("text", textarea.value.trim());
  }

  if (file) {
    formData.append("file", file);
  }

  try {
    const response = await fetch("/api/v1/analyze", {
      method: "POST",
      body: formData,
    });

    const data = await parseResponse(response);
    if (!response.ok) {
      throw new Error(data.detail || "Não foi possível concluir a análise.");
    }

    renderResult(data);
    showFeedback("Análise concluída com sucesso.", "success", "submit");
  } catch (error) {
    resetResult();
    setStatusNote("Erro", "error");
    showFeedback(error.message || "Erro inesperado ao analisar o email.", "error", "submit");
  } finally {
    setLoading(false);
  }
}

function handleClear() {
  form.reset();
  textarea.value = "";
  fileInput.value = "";
  updateCharCount();
  updateFileSummary();
  updateSubmitButtonState();
  hideFeedback();
  resetResult();
}

async function handleCopyReply() {
  const reply = resultReply.textContent.trim();
  if (!reply) {
    showFeedback("Não há resposta sugerida disponível para copiar.", "error", "copy");
    return;
  }

  try {
    await navigator.clipboard.writeText(reply);
    showFeedback("Resposta sugerida copiada com sucesso.", "success", "copy");
  } catch (_) {
    showFeedback("Não foi possível copiar a resposta.", "error", "copy");
  }
}

function handleFileSelection(file) {
  if (!file) {
    updateFileSummary();
    updateSubmitButtonState();
    syncCombinedContentHint();
    return;
  }

  if (!isAllowedFile(file)) {
    setSelectedFile(null);
    updateSubmitButtonState();
    showFeedback("Formato inválido. Envie apenas arquivos .txt ou .pdf.", "error", "validation");
    setStatusNote("Erro", "error");
    return;
  }

  setSelectedFile(file);
  updateSubmitButtonState();
  if (!hasTypedText()) {
    showFeedback(`Arquivo "${file.name}" pronto para envio.`, "info", "file");
  }
  syncCombinedContentHint();
}

function handleDrop(event) {
  event.preventDefault();
  dropzone.classList.remove("is-drag-over");

  const droppedFile = event.dataTransfer.files[0];
  handleFileSelection(droppedFile);
  updateSubmitButtonState();
}

function handleDragOver(event) {
  event.preventDefault();
  dropzone.classList.add("is-drag-over");
}

function handleDragLeave() {
  dropzone.classList.remove("is-drag-over");
  updateDropzoneState();
}

function handleExampleClick(event) {
  const exampleKey = event.currentTarget.dataset.example;
  const exampleText = examples[exampleKey];
  const exampleLabel = event.currentTarget.textContent.trim();
  if (!exampleText) {
    return;
  }

  const hadSelectedFile = Boolean(getSelectedFile());
  if (hadSelectedFile) {
    setSelectedFile(null);
  }

  textarea.value = exampleText;
  updateCharCount();
  updateFileSummary();
  updateSubmitButtonState();
  syncCombinedContentHint();
  textarea.focus();

  if (hadSelectedFile) {
    showFeedback(`Exemplo "${exampleLabel}" preenchido. O arquivo selecionado foi removido para usar apenas o texto de teste.`, "info", "example");
    return;
  }

  showFeedback(`Exemplo "${exampleLabel}" preenchido. Você pode editar o texto antes de enviar.`, "info", "example");
}

textarea.addEventListener("input", () => {
  updateCharCount();
  updateFileSummary();
  updateSubmitButtonState();
  syncCombinedContentHint();
});

fileInput.addEventListener("change", () => {
  handleFileSelection(getSelectedFile());
  updateSubmitButtonState();
});

exampleButtons.forEach((button) => {
  button.addEventListener("click", handleExampleClick);
});

form.addEventListener("submit", handleSubmit);
clearButton.addEventListener("click", handleClear);
copyButton.addEventListener("click", handleCopyReply);
dropzone.addEventListener("dragover", handleDragOver);
dropzone.addEventListener("dragleave", handleDragLeave);
dropzone.addEventListener("drop", handleDrop);

updateCharCount();
updateFileSummary();
resetResult();
updateSubmitButtonState();
