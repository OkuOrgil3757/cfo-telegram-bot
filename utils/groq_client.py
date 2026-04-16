from groq import Groq
import os

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


def ask(system_prompt: str, user_message: str, context: str = "") -> str:
    client = get_client()
    full_user = f"{context}\n\n{user_message}" if context else user_message
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user},
        ],
        max_tokens=1024,
        temperature=0.3,
    )
    return response.choices[0].message.content


def ask_with_history(system_prompt: str, history: list[dict]) -> str:
    """Multi-turn chat with full message history. history is list of {role, content} dicts."""
    client = get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}] + history,
        max_tokens=1024,
        temperature=0.3,
    )
    return response.choices[0].message.content
