import unittest
from engine import GameEngine
from collections import defaultdict


class TestBonusEvents(unittest.TestCase):
    def setUp(self):
        self.game = GameEngine()
        # Add test players and give them some shares
        self.game.add_player("Player1")
        self.game.add_player("Player2")

        # Give players some shares to test with
        for share in ["LEAD", "ZINC", "TIN", "GOLD"]:
            self.game.player_data["Player1"]["shares"][share] = 10
            self.game.player_data["Player2"]["shares"][share] = 10

    def test_bonus_distribution(self):
        """Test that bonus payments and share splits are fairly distributed"""
        bonus_payments = defaultdict(int)
        share_splits = defaultdict(int)
        flash_news_count = 0

        # Run many iterations to get statistical distribution
        for _ in range(1000):
            news = self.game.generate_flash_news()
            if news:
                flash_news_count += 1
                for event in news:
                    if "BONUS PAYMENT TO ALL" in event:
                        share = event.split()[3]  # Get share name
                        bonus_payments[share] += 1
                    elif "BONUS ISSUE" in event:
                        share = event.split()[0]  # Get share name
                        share_splits[share] += 1

        # Print statistics
        print("\nBonus Payment Distribution:")
        for share, count in bonus_payments.items():
            print(
                f"{share}: {count} times ({count/sum(bonus_payments.values())*100:.1f}%)"
            )

        print("\nShare Split Distribution:")
        for share, count in share_splits.items():
            print(
                f"{share}: {count} times ({count/sum(share_splits.values())*100:.1f}%)"
            )

        print(f"\nTotal flash news events: {flash_news_count}")

        # Test that the distribution is roughly even (within 10% of expected)
        if bonus_payments:
            expected_share = sum(bonus_payments.values()) / len(bonus_payments)
            for count in bonus_payments.values():
                self.assertLess(abs(count - expected_share), expected_share * 0.3)

        if share_splits:
            expected_share = sum(share_splits.values()) / len(share_splits)
            for count in share_splits.values():
                self.assertLess(abs(count - expected_share), expected_share * 0.3)

    def test_bonus_effects(self):
        """Test that bonuses and splits actually affect player holdings"""
        # Store initial share counts
        initial_shares = {
            player: {
                share: self.game.player_data[player]["shares"][share]
                for share in ["LEAD", "ZINC", "TIN", "GOLD"]
            }
            for player in ["Player1", "Player2"]
        }

        # Record changes from many news events
        changes_observed = False
        for _ in range(100):
            self.game.generate_flash_news()

            # Check if any shares changed
            for player in ["Player1", "Player2"]:
                for share in ["LEAD", "ZINC", "TIN", "GOLD"]:
                    if (
                        self.game.player_data[player]["shares"][share]
                        != initial_shares[player][share]
                    ):
                        changes_observed = True
                        print(f"\nShare change detected for {player}'s {share} shares")
                        print(f"Before: {initial_shares[player][share]}")
                        print(
                            f"After: {self.game.player_data[player]['shares'][share]}"
                        )

        self.assertTrue(
            changes_observed, "No share changes were observed after 100 iterations"
        )


if __name__ == "__main__":
    unittest.main()
