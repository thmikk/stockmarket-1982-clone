#!/usr/bin/env python3
"""
Test bankruptcy logic
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine import GameEngine


def test_bankruptcy():
    """Test bankruptcy scenario"""
    print("Testing bankruptcy logic...")

    # Create game
    game = GameEngine()
    game.add_player("TestPlayer")

    pdata = game.player_data["TestPlayer"]
    print(f"Initial: Balance=${pdata['balance']}, Loan=${pdata['loan']}")

    # Force large loan that will cause bankruptcy
    pdata["loan"] = 20000  # Much larger than starting balance
    print(f"Forced loan: Balance=${pdata['balance']}, Loan=${pdata['loan']}")

    # Check bankruptcy
    is_bankrupt, msg = game.check_bankruptcy("TestPlayer")
    print(f"Bankruptcy check: {is_bankrupt}, msg='{msg}'")
    print(f"After check: Balance=${pdata['balance']}, Loan=${pdata['loan']}")

    # Test loan interest collection (should trigger bankruptcy)
    game.player_data["TestPlayer"]["loan"] = 15000  # Reset for interest test
    game.player_data["TestPlayer"]["balance"] = 1000
    game.player_data["TestPlayer"]["bankrupt"] = False

    print(f"\nBefore interest: Balance=${pdata['balance']}, Loan=${pdata['loan']}")
    bankruptcy_msgs = game.collect_loan_interest()
    print(f"After interest: Balance=${pdata['balance']}, Loan=${pdata['loan']}")
    print(f"Bankrupt: {pdata.get('bankrupt', False)}")
    print(f"Bankruptcy messages: {bankruptcy_msgs}")

    # Test that bankrupt player cannot trade
    print(f"\nTesting trading while bankrupt...")
    success, msg = game.buy("TestPlayer", "LEAD", 10)
    print(f"Buy attempt: success={success}, msg='{msg}'")

    success, msg = game.sell("TestPlayer", "LEAD", 5)
    print(f"Sell attempt: success={success}, msg='{msg}'")


if __name__ == "__main__":
    test_bankruptcy()
