# main.py
from ui import ChessUI
from storage import init_if_empty

if __name__ == "__main__":
    print("🚀 Starting Local AI Chess Puzzle Generator...")
    print("Make sure Ollama is installed and 'llama3.2:3b' model is pulled.")
    init_if_empty()
    app = ChessUI()
    app.mainloop()