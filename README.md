# ♟️ Local AI Chess Puzzle Generator

A fully local, AI-powered chess puzzle trainer built with Python.  
This app detects tactical motifs such as **pins, forks, skewers, and back-rank mates**, and uses a local LLM via **Ollama** to generate hints and explanations.

---

## 🚀 Features

- ♟️ Classic tactical puzzles:
  - Pin  
  - Fork  
  - Skewer  
  - Back-rank mate  

- 🖱️ Interactive click-to-move chessboard (no typing required)  
- 🔁 Puzzle controls:
  - New Puzzle  
  - Retry Puzzle  
  - Get Hint  
  - Show Solution  

- 🧠 Local AI-powered:
  - Context-aware hints  
  - Step-by-step explanations  

- 🔒 Fully offline after setup  

---

## 🧰 Prerequisites

Make sure you have the following installed:

### 1. Python
- Python **3.10 or higher**

### 2. Ollama (for local AI)
- Download: https://ollama.com/download  
- Ensure it is **installed and running**

### 3. Recommended Model
ollama pull mistral


🎮 Controls
-----------

*   **Click a piece → Click destination square** to move
    
*   **New Puzzle** → Load a new random puzzle
    
*   **Retry Puzzle** → Restart current puzzle
    
*   **Get Hint** → AI-generated subtle hint
    
*   **Show Solution** → Full solution with explanation
