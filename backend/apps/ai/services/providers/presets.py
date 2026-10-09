from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    kind: str  # "anthropic" or "openai" (any OpenAI compatible endpoint)
    base_url: str = ""
    needs_key: bool = True


PRESETS = {
    "anthropic": Preset("anthropic"),
    "gemini": Preset("openai", "https://generativelanguage.googleapis.com/v1beta/openai/"),
    "groq": Preset("openai", "https://api.groq.com/openai/v1"),
    "openrouter": Preset("openai", "https://openrouter.ai/api/v1"),
    "mistral": Preset("openai", "https://api.mistral.ai/v1"),
    # Reached from the Docker containers through host.docker.internal (see docker-compose.yml).
    "ollama": Preset("openai", "http://host.docker.internal:11434/v1", needs_key=False),
    "openai_compatible": Preset("openai", "", needs_key=False),
}
