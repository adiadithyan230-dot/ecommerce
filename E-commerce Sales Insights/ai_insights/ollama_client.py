import requests
from django.conf import settings


PROMPT_TEMPLATE = """You are a professional E-commerce Business Analyst.

Analyze the following KPI data and provide:

1. Executive Summary
2. Key Insights
3. Potential Issues
4. Business Recommendations

Rules:
- Use simple business language.
- Use bullet points.
- Maximum 200 words.
- Focus on actionable recommendations.

KPI DATA:

{KPI_DATA}
"""


class OllamaInsightError(Exception):
    """Raised when Ollama cannot return a usable sales insight."""


def generate_sales_insights(kpi_data):
    prompt = PROMPT_TEMPLATE.format(KPI_DATA=kpi_data)
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        'model': settings.OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False,
    }

    try:
        response = requests.post(url, json=payload, timeout=settings.OLLAMA_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise OllamaInsightError(
            'Ollama is not running. Start it with "ollama serve" and try again.'
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise OllamaInsightError(
            'Ollama took too long to respond. Please try again in a moment.'
        ) from exc
    except requests.exceptions.HTTPError as exc:
        message = _extract_error_message(response)
        if response.status_code == 404 or 'not found' in message.lower():
            raise OllamaInsightError(
                f'Model "{settings.OLLAMA_MODEL}" is not available. Run "ollama pull {settings.OLLAMA_MODEL}".'
            ) from exc
        raise OllamaInsightError(f'Ollama returned an error: {message}') from exc
    except requests.exceptions.RequestException as exc:
        raise OllamaInsightError('Unable to connect to Ollama. Please verify the Ollama service is available.') from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise OllamaInsightError('Ollama returned an invalid response. Please restart Ollama and try again.') from exc

    if data.get('error'):
        error_message = data['error']
        if 'not found' in error_message.lower() or 'pull' in error_message.lower():
            raise OllamaInsightError(
                f'Model "{settings.OLLAMA_MODEL}" is missing. Run "ollama pull {settings.OLLAMA_MODEL}".'
            )
        raise OllamaInsightError(f'Ollama returned an error: {error_message}')

    generated_text = data.get('response', '').strip()
    if not generated_text:
        raise OllamaInsightError('Ollama returned an empty response.')

    return generated_text


def _extract_error_message(response):
    try:
        return response.json().get('error') or response.text
    except ValueError:
        return response.text or 'Unknown Ollama error'
