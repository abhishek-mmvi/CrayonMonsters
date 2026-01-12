"""
CrayonMonsters Battle Engine
Implements turn-based combat following the design spec.
"""
import random
from typing import Dict, List, Tuple, Optional


class Creature:
    """A battle-ready creature with stats and moves."""
    
    def __init__(self, data: dict):
        self.name = data.get('name', 'Unknown')
        self.original_image = data.get('original_image', None)
        
        stats = data.get('stats', {})
        self.max_hp = stats.get('hp', 100)
        self.current_hp = self.max_hp
        self.attack = stats.get('attack', 50)
        self.defense = stats.get('defense', 50)
        self.speed = stats.get('speed', 50)
        self.nature = stats.get('nature', 'normal')
        
        # Temporary stat modifiers (from buffs/debuffs)
        self.attack_mod = 0
        self.defense_mod = 0
        self.speed_mod = 0
        
        self.moves = data.get('moves', [])
        self.skip_next_turn = False
    
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    def get_effective_stat(self, stat_name: str) -> int:
        """Get stat with modifiers applied."""
        base = getattr(self, stat_name, 50)
        mod = getattr(self, f'{stat_name}_mod', 0)
        return max(1, int(base * (1 + mod / 100)))
    
    def take_damage(self, amount: int):
        """Apply damage to this creature."""
        self.current_hp = max(0, self.current_hp - amount)
    
    def heal(self, amount: int):
        """Heal this creature."""
        self.current_hp = min(self.max_hp, self.current_hp + amount)
    
    def apply_stat_change(self, stat: str, percent: int):
        """Apply a stat modifier (positive = buff, negative = debuff)."""
        attr = f'{stat}_mod'
        if hasattr(self, attr):
            current = getattr(self, attr)
            # Cap modifiers at ±50%
            setattr(self, attr, max(-50, min(50, current + percent)))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'nature': self.nature,
            'current_hp': self.current_hp,
            'max_hp': self.max_hp,
            'attack': self.get_effective_stat('attack'),
            'defense': self.get_effective_stat('defense'),
            'speed': self.get_effective_stat('speed'),
            'moves': self.moves,
            'is_alive': self.is_alive(),
            'original_image': self.original_image
        }


