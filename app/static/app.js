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
const feedbackBaseClass = "mt-6 rounded-2xl border px-4 py-4 text-sm leading-6";

const examples = {
  status: "Olá, poderia nos informar o status da regularização do cadastro do cliente e a previsão de conclusão? Precisamos atualizar a área responsável ainda hoje.",
  support: "Bom dia, estamos com erro ao acessar o sistema interno desde o início da manhã. Podem verificar a falha e orientar o próximo passo?",
  documentation: "Segue em anexo a documentação solicitada para continuidade da análise. Caso precisem de algo adicional, por favor nos sinalizem.",
  gratitude: "Obrigado pelo apoio no fechamento desta demanda. A equipe ficou satisfeita com o suporte prestado."
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
  resultStatusNote.className = "rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em]";

  if (kind === "success") {
    resultStatusNote.classList.add("border-emerald-400/30", "bg-emerald-400/10", "text-emerald-100");
    return;
  }

  if (kind === "error") {
    resultStatusNote.classList.add("border-rose-400/30", "bg-rose-400/10", "text-rose-100");
    return;
  }

  if (kind === "loading") {
    resultStatusNote.classList.add("border-cyan-400/30", "bg-cyan-400/10", "text-cyan-100");
    return;
  }

  resultStatusNote.classList.add("border-white/10", "bg-white/5", "text-slate-300");
}

function setViewState({ showEmpty, showLoading, showResult }) {
  emptyState.classList.toggle("hidden", !showEmpty);
  loadingState.classList.toggle("hidden", !showLoading);
  resultCard.classList.toggle("hidden", !showResult);
}

function updateDropzoneState() {
  const hasFile = Boolean(getSelectedFile());
  dropzone.classList.remove("border-cyan-400/50", "bg-cyan-400/5", "border-emerald-400/30", "bg-emerald-400/5");

  if (hasFile) {
    dropzone.classList.add("border-emerald-400/30", "bg-emerald-400/5");
  }
}

function updateFileSummary() {
  const file = getSelectedFile();
  if (!file) {
    fileSummary.textContent = defaultFileSummary;
    updateDropzoneState();
    return;
  }

  const priorityNote = hasTypedText() ? " - prioridade do arquivo ativa" : "";
  fileSummary.textContent = `${file.name} - ${formatFileSize(file.size)}${priorityNote}`;
  updateDropzoneState();
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  clearButton.disabled = isLoading;
  copyButton.disabled = isLoading || !resultReply.textContent.trim();
}

function showFeedback(message, kind = "info", context = "general") {
  feedback.textContent = message;
  feedback.className = feedbackBaseClass;
  feedback.dataset.kind = kind;
  feedback.dataset.context = context;

  if (kind === "error") {
    feedback.classList.add("border-rose-400/30", "bg-rose-400/10", "text-rose-100");
  } else if (kind === "success") {
    feedback.classList.add("border-emerald-400/30", "bg-emerald-400/10", "text-emerald-100");
  } else {
    feedback.classList.add("border-cyan-400/30", "bg-cyan-400/10", "text-cyan-100");
  }

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
  resultCategoryBadge.className = "rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em]";

  if (category === "Produtivo") {
    resultCategoryBadge.classList.add("border-emerald-400/30", "bg-emerald-400/10", "text-emerald-100");
    return;
  }

  resultCategoryBadge.classList.add("border-amber-400/30", "bg-amber-400/10", "text-amber-100");
}

function resetResult() {
  setViewState({ showEmpty: true, showLoading: false, showResult: false });
  resultCategory.textContent = "";
  resultReason.textContent = "";
  resultReply.textContent = "";
  resultCategoryBadge.textContent = "Categoria";
  resultCategoryBadge.className = "rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-slate-200";
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

  if (!hasTypedText() && !file) {
    showFeedback("Informe o texto do email ou envie um arquivo antes de analisar.", "error", "validation");
    setStatusNote("Erro", "error");
    return false;
  }

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

function syncPriorityHint() {
  if (getSelectedFile() && hasTypedText()) {
    showFeedback("Texto e arquivo presentes. Se enviar ambos, o arquivo terá prioridade na análise.", "info", "priority");
    return;
  }

  if (hasFeedbackContext("priority")) {
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
    showFeedback("Texto e arquivo enviados juntos. O arquivo terá prioridade na análise.", "info", "priority");
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

    if (file && textProvided) {
      showFeedback("Análise concluída com sucesso. O arquivo enviado foi usado como prioridade.", "success", "submit");
    } else {
      showFeedback("Análise concluída com sucesso.", "success", "submit");
    }
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
    syncPriorityHint();
    return;
  }

  if (!isAllowedFile(file)) {
    setSelectedFile(null);
    showFeedback("Formato inválido. Envie apenas arquivos .txt ou .pdf.", "error", "validation");
    setStatusNote("Erro", "error");
    return;
  }

  setSelectedFile(file);
  if (!hasTypedText()) {
    showFeedback(`Arquivo "${file.name}" pronto para envio.`, "info", "file");
  }
  syncPriorityHint();
}

function handleDrop(event) {
  event.preventDefault();
  dropzone.classList.remove("border-cyan-400/50", "bg-cyan-400/5");

  const droppedFile = event.dataTransfer.files[0];
  handleFileSelection(droppedFile);
}

function handleDragOver(event) {
  event.preventDefault();
  dropzone.classList.add("border-cyan-400/50", "bg-cyan-400/5");
}

function handleDragLeave() {
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
  syncPriorityHint();
  textarea.focus();

  if (hadSelectedFile) {
    showFeedback(`Exemplo "${exampleLabel}" preenchido. O arquivo selecionado foi removido para priorizar o texto de teste.`, "info", "example");
    return;
  }

  showFeedback(`Exemplo "${exampleLabel}" preenchido. Você pode editar o texto antes de enviar.`, "info", "example");
}

textarea.addEventListener("input", () => {
  updateCharCount();
  updateFileSummary();
  syncPriorityHint();
});

fileInput.addEventListener("change", () => {
  handleFileSelection(getSelectedFile());
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
