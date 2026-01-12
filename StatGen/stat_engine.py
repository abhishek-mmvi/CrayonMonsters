"""
Stat Engine for CrayonMonsters
Validates and clamps LLM-generated creature data against stat_rules.json.
THE ENGINE IS ALWAYS FINAL.
"""
import json
import os
from typing import Dict, Any, List, Tuple

# Load rules
RULES_PATH = os.path.join(os.path.dirname(__file__), "stat_rules.json")
with open(RULES_PATH, "r") as f:
    RULES = json.load(f)


def clamp(value: int, min_val: int, max_val: int) -> int:
    """Clamp a value to a range."""
    return max(min_val, min(max_val, value))


def validate_stats(stats: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and fix creature stats.
    Returns (fixed_stats, list_of_warnings).
    """
    warnings = []
    fixed = {}
    
    # Numeric stats
    for stat_name in ["hp", "attack", "defense", "speed"]:
        rule = RULES["stats"][stat_name]
        raw_value = stats.get(stat_name, 50)
        
        if not isinstance(raw_value, int):
            try:
                raw_value = int(raw_value)
            except:
                raw_value = 50
                warnings.append(f"{stat_name} was not a number, defaulting to 50")
        
        fixed[stat_name] = clamp(raw_value, rule["min"], rule["max"])
        
        if fixed[stat_name] != raw_value:
            warnings.append(f"{stat_name} clamped from {raw_value} to {fixed[stat_name]}")
    
    # Nature
    nature = stats.get("nature", "normal").lower()
    if nature not in RULES["stats"]["nature"]:
        warnings.append(f"Invalid nature '{nature}', defaulting to 'normal'")
        nature = "normal"
    fixed["nature"] = nature
    
    return fixed, warnings


def validate_move(move: Dict[str, Any], index: int) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and fix a single move.
    Returns (fixed_move, list_of_warnings).
    """
    warnings = []
    fixed = {}
    
    # Name
    fixed["name"] = move.get("name", f"Move {index + 1}")
    
    # Category
    category = move.get("category", "active").lower()
    if category not in ["active", "passive"]:
        warnings.append(f"Move {index + 1}: Invalid category '{category}', defaulting to 'active'")
        category = "active"
    fixed["category"] = category
    
    # Effect type
    effect_type = move.get("effect_type", "damage").lower()
    category_rules = RULES["moves"]["categories"][category]
    valid_effects = list(category_rules["effects"].keys())
    
    if effect_type not in valid_effects:
        warnings.append(f"Move {index + 1}: Invalid effect '{effect_type}' for {category}, using {valid_effects[0]}")
        effect_type = valid_effects[0]
    fixed["effect_type"] = effect_type
    
    # Effect data
    effect_data = move.get("effect_data", {})
    effect_rules = category_rules["effects"][effect_type]
    fixed_data = {}
    
    if effect_type == "damage":
        power = effect_data.get("power", 50)
        fixed_data["power"] = clamp(int(power), effect_rules["power_range"][0], effect_rules["power_range"][1])
    elif effect_type == "stat_debuff":
        target = effect_data.get("target_stat", "attack")
        if target not in effect_rules["stats"]:
            target = effect_rules["stats"][0]
        fixed_data["target_stat"] = target
        fixed_data["percent"] = clamp(int(effect_data.get("percent", 10)), 
                                       effect_rules["percent_range"][0], 
                                       effect_rules["percent_range"][1])
    elif effect_type == "skip_turn":
        fixed_data["chance"] = clamp(int(effect_data.get("chance", 20)), 
                                      effect_rules["chance_range"][0], 
                                      effect_rules["chance_range"][1])
    elif effect_type == "stat_boost":
        target = effect_data.get("target_stat", "attack")
        if target not in effect_rules["stats"]:
            target = effect_rules["stats"][0]
        fixed_data["target_stat"] = target
        fixed_data["percent"] = clamp(int(effect_data.get("percent", 10)), 
                                       effect_rules["percent_range"][0], 
                                       effect_rules["percent_range"][1])
    
    fixed["effect_data"] = fixed_data
    
    # Accuracy
    accuracy = move.get("accuracy", 100)
    fixed["accuracy"] = clamp(int(accuracy), 1, 100)
    
    # Description
    fixed["description"] = move.get("description", "A mysterious move.")
    
    return fixed, warnings


def validate_creature(creature_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate and fix an entire creature.
    Returns (fixed_creature, list_of_warnings).
    """
    all_warnings = []
    
    # Validate stats
    raw_stats = creature_data.get("stats", {})
    fixed_stats, stat_warnings = validate_stats(raw_stats)
    all_warnings.extend(stat_warnings)
    
    # Validate moves
    raw_moves = creature_data.get("moves", [])
    fixed_moves = []
    active_count = 0
    
    for i, move in enumerate(raw_moves[:4]):  # Max 4 moves
        fixed_move, move_warnings = validate_move(move, i)
        all_warnings.extend(move_warnings)
        fixed_moves.append(fixed_move)
        if fixed_move["category"] == "active":
            active_count += 1
    
    # Pad to 4 moves if needed
    while len(fixed_moves) < 4:
        all_warnings.append(f"Missing move, adding default active move")
        fixed_moves.append({
            "name": f"Basic Attack {len(fixed_moves) + 1}",
            "category": "active",
            "effect_type": "damage",
            "effect_data": {"power": 40},
            "accuracy": 95,
            "description": "A basic attack."
        })
        active_count += 1
    
    # Ensure at least 1 active move
    if active_count == 0:
        all_warnings.append("No active moves found, converting first move to active")
        fixed_moves[0]["category"] = "active"
        fixed_moves[0]["effect_type"] = "damage"
        fixed_moves[0]["effect_data"] = {"power": 50}
    
    return {
        "name": creature_data.get("name", "Unknown Creature"),
        "stats": fixed_stats,
        "moves": fixed_moves
    }, all_warnings


if __name__ == "__main__":
    # Test with sample data
    test_creature = {
        "name": "Flamelord",
        "stats": {"hp": 300, "attack": 150, "defense": 80, "speed": 120, "nature": "fire"},
        "moves": [
            {"name": "Inferno", "category": "active", "effect_type": "damage", "effect_data": {"power": 300}, "accuracy": 90, "description": "Burns everything."},
        ]
    }
    
    fixed, warnings = validate_creature(test_creature)
    print("Fixed Creature:")
    print(json.dumps(fixed, indent=2))
    print("\nWarnings:")
    for w in warnings:
        print(f"  - {w}")
