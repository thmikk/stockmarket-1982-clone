# Tester for motoren
import unittest
from engine import GameEngine


class TestGameEngine(unittest.TestCase):

    def setUp(self):
        """Sett opp test-miljø"""
        self.engine = GameEngine()
        self.engine.add_player("test_player", 10000)

    def test_add_player(self):
        """Test at spillere kan legges til"""
        self.engine.add_player("player1", 5000)
        self.assertIn("player1", self.engine.players)
        self.assertEqual(self.engine.players["player1"]["balance"], 5000)

    def test_get_stock_data(self):
        """Test at aksjedata kan hentes"""
        stock_data = self.engine.get_stock_data("AAPL")
        self.assertIsNotNone(stock_data)
        if stock_data:
            self.assertEqual(stock_data["symbol"], "AAPL")
            self.assertIn("price", stock_data)

    def test_buy_stock_success(self):
        """Test vellykket aksjekjøp"""
        result = self.engine.buy_stock("test_player", "AAPL", 10)
        self.assertTrue(result["success"])
        self.assertIn("AAPL", self.engine.players["test_player"]["portfolio"])
        self.assertEqual(self.engine.players["test_player"]["portfolio"]["AAPL"], 10)

    def test_buy_stock_insufficient_funds(self):
        """Test aksjekjøp med utilstrekkelige midler"""
        result = self.engine.buy_stock("test_player", "GOOGL", 100)  # For dyrt
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Insufficient funds")

    def test_sell_stock_success(self):
        """Test vellykket aksjesalg"""
        # Først kjøp aksjer
        self.engine.buy_stock("test_player", "AAPL", 10)
        # Så selg dem
        result = self.engine.sell_stock("test_player", "AAPL", 5)
        self.assertTrue(result["success"])
        self.assertEqual(self.engine.players["test_player"]["portfolio"]["AAPL"], 5)

    def test_sell_stock_insufficient_shares(self):
        """Test aksjesalg med utilstrekkelige aksjer"""
        result = self.engine.sell_stock("test_player", "AAPL", 10)
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Insufficient shares")

    def test_get_player_portfolio(self):
        """Test henting av spillerportefølje"""
        self.engine.buy_stock("test_player", "AAPL", 5)
        portfolio = self.engine.get_player_portfolio("test_player")

        self.assertIn("balance", portfolio)
        self.assertIn("portfolio", portfolio)
        self.assertIn("portfolio_value", portfolio)
        self.assertIn("total_value", portfolio)

    def test_update_stock_prices(self):
        """Test at aksjepriser oppdateres"""
        original_price = self.engine.stocks["AAPL"]["price"]
        self.engine.update_stock_prices()
        new_price = self.engine.stocks["AAPL"]["price"]

        # Prisen kan være den samme, men vi sjekker at funksjonen kjører
        self.assertIsInstance(new_price, float)

    def test_game_start_stop(self):
        """Test start og stopp av spill"""
        self.engine.start_game()
        self.assertTrue(self.engine.game_running)

        self.engine.stop_game()
        self.assertFalse(self.engine.game_running)


if __name__ == "__main__":
    unittest.main()
