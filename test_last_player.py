import unittest
from engine import GameEngine


class TestLastPlayer(unittest.TestCase):
    def setUp(self):
        self.game = GameEngine()
        # Add 3 test players
        self.game.add_player("Player1")
        self.game.add_player("Player2")
        self.game.add_player("Player3")

    def test_last_player_standing(self):
        # Initially no winner
        self.assertIsNone(self.game.check_last_player_standing())

        # Make two players bankrupt
        self.game.player_data["Player1"]["bankrupt"] = True
        self.game.player_data["Player2"]["bankrupt"] = True

        # Now Player3 should be the winner
        self.assertEqual(self.game.check_last_player_standing(), "Player3")

        # Make all players bankrupt
        self.game.player_data["Player3"]["bankrupt"] = True

        # Now no winner
        self.assertIsNone(self.game.check_last_player_standing())

    def test_bankruptcy_integration(self):
        # Set up situation where Player1 will go bankrupt
        self.game.player_data["Player1"]["balance"] = 0
        self.game.player_data["Player1"]["loan"] = 1000

        # Run bankruptcy check
        self.game.check_end_of_turn_bankruptcy()

        # Verify that other players are still in game
        non_bankrupt = [
            p for p in self.game.players if not self.game.player_data[p]["bankrupt"]
        ]
        self.assertEqual(len(non_bankrupt), 2)
        self.assertIn("Player2", non_bankrupt)
        self.assertIn("Player3", non_bankrupt)


if __name__ == "__main__":
    unittest.main()
