CLASSIFICATION_SYSTEM_PROMPT = """
Voce classifica emails corporativos em apenas uma categoria:
- Produtivo
- Improdutivo

Considere Produtivo quando houver necessidade de acao, resposta, acompanhamento,
analise, suporte, envio de informacao relevante ou demanda operacional.

Considere Improdutivo quando nao houver demanda pratica imediata ou relevancia operacional,
como felicitacoes, agradecimentos genericos ou mensagens casuais.

Se houver ambiguidade, escolha a classificacao mais justificavel, com postura conservadora
e profissional. Nao invente contexto ausente.

Retorne estritamente um JSON com:
- category
- reason
- confidence
"""


REPLY_SYSTEM_PROMPT = """
Voce gera respostas profissionais curtas para emails corporativos.
Nao invente fatos que nao estejam no email.
Nao prometa acoes que o sistema nao executa.
Evite respostas genericas demais ou longas demais.
"""


def build_classification_prompt(email_text: str, processed_text: str) -> str:
    return f"""
Email original:
{email_text}

Texto preprocessado:
{processed_text}

Responda apenas com JSON valido no formato:
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

Motivo da classificacao:
{reason}

Gere uma resposta sugerida profissional, objetiva e coerente com o conteudo.
Retorne apenas o texto final da resposta.
""".strip()
