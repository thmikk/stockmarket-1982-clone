from typing import Dict, List, Set, Optional, Union, TypedDict, Tuple
import random


class PlayerData(TypedDict):
    balance: int
    shares: Dict[str, int]
    loan: int
    bankrupt: bool
    trades_count: int  # Track number of trades per player per round


SHARES = ["LEAD", "ZINC", "TIN", "GOLD"]

INITIAL_SHARE_PRICES = {"LEAD": 10, "ZINC": 50, "TIN": 250, "GOLD": 1250}
MIN_PRICES = {"LEAD": 1, "ZINC": 5, "TIN": 25, "GOLD": 125}  # Min 1/10 av startpris
MAX_PRICES = {k: v * 2 for k, v in INITIAL_SHARE_PRICES.items()}
INITIAL_BALANCE = 1000
DEFAULT_TARGET_VALUE = 1000000
DEFAULT_DIFFICULTY = 1  # 1 = easy


class GameEngine:
    def __init__(
        self,
        difficulty: int = DEFAULT_DIFFICULTY,
        target_value: int = DEFAULT_TARGET_VALUE,
    ):
        # Player management
        self.players: List[str] = []
        self.player_data: Dict[str, PlayerData] = {}
        self.current_player_index: int = 0

        # Share prices and market state
        self.share_prices: Dict[str, int] = INITIAL_SHARE_PRICES.copy()
        self.max_prices: Dict[str, int] = MAX_PRICES.copy()
        self.buy_volumes: Dict[str, int] = {k: 0 for k in SHARES}
        self.sell_volumes: Dict[str, int] = {k: 0 for k in SHARES}
        self.last_prices: Dict[str, int] = self.share_prices.copy()
        self.last_totals: Dict[str, int] = {k: 0 for k in SHARES}

        # Market suspension tracking
        self.market_suspended: bool = False
        self.suspended_shares: Set[str] = set()
        self.suspended_shares_rounds: Dict[str, int] = {}

        # Game state
        self.turn: int = 0
        self.round: int = 0
        self.difficulty: int = difficulty
        self.target_value: int = target_value
        self.total_trade_attempts: int = (
            0  # Counter for all trade attempts (successful or failed)
        )

        # Bonus/event tracking
        self._last_bonus_share: Optional[str] = None
        self._last_event_share: Optional[str] = None
        self._last_flash_share: Optional[str] = None
        self._last_news_round: int = -1
        self._flash_news_count: int = 0

        # Pressure history for sustained price movements
        self.pressure_history: Dict[str, List[float]] = {s: [0.0] * 3 for s in SHARES}

    def add_player(self, name: str) -> None:
        if name not in self.players:
            self.players.append(name)
            self.player_data[name] = {
                "balance": INITIAL_BALANCE,
                "shares": {k: 0 for k in SHARES},
                "loan": 0,
                "bankrupt": False,  # Track bankruptcy status
                "trades_count": 0,  # Initialize trades count
            }

    def get_current_player(self) -> Optional[str]:
        if self.players:
            return self.players[self.current_player_index]
        return None

    def calculate_max_loan(self, username: str) -> int:
        pdata = self.player_data[username]
        share_value = sum(pdata["shares"][s] * self.share_prices[s] for s in SHARES)
        return int(0.5 * (share_value + pdata["balance"]) - pdata["loan"])

    def reset_game(self) -> None:
        self.__init__(self.difficulty, self.target_value)

    def get_player_values(self) -> List[Dict[str, Union[str, int]]]:
        values = []
        for name in self.players:
            pdata = self.player_data[name]
            total_value = pdata["balance"] + sum(
                pdata["shares"][s] * self.share_prices[s] for s in SHARES
            )
            values.append({"name": name, "totalValue": total_value})
        return values

    def buy(self, username: str, share: str, amount: int) -> Tuple[bool, str]:
        # Always increment total trade attempts, regardless of outcome
        self.total_trade_attempts += 1

        # Check if player is bankrupt (like original line 515-520)
        pdata = self.player_data[username]
        if pdata.get("bankrupt", False):
            return False, "Cannot trade - you are bankrupt!"

        price = self.share_prices[share]
        cost = price * amount
        if pdata["balance"] >= cost:
            # Only increment trades_count on successful trades
            pdata["trades_count"] += 1
            pdata["balance"] -= cost
            pdata["shares"][share] += amount
            self.buy_volumes[share] += amount
            return True, "Bought successfully"
        else:
            max_loan = self.calculate_max_loan(username)
            additional_needed = cost - pdata["balance"]
            if pdata["loan"] + additional_needed <= max_loan:
                # Only increment trades_count on successful trades
                pdata["trades_count"] += 1
                pdata["loan"] += additional_needed
                pdata["balance"] += additional_needed
                pdata["balance"] -= cost
                pdata["shares"][share] += amount
                self.buy_volumes[share] += amount
                return True, "Bought with loan"
            else:
                return False, "Insufficient funds"

    def sell(self, username: str, share: str, amount: int) -> Tuple[bool, str]:
        # Always increment total trade attempts, regardless of outcome
        self.total_trade_attempts += 1

        # Check if player is bankrupt (like original line 515-520)
        pdata = self.player_data[username]
        if pdata.get("bankrupt", False):
            return False, "Cannot trade - you are bankrupt!"

        if pdata["shares"][share] >= amount:
            # Only increment trades_count on successful trades
            pdata["trades_count"] += 1
            pdata["shares"][share] -= amount
            sale_value = self.share_prices[share] * amount
            pdata["balance"] += sale_value
            self.sell_volumes[share] += amount

            # Auto-repay loan if possible (like original line 3770-3795)
            if pdata["loan"] > 0:
                if pdata["loan"] <= pdata["balance"]:
                    # Pay off entire loan
                    pdata["balance"] -= pdata["loan"]
                    loan_amount = pdata["loan"]
                    pdata["loan"] = 0
                    return True, (
                        f"Sold successfully. Bank loan of " f"£{loan_amount} repaid"
                    )
                else:
                    # Still need more cash to repay bank
                    return (
                        True,
                        "Sold successfully. You need more cash to repay the bank",
                    )

            return True, "Sold successfully"
        else:
            return False, "Not enough shares"

    def repay_loan(
        self, username: str, amount: Optional[int] = None
    ) -> Tuple[bool, str]:
        """Repay loan manually (Q option when selling in original)"""
        pdata = self.player_data[username]

        if pdata["loan"] <= 0:
            return False, "No loan to repay"

        if amount is None:
            amount = min(pdata["loan"], pdata["balance"])

        if amount > pdata["balance"]:
            return False, "Insufficient funds to repay that amount"

        if amount > pdata["loan"]:
            amount = pdata["loan"]

        pdata["balance"] -= amount
        pdata["loan"] -= amount

        if pdata["loan"] == 0:
            return True, f"Loan fully repaid (£{amount})"
        else:
            return (
                True,
                f"Partial loan repayment (£{amount}). Remaining: £{pdata['loan']}",
            )

    def check_bankruptcy(self, username: str) -> Tuple[bool, str]:
        """Check if player is bankrupt (like original line 3800-3835)"""
        pdata = self.player_data[username]

        # Calculate total assets including shares
        total_asset_value = pdata["balance"]
        for share in SHARES:
            total_asset_value += pdata["shares"][share] * self.share_prices[share]

        # If loan exceeds ability to pay even with forced liquidation
        if pdata["loan"] > total_asset_value:
            # Force liquidation of all shares (line 3810)
            for share in SHARES:
                if pdata["shares"][share] > 0:
                    sale_value = pdata["shares"][share] * self.share_prices[share]
                    pdata["balance"] += sale_value
                    self.sell_volumes[share] += pdata["shares"][share]
                    pdata["shares"][share] = 0

            # Try to pay loan
            if pdata["balance"] >= pdata["loan"]:
                pdata["balance"] -= pdata["loan"]
                pdata["loan"] = 0
                return False, "Forced liquidation completed. Loan repaid."
            else:
                # Bankruptcy (line 3830)
                pdata["balance"] = 0
                pdata["loan"] = 0
                return True, "YOU ARE BANKRUPT SIR!"

        return False, ""

    def end_turn(self) -> Tuple[List[str], List[str], bool]:
        """
        End the current player's turn and process end-of-round events if needed.
        Returns:
            Tuple containing:
            - List of winner names (if any)
            - List of news events
            - Boolean indicating if this is the end of a round
        """
        # Reset flash news counter at start of new round
        self._flash_news_count = 0
        self._last_bonus_share = None

        # Find next non-bankrupt player
        attempts = 0
        while attempts < len(self.players):
            self.current_player_index = (self.current_player_index + 1) % len(
                self.players
            )
            current_player = self.players[self.current_player_index]

            if not self.player_data[current_player].get("bankrupt", False):
                break

            attempts += 1

        # If all players are bankrupt, end game
        if attempts >= len(self.players):
            return ["GAME OVER - ALL BANKRUPT"], [], True

        news_events: List[str] = []
        is_round_end = False

        if self.current_player_index == 0:
            # End of round - all players have completed their turns
            is_round_end = True
            self.round += 1
            self.last_prices = self.share_prices.copy()

            # Reset market state
            self.suspended_shares.clear()
            self.suspended_shares_rounds.clear()
            self.collect_loan_interest()
            self.buy_volumes = {k: 0 for k in SHARES}
            self.sell_volumes = {k: 0 for k in SHARES}

            # Reset trade counters for all players
            for player_data in self.player_data.values():
                player_data["trades_count"] = 0

            # Generate market news at the end of each round
            news_events = self.generate_market_news()

        winners: List[str] = []
        millionaires = self.check_millionaires()

        # Check for bankruptcy
        bankruptcy_messages = self.check_end_of_turn_bankruptcy()
        if bankruptcy_messages:
            news_events.extend([""] + bankruptcy_messages)

        # Check for winners by total value
        for name in self.players:
            pdata = self.player_data[name]
            total_value = (
                pdata["balance"]
                + sum(pdata["shares"][s] * self.share_prices[s] for s in SHARES)
                - pdata["loan"]
            )
            if total_value >= self.target_value:
                winners.append(name)

        # Add millionaires to winners list
        if millionaires:
            winners.extend(millionaires)

        return winners, news_events, is_round_end

    def check_end_of_turn_bankruptcy(self) -> List[str]:
        """Check bankruptcy status for all players at the end of a turn"""
        bankruptcy_messages: List[str] = []

        for username, pdata in self.player_data.items():
            # Skip already bankrupt players
            if pdata.get("bankrupt", False):
                continue

            # Calculate total assets including shares
            total_value = pdata["balance"]
            for share in SHARES:
                total_value += pdata["shares"][share] * self.share_prices[share]

            # Check if player is bankrupt
            if pdata["loan"] > total_value:
                pdata["bankrupt"] = True
                bankruptcy_messages.append(f"{username} IS BANKRUPT!")

        return bankruptcy_messages

    def check_millionaires(self) -> List[str]:
        """Check if any player has reached the target value"""
        millionaires = []

        for name in self.players:
            if self.player_data[name].get("bankrupt", False):
                continue

            pdata = self.player_data[name]
            total_value = (
                pdata["balance"]
                + sum(pdata["shares"][s] * self.share_prices[s] for s in SHARES)
                - pdata["loan"]
            )
            if total_value >= self.target_value:
                millionaires.append(name)

        return millionaires

    def collect_loan_interest(self) -> None:
        """Collect interest on loans at end of round"""
        for name in self.players:
            pdata = self.player_data[name]
            if pdata["loan"] > 0:
                interest = int(pdata["loan"] * 0.1)  # 10% interest
                pdata["loan"] += interest

    def update_share_prices_c64(self) -> None:
        """
        Update share prices using C64-inspired algorithm with improved volume sensitivity,
        proper bonus share price adjustments, and persistent price momentum.
        """
        total_now: Dict[str, int] = {s: 0 for s in SHARES}
        for pdata in self.player_data.values():
            for s in SHARES:
                total_now[s] += pdata["shares"][s]

        for i, s in enumerate(SHARES):
            # Each share has different base movement
            base_step = [1, 5, 25, 125][i]  # LEAD, ZINC, TIN, GOLD

            # Get current price and trade volumes
            p = self.share_prices[s]
            buys = self.buy_volumes[s]
            sells = self.sell_volumes[s]
            net_volume = buys - sells
            total_volume = buys + sells

            # Calculate volume impact and market pressure
            volume_factor = 0
            market_pressure = 0.0

            if total_volume > 0:  # Only consider pressure if there is trading
                # Convert volumes to percentages of total shares
                total_shares = max(
                    1, sum(pdata["shares"][s] for pdata in self.player_data.values())
                )
                buy_percent = (buys / total_shares) * 100
                sell_percent = (sells / total_shares) * 100

                # Calculate directional pressure (-1.0 to +1.0)
                if net_volume != 0:
                    pressure = (buy_percent - sell_percent) / max(
                        buy_percent + sell_percent, 1
                    )

                    # Scale volume factor based on total trading activity (1-15)
                    activity_scale = min(
                        15, max(1, int((buy_percent + sell_percent) / 5))
                    )

                    # Stronger impact for heavy one-sided trading
                    dominance = abs(pressure)  # How one-sided the trading is (0-1)

                    # Calculate final volume factor
                    volume_factor = int(activity_scale * (1 + dominance))
                    if net_volume < 0:
                        volume_factor = -volume_factor

                    # Update pressure history
                    self.pressure_history[s].pop(0)
                    self.pressure_history[s].append(pressure)

                    # Calculate market pressure from history
                    market_pressure = sum(self.pressure_history[s]) / len(
                        self.pressure_history[s]
                    )

            # Random factor reduced for active trading
            if total_volume > 0:
                r = random.randint(-1, 1)  # Smaller random factor during active trading
            else:
                r = random.randint(-2, 2)  # Larger random factor for quiet periods

            # Base price change from volume
            price_change = volume_factor * base_step

            # Add momentum from pressure history
            momentum = int(market_pressure * base_step * 2)
            price_change += momentum

            # Add reduced random factor
            price_change += r * base_step

            # Ensure minimum movement for significant trading
            min_move = max(1, int(p * 0.05))  # Minimum 5% move
            if total_volume > 0 and abs(price_change) < min_move:
                price_change = min_move if price_change > 0 else -min_move

            # Apply difficulty multiplier more predictably
            if self.difficulty >= 2:
                # Higher difficulty increases volatility but preserves direction
                volatility = (
                    1 + (self.difficulty - 1) * 0.5
                )  # 1.5x for diff 2, 2x for diff 3
                price_change = int(price_change * volatility)

            # Handle bonus share price adjustment
            if s == self._last_bonus_share:
                # If shares were doubled, price should be halved to maintain value
                target_price = max(MIN_PRICES[s], p // 2)
                # Move price smoothly towards target
                if p > target_price:
                    price_change = -base_step * 2  # Move down faster during split
                self._last_bonus_share = None  # Reset after handling

            # Apply change with limits and ensure movement
            new_price = max(
                MIN_PRICES[s], min(self.max_prices[s], int(p + price_change))
            )

            # Prevent price from getting stuck, with bias based on pressure
            if new_price == p:
                bias = sum(self.pressure_history[s]) / len(self.pressure_history[s])
                min_change = max(1, int(p * 0.02))  # Minimum 2% change
                if bias > 0:  # Upward pressure - more likely to rise
                    new_price += (
                        min_change
                        if random.random() < (0.6 + bias * 0.2)
                        else -min_change
                    )
                elif bias < 0:  # Downward pressure - more likely to fall
                    new_price += (
                        min_change
                        if random.random() < (0.4 + bias * 0.2)
                        else -min_change
                    )
                else:  # No pressure - random movement
                    new_price += min_change if random.random() < 0.5 else -min_change
                new_price = max(MIN_PRICES[s], min(self.max_prices[s], new_price))

            self.share_prices[s] = new_price

        self.last_totals = total_now.copy()

    def generate_flash_news(self) -> List[str]:
        """Generate flash news during player turn"""
        import time

        news_events: List[str] = []

        # Base chance for all events decreases with trade attempts
        event_chance = max(0.1, 1.0 - (self.total_trade_attempts * 0.02))

        # Prevent flash news from happening too often
        current_time = time.time()
        if hasattr(self, "_last_flash_news_time"):
            if (
                current_time - self._last_flash_news_time < 5
            ):  # At least 5 seconds between
                return []
        self._last_flash_news_time = current_time

        # Reduce chance further based on how many have happened this round
        if not hasattr(self, "_flash_news_count"):
            self._flash_news_count = 0
        if random.random() < (self._flash_news_count * 0.2):
            return []

        # Base check for any event
        if random.random() > event_chance:
            return []  # No event due to high trade attempts

        news_events.append("!! NEWSFLASH !!")

        # Pick event type with weighted probabilities
        event_roll = random.random()

        # Market weakness (10% base chance)
        if event_roll < 0.1:
            news_events.append("MARKET VERY WEAK")
            return news_events

        # Tax investigations (higher chance with more trades)
        if self.total_trade_attempts > 3 and event_roll < 0.4:
            tax_prob = min(0.8, 0.1 + (self.total_trade_attempts * 0.05))
            if random.random() < tax_prob:
                news_events.append("CAPITAL GAINS TAX INVESTIGATIONS")

                # Get current player's trade count
                current_player = self.get_current_player()
                trades = (
                    self.player_data[current_player]["trades_count"]
                    if current_player
                    else 0
                )

                # Determine tax rate based on trading activity
                if trades <= 5:  # Few trades: low tax
                    r_tax = random.randint(1, 3)  # 10-30%
                elif trades <= 10:  # Moderate trades: medium tax
                    r_tax = random.randint(3, 5)  # 30-50%
                else:  # Many trades: high tax
                    r_tax = random.randint(5, 9)  # 50-90%

                if random.random() < 0.2:  # 20% chance of relenting
                    news_events.append("TAX OFFICE RELENTS !...NO TAX DEMAND")
                else:
                    tax_rate = r_tax * 10
                    news_events.append(f"DEMAND OF {tax_rate}% OF BANK BALANCE")
                    if current_player:
                        pdata = self.player_data[current_player]
                        tax = int(pdata["balance"] * (r_tax * 0.1))
                        pdata["balance"] = max(0, pdata["balance"] - tax)
                return news_events

        # Trading practice investigation (more likely with high trades)
        if self.total_trade_attempts > 10 and event_roll < 0.6:
            investigate_prob = min(0.9, 0.2 + (self.total_trade_attempts * 0.05))
            if random.random() < investigate_prob:
                news_events.append("TRADING PRACTICES UNDER SUSPICION")
                news_events.append("TAX OFFICIALS INVESTIGATE")
                return news_events

        # Bonus shares (less likely with more trades)
        if event_roll < 0.8:
            bonus_prob = max(0.1, 1.0 - (self.total_trade_attempts * 0.02))
            if random.random() < bonus_prob:
                chosen_share = SHARES[random.randint(0, len(SHARES) - 1)]
                news_events.append(f"{chosen_share} SHARES BONUS ISSUE OF 1 SHARE")
                news_events.append("FOR EVERY TWO SHARES HELD")

                # Apply bonus to all players
                for player in self.player_data.values():
                    if chosen_share in player["shares"]:
                        bonus_shares = player["shares"][chosen_share] // 2
                        player["shares"][chosen_share] += bonus_shares
                return news_events

        # Tax refund (fallback event)
        news_events.append("TAX .. REFUND")
        r_refund = random.randint(0, 9)
        if r_refund == 0:
            news_events.append("ERROR IN TAX OFFICE ! NO REFUND")
        else:
            refund_rate = 10 * r_refund
            news_events.append(f"REFUND = {refund_rate}% OF BANK BALANCE")
            # Apply to current player only
            current_player = self.get_current_player()
            if current_player:
                pdata = self.player_data[current_player]
                refund = int(pdata["balance"] * (0.1 * r_refund))
                pdata["balance"] += refund

        self._flash_news_count += 1
        return news_events

    def generate_market_news(self) -> List[str]:
        """Generate market news at the end of each round"""
        news_events: List[str] = []

        # Base chance for all events decreases with trade attempts
        event_chance = max(0.1, 1.0 - (self.total_trade_attempts * 0.02))

        # Market suspension events
        if not self.suspended_shares:  # Only check if no shares are suspended
            if random.random() < event_chance * 0.2:  # 20% of event_chance
                chosen_share = random.choice(SHARES)
                if chosen_share not in self.suspended_shares:
                    self.suspended_shares.add(chosen_share)
                    self.suspended_shares_rounds[chosen_share] = random.randint(1, 3)
                    news_events.append(f"{chosen_share} MARKET DEALINGS SUSPENDED")

        # Share split events (with cooldown and reduced probability)
        if random.random() < event_chance * 0.2:  # 20% of event_chance
            # Avoid recently split shares
            eligible_shares = [s for s in SHARES if s != self._last_event_share]
            if eligible_shares:  # Only proceed if we have eligible shares
                chosen_share = random.choice(eligible_shares)
                self._last_event_share = chosen_share
                news_events.append(f"{chosen_share} SHARES SPLIT")
                news_events.append("TWO FOR EVERY ONE HELD")

                # Apply split to all players
                for player in self.player_data.values():
                    if not player.get("bankrupt", False):
                        player["shares"][chosen_share] *= 2
                self.share_prices[chosen_share] = max(
                    MIN_PRICES[chosen_share], self.share_prices[chosen_share] // 2
                )

        # Process suspended shares
        for share in list(self.suspended_shares):
            if share in self.suspended_shares_rounds:
                self.suspended_shares_rounds[share] -= 1
                if self.suspended_shares_rounds[share] <= 0:
                    self.suspended_shares.remove(share)
                    del self.suspended_shares_rounds[share]
                    news_events.append(f"{share} MARKET DEALINGS RESUMED")

        # Update share prices
        self.update_share_prices_c64()

        # Report price changes
        for share in SHARES:
            if share in self.suspended_shares:
                continue

            old_price = self.last_prices[share]
            new_price = self.share_prices[share]

            if new_price > old_price:
                news_events.append(f"{share} UP BY £{new_price - old_price}")
            elif new_price < old_price and new_price > MIN_PRICES[share]:
                news_events.append(f"{share} DOWN BY £{old_price - new_price}")

        return news_events

    def check_last_player_standing(self) -> Optional[str]:
        """Check if only one non-bankrupt player remains"""
        active_players = [
            name
            for name in self.players
            if not self.player_data[name].get("bankrupt", False)
        ]
        return active_players[0] if len(active_players) == 1 else None

    def calculate_final_scores(self) -> List[Dict[str, Union[str, int]]]:
        """Calculate final scores and rankings"""
        results = []

        for name in self.players:
            pdata = self.player_data[name]

            total_value = pdata["balance"]
            for share in SHARES:
                total_value += pdata["shares"][share] * self.share_prices[share]
            total_value -= pdata["loan"]

            profit_made = total_value - INITIAL_BALANCE
            divisor = max(1, self.round + self.difficulty * 5)
            score = int(total_value / divisor)

            results.append(
                {
                    "name": name,
                    "total_value": int(total_value),
                    "profit_made": int(profit_made),
                    "score": score,
                }
            )

        results.sort(key=lambda x: x["total_value"], reverse=True)
        return results