class BattleEngine:
    """Manages a battle between two players."""
    
    def __init__(self, player1_id: str, player2_id: str):
        self.player1_id = player1_id
        self.player2_id = player2_id
        
        # Teams: List of Creature objects
        self.teams: Dict[str, List[Creature]] = {
            player1_id: [],
            player2_id: []
        }
        
        # Active creature index for each player
        self.active: Dict[str, int] = {
            player1_id: 0,
            player2_id: 0
        }
        
        # Move selections for current turn
        self.selected_moves: Dict[str, Optional[int]] = {
            player1_id: None,
            player2_id: None
        }
        
        self.turn_number = 0
        self.battle_log: List[str] = []
        self.winner = None
    
    def set_team(self, player_id: str, creatures_data: List[dict]):
        """Set a player's team of creatures."""
        self.teams[player_id] = [Creature(c) for c in creatures_data]
    
    def get_active_creature(self, player_id: str) -> Optional[Creature]:
        """Get a player's currently active creature."""
        team = self.teams.get(player_id, [])
        idx = self.active.get(player_id, 0)
        if idx < len(team):
            return team[idx]
        return None
    
    def select_move(self, player_id: str, move_index: int):
        """Player selects a move (0-3)."""
        creature = self.get_active_creature(player_id)
        if creature and 0 <= move_index < len(creature.moves):
            self.selected_moves[player_id] = move_index
    
    def both_moves_selected(self) -> bool:
        """Check if both players have selected moves."""
        return all(m is not None for m in self.selected_moves.values())
    
    def resolve_turn(self) -> List[dict]:
        """
        Resolve the current turn.
        Returns a list of events that occurred.
        """
        events = []
        self.turn_number += 1
        
        c1 = self.get_active_creature(self.player1_id)
        c2 = self.get_active_creature(self.player2_id)
        
        if not c1 or not c2:
            return events
        
        m1_idx = self.selected_moves[self.player1_id]
        m2_idx = self.selected_moves[self.player2_id]
        
        m1 = c1.moves[m1_idx] if m1_idx is not None else None
        m2 = c2.moves[m2_idx] if m2_idx is not None else None
        
        # Determine turn order
        order = self._determine_order(c1, m1, c2, m2)
        
        for attacker_id, attacker, move, defender_id, defender in order:
            if not attacker.is_alive():
                continue
                
            # Check skip turn
            if attacker.skip_next_turn:
                attacker.skip_next_turn = False
                events.append({
                    'type': 'skip',
                    'player': attacker_id,
                    'creature': attacker.name,
                    'message': f"{attacker.name} is stunned and can't move!"
                })
                continue
            
            # Execute move
            move_events = self._execute_move(attacker_id, attacker, move, defender_id, defender)
            events.extend(move_events)
        
        # Reset move selections
        self.selected_moves = {p: None for p in self.selected_moves}
        
        # Check for knockouts
        ko_events = self._check_knockouts()
        events.extend(ko_events)
        
        return events
    
    def _determine_order(self, c1: Creature, m1: dict, c2: Creature, m2: dict) -> list:
        """Determine who acts first based on priority rules."""
        # Get move categories
        cat1 = m1.get('category', 'active') if m1 else 'active'
        cat2 = m2.get('category', 'active') if m2 else 'active'
        
        # Priority: Active > Passive
        if cat1 == 'active' and cat2 == 'passive':
            first = (self.player1_id, c1, m1, self.player2_id, c2)
            second = (self.player2_id, c2, m2, self.player1_id, c1)
        elif cat1 == 'passive' and cat2 == 'active':
            first = (self.player2_id, c2, m2, self.player1_id, c1)
            second = (self.player1_id, c1, m1, self.player2_id, c2)
        else:
            # Same category: compare speed
            speed1 = c1.get_effective_stat('speed')
            speed2 = c2.get_effective_stat('speed')
            
            if speed1 > speed2:
                first = (self.player1_id, c1, m1, self.player2_id, c2)
                second = (self.player2_id, c2, m2, self.player1_id, c1)
            elif speed2 > speed1:
                first = (self.player2_id, c2, m2, self.player1_id, c1)
                second = (self.player1_id, c1, m1, self.player2_id, c2)
            else:
                # Speed tie: random
                if random.random() < 0.5:
                    first = (self.player1_id, c1, m1, self.player2_id, c2)
                    second = (self.player2_id, c2, m2, self.player1_id, c1)
                else:
                    first = (self.player2_id, c2, m2, self.player1_id, c1)
                    second = (self.player1_id, c1, m1, self.player2_id, c2)
        
        return [first, second]
    
    def _execute_move(self, attacker_id: str, attacker: Creature, move: dict,
                      defender_id: str, defender: Creature) -> List[dict]:
        """Execute a single move."""
        events = []
        
        if not move:
            return events
        
        move_name = move.get('name', 'Unknown Move')
        effect_type = move.get('effect_type', 'damage')
        effect_data = move.get('effect_data', {})
        accuracy = move.get('accuracy', 100)
        
        # Accuracy check
        if random.randint(1, 100) > accuracy:
            events.append({
                'type': 'miss',
                'player': attacker_id,
                'creature': attacker.name,
                'move': move_name,
                'message': f"{attacker.name} used {move_name} but missed!"
            })
            return events
        
        # Execute based on effect type
        if effect_type == 'damage':
            power = effect_data.get('power', 50)
            atk = attacker.get_effective_stat('attack')
            def_ = defender.get_effective_stat('defense')
            
            # Damage formula
            damage = int(atk * (power / 100) * (100 / (100 + def_)))
            damage = max(1, damage)  # Minimum 1 damage
            
            defender.take_damage(damage)
            
            events.append({
                'type': 'damage',
                'player': attacker_id,
                'creature': attacker.name,
                'move': move_name,
                'target': defender.name,
                'damage': damage,
                'message': f"{attacker.name} used {move_name}! {defender.name} took {damage} damage!"
            })
        
        elif effect_type == 'stat_debuff':
            target_stat = effect_data.get('target_stat', 'attack')
            percent = effect_data.get('percent', 10)
            
            defender.apply_stat_change(target_stat, -percent)
            
            events.append({
                'type': 'debuff',
                'player': attacker_id,
                'creature': attacker.name,
                'move': move_name,
                'target': defender.name,
                'stat': target_stat,
                'amount': -percent,
                'message': f"{attacker.name} used {move_name}! {defender.name}'s {target_stat} fell!"
            })
        
        elif effect_type == 'skip_turn':
            chance = effect_data.get('chance', 20)
            
            if random.randint(1, 100) <= chance:
                defender.skip_next_turn = True
                events.append({
                    'type': 'stun',
                    'player': attacker_id,
                    'creature': attacker.name,
                    'move': move_name,
                    'target': defender.name,
                    'message': f"{attacker.name} used {move_name}! {defender.name} is stunned!"
                })
            else:
                events.append({
                    'type': 'stun_fail',
                    'player': attacker_id,
                    'creature': attacker.name,
                    'move': move_name,
                    'message': f"{attacker.name} used {move_name} but it had no effect!"
                })
        
        elif effect_type == 'stat_boost':
            target_stat = effect_data.get('target_stat', 'attack')
            percent = effect_data.get('percent', 10)
            
            attacker.apply_stat_change(target_stat, percent)
            
            events.append({
                'type': 'buff',
                'player': attacker_id,
                'creature': attacker.name,
                'move': move_name,
                'stat': target_stat,
                'amount': percent,
                'message': f"{attacker.name} used {move_name}! Its {target_stat} rose!"
            })
        
        return events
    
    def _check_knockouts(self) -> List[dict]:
        """Check for knockouts and handle switching."""
        events = []
        
        for player_id in [self.player1_id, self.player2_id]:
            creature = self.get_active_creature(player_id)
            if creature and not creature.is_alive():
                events.append({
                    'type': 'knockout',
                    'player': player_id,
                    'creature': creature.name,
                    'message': f"{creature.name} fainted!"
                })
                
                # Check if player has more creatures
                team = self.teams[player_id]
                alive = [c for c in team if c.is_alive()]
                
                if not alive:
                    # Player lost
                    opponent = self.player2_id if player_id == self.player1_id else self.player1_id
                    self.winner = opponent
                    events.append({
                        'type': 'victory',
                        'winner': opponent,
                        'loser': player_id,
                        'message': f"{opponent} wins the battle!"
                    })
        
        return events
    
    def switch_creature(self, player_id: str, creature_index: int) -> bool:
        """Switch to a different creature."""
        team = self.teams.get(player_id, [])
        
        if 0 <= creature_index < len(team):
            creature = team[creature_index]
            if creature.is_alive():
                self.active[player_id] = creature_index
                return True
        return False
    
    def needs_switch(self, player_id: str) -> bool:
        """Check if player needs to switch (active creature fainted)."""
        creature = self.get_active_creature(player_id)
        if creature and not creature.is_alive():
            team = self.teams[player_id]
            return any(c.is_alive() for c in team)
        return False
    
    def get_state(self, for_player: str) -> dict:
        """Get current battle state for a player."""
        opponent = self.player2_id if for_player == self.player1_id else self.player1_id
        
        my_creature = self.get_active_creature(for_player)
        opp_creature = self.get_active_creature(opponent)
        
        return {
            'turn': self.turn_number,
            'my_creature': my_creature.to_dict() if my_creature else None,
            'opponent_creature': opp_creature.to_dict() if opp_creature else None,
            'my_team': [c.to_dict() for c in self.teams.get(for_player, [])],
            'opponent_team_status': [
                {'name': c.name, 'is_alive': c.is_alive()} 
                for c in self.teams.get(opponent, [])
            ],
            'winner': self.winner,
            'needs_switch': self.needs_switch(for_player),
            'waiting_for_opponent': self.selected_moves.get(for_player) is not None 
                                    and self.selected_moves.get(opponent) is None
        }
