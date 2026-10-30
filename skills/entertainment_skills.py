"""
skills/entertainment_skills.py

Module 11: Entertainment and Media
Implements movie/music/podcast recommendations, ebook/text reading aloud,
and interactive voice games (trivia, riddles, word puzzles).
Auto-registered via engine.py.
"""

import os
import random


def recommend_entertainment(category: str = "movie", mood_or_genre: str = "sci-fi") -> str:
    """Provides curated recommendations for movies, music albums, or podcasts based on category and mood/genre."""
    cat = category.lower().strip()
    g = mood_or_genre.lower().strip()

    recs = {
        "movie": {
            "sci-fi": ["Interstellar (2014)", "Inception (2010)", "Blade Runner 2049 (2017)", "The Matrix (1999)"],
            "action": ["Top Gun: Maverick (2022)", "John Wick (2014)", "The Dark Knight (2008)", "Mad Max: Fury Road (2015)"],
            "comedy": ["The Grand Budapest Hotel (2014)", "Superbad (2007)", "3 Idiots (2009)", "Knives Out (2019)"],
            "thriller": ["Shutter Island (2010)", "Gone Girl (2014)", "Se7en (1995)", "Drishyam (2015)"],
        },
        "podcast": {
            "tech": ["Lex Fridman Podcast", "Huberman Lab", "The Changelog", "Hard Fork by NYT"],
            "science": ["Radiolab", "StarTalk Radio with Neil deGrasse Tyson", "Ologies with Alie Ward"],
            "productivity": ["The Tim Ferriss Show", "Deep Questions with Cal Newport", "Atomic Habits podcast"],
        },
        "music": {
            "lofi": ["Lofi Girl - Chill Beats to Study to", "Komorebi by Kupla", "Coffee Shop Ambient Jazz"],
            "focus": ["Brian Eno - Music for Airports", "Max Richter - Sleep", "Hans Zimmer - Interstellar OST"],
            "bollywood": ["Arijit Singh Soulful Hits", "A.R. Rahman Timeless Classics", "Pritam Melodies Collection"]
        }
    }

    target_dict = recs.get(cat, recs["movie"])
    items = None
    for k in target_dict:
        if k in g:
            items = target_dict[k]
            break
    if not items:
        # Pick default
        key = list(target_dict.keys())[0]
        items = target_dict[key]

    picks = ", ".join(items[:3])
    return f"Here are 3 top {cat} recommendations for '{mood_or_genre}': {picks}."


def read_ebook_or_text_aloud(file_path: str, max_paragraphs: str = "3") -> str:
    """Reads aloud a portion of an ebook or text document. max_paragraphs: number of paragraphs to read."""
    target = file_path.strip()
    profile = os.environ.get("USERPROFILE", "")
    for key, fld in {"desktop": "Desktop", "downloads": "Downloads", "documents": "Documents"}.items():
        if target.lower().startswith(key):
            target = os.path.join(profile, fld, target[len(key):].lstrip("\\/"))
            break

    if not os.path.exists(target):
        return f"File not found: '{file_path}'."

    n = int(''.join(filter(str.isdigit, max_paragraphs)) or '3')
    try:
        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            lines = [ln.strip() for ln in f.readlines() if ln.strip()]
        if not lines:
            return f"Document '{os.path.basename(target)}' is empty."
        excerpt = " ".join(lines[:n])
        return f"Reading from '{os.path.basename(target)}':\n{excerpt}"
    except Exception as e:
        return f"Error reading document aloud: {e}"


def play_voice_game(game_name: str = "trivia") -> str:
    """Starts an interactive quick voice game: 'trivia', 'riddle', or 'fun_fact'."""
    g = game_name.lower().strip()
    if "riddle" in g:
        riddles = [
            ("I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "An echo!"),
            ("What has keys, but no locks; space, but no room; and you can enter, but can't go outside?", "A computer keyboard!"),
            ("The more of this there is, the less you see. What is it?", "Darkness!"),
            ("What has a head and a tail that will never meet?", "A coin!"),
        ]
        q, a = random.choice(riddles)
        return f"Here is your riddle: {q} ... (Think about it! Say 'reveal riddle answer' when you are ready: {a})"
    else: # trivia
        trivia_questions = [
            "Tech Trivia: Who is considered the world's first computer programmer? Answer: Ada Lovelace in 1843!",
            "AI Trivia: In what year was the term 'Artificial Intelligence' coined at the Dartmouth workshop? Answer: 1956!",
            "Space Trivia: Which planet in our solar system has the most moons? Answer: Saturn, with 146 discovered moons!",
            "Physics Trivia: What is the only letter not found on the periodic table of elements? Answer: The letter J!"
        ]
        return random.choice(trivia_questions)
