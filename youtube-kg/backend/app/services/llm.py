"""
Unified LLM interface supporting Anthropic and OpenAI.
"""
from app.config import get_settings

settings = get_settings()


def call_llm(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    system: str | None = None,
) -> str:
    model = model or settings.llm_model
    provider = settings.llm_provider

    if provider == "anthropic":
        return _call_anthropic(prompt, model, temperature, max_tokens, system)
    elif provider == "openai":
        return _call_openai(prompt, model, temperature, max_tokens, system)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _call_anthropic(prompt: str, model: str, temperature: float, max_tokens: int, system: str | None) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    if system:
        kwargs["system"] = system
    msg = client.messages.create(**kwargs)
    return msg.content[0].text


def _call_openai(prompt: str, model: str, temperature: float, max_tokens: int, system: str | None) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content
