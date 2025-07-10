from typing import Dict, List, Set, Optional, Union, TypedDict, Tuple
import random


class PlayerData(TypedDict):
    balance: int
    shares: Dict[str, int]
    loan: int
    bankrupt: bool


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
        self.ch: int = 0  # Counter for various game events

        # Bonus/event tracking
        self._last_bonus_share: Optional[str] = None
        self._last_event_share: Optional[str] = None
        self._last_flash_share: Optional[str] = None
        self._last_news_round: int = -1
        self._flash_news_count: int = 0

    def add_player(self, name: str) -> None:
        if name not in self.players:
            self.players.append(name)
            self.player_data[name] = {
                "balance": INITIAL_BALANCE,
                "shares": {k: 0 for k in SHARES},
                "loan": 0,
                "bankrupt": False,  # Track bankruptcy status
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
        # Check if player is bankrupt (like original line 515-520)
        pdata = self.player_data[username]
        if pdata.get("bankrupt", False):
            return False, "Cannot trade - you are bankrupt!"

        # Increment ch counter for each buy attempt (like original line 3300)
        self.ch += 1

        price = self.share_prices[share]
        cost = price * amount
        if pdata["balance"] >= cost:
            pdata["balance"] -= cost
            pdata["shares"][share] += amount
            self.buy_volumes[share] += amount
            return True, "Bought successfully"
        else:
            max_loan = self.calculate_max_loan(username)
            additional_needed = cost - pdata["balance"]
            if pdata["loan"] + additional_needed <= max_loan:
                pdata["loan"] += additional_needed
                pdata["balance"] += additional_needed
                pdata["balance"] -= cost
                pdata["shares"][share] += amount
                self.buy_volumes[share] += amount
                return True, "Bought with loan"
            else:
                return False, "Insufficient funds"

    def sell(self, username: str, share: str, amount: int) -> Tuple[bool, str]:
        # Check if player is bankrupt (like original line 515-520)
        pdata = self.player_data[username]
        if pdata.get("bankrupt", False):
            return False, "Cannot trade - you are bankrupt!"

        # Increment ch counter for each sell attempt (like original line 3300)
        self.ch += 1

        pdata = self.player_data[username]
        if pdata["shares"][share] >= amount:
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
            self.ch = 0

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
        Update share prices using authentic C64 algorithm.
        Original game used simple random changes with trade volume influence.
        """
        total_now: Dict[str, int] = {s: 0 for s in SHARES}
        for pdata in self.player_data.values():
            for s in SHARES:
                total_now[s] += pdata["shares"][s]

        for i, s in enumerate(SHARES):
            # Each share has different base movement (like original)
            base_step = [1, 5, 25, 125][i]  # LEAD, ZINC, TIN, GOLD

            # Get current price and trade volume
            p = self.share_prices[s]
            tp = self.last_totals[s]
            tn = total_now[s]
            volume_change = tn - tp

            # Basic random change (-2 to +2 like C64)
            r = random.randint(-2, 2)

            # Volume influence (simplified from original)
            if volume_change > 0:  # More buying
                r += 1 if random.random() < 0.7 else 0
            elif volume_change < 0:  # More selling
                r -= 1 if random.random() < 0.7 else 0

            # 30% chance of no change
            if random.random() < 0.3:
                r = 0

            # Calculate price change
            pc = r * base_step

            # Apply difficulty multiplier (like original)
            if self.difficulty >= 2:
                if random.random() < 0.3:  # 30% chance of bigger moves
                    pc *= self.difficulty

            # 10% chance of price staying exactly the same
            if random.random() < 0.1:
                pc = 0

            # Apply change with limits
            new_price = int(p + pc)
            new_price = max(MIN_PRICES[s], min(self.max_prices[s], new_price))

            # In original, sometimes prices would stick for a while
            if (
                new_price == p and random.random() < 0.2
            ):  # 20% chance of small movement when stuck
                new_price += base_step if random.random() < 0.5 else -base_step
                new_price = max(MIN_PRICES[s], min(self.max_prices[s], new_price))

            self.share_prices[s] = new_price

        self.last_totals = total_now.copy()

    def generate_flash_news(self) -> List[str]:
        """Generate flash news during player turn"""
        import time

        news_events: List[str] = []

        # Prevent flash news from happening too often
        current_time = time.time()
        if hasattr(self, "_last_flash_news_time"):
            if (
                current_time - self._last_flash_news_time < 5
            ):  # At least 5 seconds between flash news
                return []
        self._last_flash_news_time = current_time

        # Reduce chance of flash news based on how many have happened this round
        if not hasattr(self, "_flash_news_count"):
            self._flash_news_count = 0
        if random.random() < (self._flash_news_count * 0.2):
            return []

        news_events.append("!! NEWSFLASH !!")

        # Original logic from lines 2630-2960
        if self.ch > 12:
            # Capital gains tax investigations (line 2870)
            news_events.append("CAPITAL GAINS TAX INVESTIGATIONS")
            r_tax = random.randint(0, 9)
            if r_tax == 0:
                news_events.append("TAX OFFICE RELENTS !...NO TAX DEMAND")
            else:
                news_events.append(f"DEMAND OF {r_tax * 10}% OF BANK BALANCE")
                # Apply tax to current player only (like original)
                current_player = self.get_current_player()
                if current_player:
                    pdata = self.player_data[current_player]
                    tax = int(pdata["balance"] * (r_tax * 0.1))
                    pdata["balance"] = max(0, pdata["balance"] - tax)
            return news_events

        if self.ch > 10:
            # Trading practices under suspicion (line 2950)
            news_events.append("TRADING PRACTICES UNDER SUSPICION")
            news_events.append("TAX OFFICIALS INVESTIGATE")
            self.ch = 100  # Set high value like original
            return news_events

        # Original difficulty check and random events
        r = random.randint(0, 9)
        if r > 4 + self.difficulty:
            # Bonus share issues or other events
            r_bonus = random.randint(0, 9)
            if r_bonus == 0:
                news_events.append("MARKET VERY WEAK")
                return news_events
            elif r_bonus <= 4:
                # Capital gains tax path
                news_events.append("CAPITAL GAINS TAX INVESTIGATIONS")
                r_tax = random.randint(0, 9)
                if r_tax == 0:
                    news_events.append("TAX OFFICE RELENTS !...NO TAX DEMAND")
                else:
                    news_events.append(f"DEMAND OF {r_tax * 10}% OF BANK BALANCE")
                    # Apply tax to current player only (like original)
                    current_player = self.get_current_player()
                    if current_player:
                        pdata = self.player_data[current_player]
                        tax = int(pdata["balance"] * (r_tax * 0.1))
                        pdata["balance"] = max(0, pdata["balance"] - tax)
                return news_events
            else:
                # Bonus share issue (line 2840)
                # Velg aksje med lik sannsynlighet for alle
                share = SHARES[random.randint(0, len(SHARES) - 1)]
                news_events.append(f"{share} SHARES BONUS ISSUE OF 1 SHARE")
                news_events.append("FOR EVERY TWO SHARES HELD")

                # Apply to all players
                for player in self.player_data.values():
                    if share in player["shares"]:
                        bonus_shares = player["shares"][share] // 2
                        player["shares"][share] += bonus_shares
                return news_events

        # Original main flash news logic (line 2660 onwards)
        r_main = random.randint(0, 9)
        if r_main == 0:
            # All market dealings suspended (line 2790)
            news_events.append("ALL MARKET DEALINGS SUSPENDED")
            for share in SHARES:
                self.suspended_shares.add(share)
                self.suspended_shares_rounds[share] = 3
            return news_events
        elif r_main > 4:
            # Tax refund (line 2750)
            news_events.append("TAX .. REFUND")
            r_refund = random.randint(0, 9)
            if r_refund == 0:
                news_events.append("ERROR IN TAX OFFICE ! NO REFUND")
            else:
                news_events.append(f"REFUND = {10 * r_refund}% OF BANK BALANCE")
                # Apply to current player only
                current_player = self.get_current_player()
                if current_player:
                    pdata = self.player_data[current_player]
                    refund = int(pdata["balance"] * (0.1 * r_refund))
                    pdata["balance"] += refund
            return news_events
        else:
            # Bonus payment to shareholders (line 2690)
            # Velg aksje med lik sannsynlighet for alle
            share = SHARES[random.randint(0, len(SHARES) - 1)]
            news_events.append(f"BONUS PAYMENT TO ALL {share} SHAREHOLDERS")

            r_payment = random.randint(0, 9)
            if r_payment == 0:
                news_events.append("PAYMENT SUSPENDED BECAUSE OF STRIKE")
            else:
                percentage = r_payment * 10
                news_events.append(f"PAYMENT = {percentage}% OF SHARE VALUE")

                # Apply to all players (line 2730)
                for player in self.player_data.values():
                    if share in player["shares"] and player["shares"][share] > 0:
                        bonus = int(
                            0.1
                            * r_payment
                            * player["shares"][share]
                            * self.share_prices[share]
                        )
                        player["balance"] += bonus
            return news_events

    def generate_market_news(self) -> List[str]:
        """Generate market news at the end of each round"""
        news_events: List[str] = []

        # Market suspension events
        r_suspend = random.randint(0, 9)
        if (
            r_suspend < 2 and not self.suspended_shares
        ):  # 20% chance if no shares suspended
            share = random.choice(SHARES)
            if share not in self.suspended_shares:
                self.suspended_shares.add(share)
                self.suspended_shares_rounds[share] = random.randint(1, 3)
                news_events.append(f"{share} MARKET DEALINGS SUSPENDED")

        # Bonus events (with cooldown)
        r_bonus = random.randint(0, 9)
        if r_bonus < 3:  # 30% chance
            share = random.choice([s for s in SHARES if s != self._last_bonus_share])
            self._last_bonus_share = share
            bonus_amount = random.randint(1, 5) * 10
            news_events.append(f"BONUS PAYMENT TO ALL {share} SHAREHOLDERS")
            news_events.append(f"PAYMENT = {bonus_amount}% OF SHARE VALUE")

            for player in self.player_data.values():
                if not player.get("bankrupt", False):
                    share_count = player["shares"][share]
                    if share_count > 0:
                        payment = int(
                            share_count
                            * self.share_prices[share]
                            * (bonus_amount / 100)
                        )
                        player["balance"] += payment

        # Share split events (with cooldown)
        r_split = random.randint(0, 9)
        if r_split < 2:  # 20% chance
            share = random.choice([s for s in SHARES if s != self._last_event_share])
            self._last_event_share = share
            news_events.append(f"{share} SHARES SPLIT")
            news_events.append("TWO FOR EVERY ONE HELD")

            for player in self.player_data.values():
                if not player.get("bankrupt", False):
                    player["shares"][share] *= 2
            self.share_prices[share] = max(
                MIN_PRICES[share], self.share_prices[share] // 2
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
