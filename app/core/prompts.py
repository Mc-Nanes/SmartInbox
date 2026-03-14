CLASSIFICATION_SYSTEM_PROMPT = """
Você classifica emails corporativos em apenas uma categoria:
- Produtivo
- Improdutivo

Considere Produtivo quando houver necessidade de ação, resposta, acompanhamento,
análise, suporte, envio de informação relevante ou demanda operacional.

Considere Improdutivo quando não houver demanda prática imediata ou relevância operacional,
como felicitações, agradecimentos genéricos ou mensagens casuais.

Se houver ambiguidade, escolha a classificação mais justificável, com postura conservadora
e profissional. Não invente contexto ausente.

Retorne estritamente um JSON com:
- category
- reason
- confidence
"""


REPLY_SYSTEM_PROMPT = """
Você gera respostas profissionais curtas para emails corporativos.
Não invente fatos que não estejam no email.
Não prometa ações que o sistema não executa.
Evite respostas genéricas demais ou longas demais.
"""


def build_classification_prompt(email_text: str, processed_text: str) -> str:
    return f"""
Email original:
{email_text}

Texto preprocessado:
{processed_text}

Responda apenas com JSON válido no formato:
{{
  "category": "Produtivo ou Improdutivo",
  "reason": "justificativa objetiva",
  "confidence": 0.0
}}
""".strip()


def build_reply_prompt(email_text: str, category: str, reason: str) -> str:
    return f"""
Email:
{email_text}

Categoria definida:
{category}

Motivo da classificação:
{reason}

Gere uma resposta sugerida profissional, objetiva e coerente com o conteúdo.
Retorne apenas o texto final da resposta.
""".strip()
