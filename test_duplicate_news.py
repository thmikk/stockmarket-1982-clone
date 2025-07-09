#!/usr/bin/env python3
"""
Test script for debugging duplicate market news
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import GameEngine

def test_duplicate_news():
    """Test for duplicate news generation"""
    print("Testing for duplicate market news...")
    
    # Create game engine
    game = GameEngine()
    
    # Add two players
    game.add_player("Player1")
    game.add_player("Player2")
    
    print(f"Initial state: round={game.round}, turn={game.turn}, current_player={game.get_current_player()}")
    
    # Simulate first player's turn
    print("\n=== Player1's turn ===")
    winners1, news1, is_round_end1 = game.end_turn()
    print(f"After Player1: round={game.round}, turn={game.turn}, current_player={game.get_current_player()}")
    print(f"is_round_end={is_round_end1}, news_events={len(news1) if news1 else 0}")
    if news1:
        print("News events:")
        for event in news1:
            print(f"  - {event}")
    
    # Simulate second player's turn
    print("\n=== Player2's turn ===")
    winners2, news2, is_round_end2 = game.end_turn()
    print(f"After Player2: round={game.round}, turn={game.turn}, current_player={game.get_current_player()}")
    print(f"is_round_end={is_round_end2}, news_events={len(news2) if news2 else 0}")
    if news2:
        print("News events:")
        for event in news2:
            print(f"  - {event}")
    
    # Check if both calls generated news (this would be wrong)
    if news1 and news2:
        print("\n❌ ERROR: Both end_turn calls generated news events!")
        return False
    elif is_round_end2 and news2:
        print("\n✅ OK: Only second player (round end) generated news")
        return True
    elif not news1 and not news2:
        print("\n⚠️  WARNING: No news generated at all")
        return False
    else:
        print(f"\n❓ UNEXPECTED: news1={bool(news1)}, news2={bool(news2)}")
        return False

if __name__ == "__main__":
    test_duplicate_news()
