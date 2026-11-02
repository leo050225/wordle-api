import os
import random
import uuid
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Wordle API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORD_BANK = ["APPLE", "TRAIN", "HOUSE", "PLANT", "SMART", "WORLD", "LIGHT", "BRAIN", "CLOUD", "WATER"]
games_db: Dict[str, dict] = {}

class GuessRequest(BaseModel):
    game_id: str
    guess: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/new-game")
def start_new_game():
    game_id = str(uuid.uuid4())
    target_word = random.choice(WORD_BANK)
    games_db[game_id] = {
        "target": target_word,
        "status": "PLAYING"
    }
    return {"game_id": game_id, "message": "New game started!"}

@app.post("/api/guess")
def process_guess(req: GuessRequest):
    game_id = req.game_id
    guess = req.guess.upper()

    if game_id not in games_db:
        raise HTTPException(status_code=404, detail="Game session not found.")

    if len(guess) != 5 or not guess.isascii() or not guess.isalpha():
        raise HTTPException(status_code=400, detail="Word must be 5 English letters.")

    target = games_db[game_id]["target"]
    feedback = ["absent"] * 5
    target_letter_counts = {}

    for char in target:
        target_letter_counts[char] = target_letter_counts.get(char, 0) + 1

    for i in range(5):
        if guess[i] == target[i]:
            feedback[i] = "correct"
            target_letter_counts[guess[i]] -= 1

    for i in range(5):
        if feedback[i] != "correct" and guess[i] in target:
            if target_letter_counts[guess[i]] > 0:
                feedback[i] = "present"
                target_letter_counts[guess[i]] -= 1

    is_correct = (guess == target)
    if is_correct:
        games_db[game_id]["status"] = "WON"

    return {
        "guess": guess,
        "feedback": feedback,
        "is_correct": is_correct,
        "target_word": target if is_correct else None
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)