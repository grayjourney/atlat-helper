"""
LLM Module - Language Model Abstraction

Contains:
- base.py: Abstract LLM interface (Protocol)
- mock.py: Mock LLM for testing without API calls

This abstraction allows swapping between:
- OpenAI (GPT-4)
- Ollama (local Llama models)
- Mock (deterministic testing)

Think of it like:
- Go: An interface with multiple implementations
- PHP: A contract with different drivers (like Laravel's Mail)
"""
