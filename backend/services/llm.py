from openai import AsyncOpenAI
from config import settings

_GROQ_MODEL = "openai/gpt-oss-20b"
_FEATHERLESS_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"

_client: AsyncOpenAI | None = None


def get_llm_client() -> tuple[AsyncOpenAI, str]:
    global _client
    if settings.groq_api_key:
        if _client is None or getattr(_client, "_base_url_str", "") != "https://api.groq.com/openai/v1":
            _client = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=15.0,
            )
            _client._base_url_str = "https://api.groq.com/openai/v1"
        return _client, _GROQ_MODEL
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.featherless_api_key,
            base_url="https://api.featherless.ai/v1",
            timeout=30.0,
        )
        _client._base_url_str = "https://api.featherless.ai/v1"
    return _client, _FEATHERLESS_MODEL


async def chat_complete(prompt: str, temperature: float = 0.3, max_tokens: int = 1024) -> str:
    client, model = get_llm_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
