"""
LLM Client for CrayonMonsters StatGen
Uses Groq API (OpenAI-compatible) with Llama 3.3.
"""
import json
import os
import requests

# Configuration - Using Groq API (OpenAI-compatible)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_ID = "llama-3.3-70b-versatile"  # Groq's fast model

# Load stat rules
RULES_PATH = os.path.join(os.path.dirname(__file__), "stat_rules.json")
with open(RULES_PATH, "r") as f:
    STAT_RULES = json.load(f)


def generate_creature_stats(creature_label: str, confidence: float = 1.0) -> dict:
    """
    Call the LLM to generate creature stats and moves.
    
    Args:
        creature_label: The entity type (e.g., "dragon", "bridge").
        confidence: The AI's confidence in the classification (0.0 - 1.0).
    
    Returns:
        Dictionary containing stats and moves.
    """
    # Build the prompt
    system_prompt = f"""You are a game designer for a Pokémon-like battle game called CrayonMonsters.
Your job is to generate stats and moves for a creature based on its type.

STRICT RULES (You MUST follow these exactly):
1. Stats: hp, attack, defense, speed (integers 0-255), nature (one of: {STAT_RULES['stats']['nature']})
2. Moves: Exactly 4 moves. At least 1 must be "active".
3. Active moves: Can have ONE of these effects: "damage", "stat_debuff", or "skip_turn"
4. Passive moves: Can only boost ONE stat (hp/attack/defense/speed) by a small percentage (1-20%)
5. Move names and descriptions must match the creature's nature/theme.

OUTPUT FORMAT (JSON only, no markdown):
{{
  "name": "Creature Name",
  "stats": {{
    "hp": <int>,
    "attack": <int>,
    "defense": <int>,
    "speed": <int>,
    "nature": "<element>"
  }},
  "moves": [
    {{
      "name": "Move Name",
      "category": "active" or "passive",
      "effect_type": "damage" | "stat_debuff" | "skip_turn" | "stat_boost",
      "effect_data": {{ ... }},
      "accuracy": <int 1-100>,
      "description": "Short flavor text"
    }},
    ... (exactly 4 moves)
  ]
}}

The creature's drawing confidence was {confidence*100:.1f}%. Higher confidence = stronger base stats.
"""

    user_prompt = f"Generate stats and moves for a creature based on: {creature_label}"

    # Make API request to Groq
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    try:
        print(f"[LLM] Calling Groq API for: {creature_label}...")
        response = requests.post(GROQ_BASE_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        print(f"[LLM] Got response for: {creature_label}")
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # Parse JSON from response (handle potential markdown wrapping)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        creature_data = json.loads(content.strip())
        return creature_data
        
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return {"error": str(e)}
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Raw content: {content}")
        return {"error": f"Failed to parse LLM response: {e}"}


if __name__ == "__main__":
    # Test the client
    result = generate_creature_stats("dragon", confidence=0.95)
    print(json.dumps(result, indent=2))
