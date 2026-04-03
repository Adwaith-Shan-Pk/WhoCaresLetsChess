# ai_helper.py
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def query_ollama(prompt: str) -> str:
    """Reliable way to talk to Ollama (uses HTTP instead of subprocess)."""
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "No response received.")
        else:
            return f"Ollama returned error {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to Ollama.\n\nMake sure Ollama is running (check the tray icon)."
    except Exception as e:
        return f"Error: {str(e)}"

def give_hint(fen: str, motif: str) -> str:
    prompt = f"""You are a friendly chess coach for beginners.
FEN: {fen}
Motif: {motif}

Give one short, subtle hint (1-2 sentences max). Do not give the exact move."""
    return query_ollama(prompt)

def explain_solution(fen: str, solution: str, motif: str) -> str:
    prompt = f"""You are a patient chess tutor.
FEN: {fen}
Solution: {solution}
Motif: {motif}

Explain step-by-step why this is a good move. Keep it simple and encouraging for a beginner."""
    return query_ollama(prompt)