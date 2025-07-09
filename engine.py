import random

SHARES = ["LEAD", "ZINC", "TIN", "GOLD"]

INITIAL_SHARE_PRICES = {"LEAD": 10, "ZINC": 50, "TIN": 250, "GOLD": 1250}
MIN_PRICES = INITIAL_SHARE_PRICES.copy()
MAX_PRICES = {k: v * 2 for k, v in INITIAL_SHARE_PRICES.items()}
INITIAL_BALANCE = 1000
DEFAULT_TARGET_VALUE = 1000000
DEFAULT_DIFFICULTY = 1  # 1 = easy


class GameEngine:
    def __init__(
        self, difficulty=DEFAULT_DIFFICULTY, target_value=DEFAULT_TARGET_VALUE
    ):
        self.players = []
        self.player_data = {}
        self.share_prices = INITIAL_SHARE_PRICES.copy()
        self.max_prices = MAX_PRICES.copy()
        self.turn = 0
        self.round = 0
        self.difficulty = difficulty
        self.target_value = target_value
        self.current_player_index = 0
        self.market_suspended = False
        self.suspended_shares = set()
        self.suspended_shares_rounds = {}
        self.market_trend = 0
        self.market_trend_rounds_left = 0
        self.buy_volumes = {k: 0 for k in SHARES}
        self.sell_volumes = {k: 0 for k in SHARES}
        self.ch = 0
        self.last_totals = {k: 0 for k in SHARES}
        self.last_prices = self.share_prices.copy()

    def add_player(self, name):
        if name not in self.players:
            self.players.append(name)
            self.player_data[name] = {
                "balance": INITIAL_BALANCE,
                "shares": {k: 0 for k in SHARES},
                "loan": 0,
                "bankrupt": False,  # Track bankruptcy status
            }

    def get_current_player(self):
        if self.players:
            return self.players[self.current_player_index]
        return None

    def calculate_max_loan(self, username):
        pdata = self.player_data[username]
        share_value = sum(pdata["shares"][s] * self.share_prices[s] for s in SHARES)
        return int(0.5 * (share_value + pdata["balance"]) - pdata["loan"])

    def reset_game(self):
        self.__init__(self.difficulty, self.target_value)

    def get_player_values(self):
        values = []
        for name in self.players:
            pdata = self.player_data[name]
            total_value = pdata["balance"] + sum(
                pdata["shares"][s] * self.share_prices[s] for s in SHARES
            )
            values.append({"name": name, "totalValue": total_value})
        return values

    def buy(self, username, share, amount):
        # Check if player is bankrupt (like original line 515-520)
        pdata = self.player_data[username]
        if pdata.get("bankrupt", False):
            return False, "Cannot trade - you are bankrupt!"

        # Increment ch counter for each buy attempt (like original line 3300)
        self.ch += 1

        pdata = self.player_data[username]
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

    def sell(self, username, share, amount):
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

    def repay_loan(self, username, amount=None):
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

    def check_bankruptcy(self, username):
        """Check if player is bankrupt (like original line 3800-3835)"""
        pdata = self.player_data[username]

        # If loan exceeds ability to pay even with forced liquidation
        total_asset_value = pdata["balance"]
        for share in SHARES:
            total_asset_value += pdata["shares"][share] * self.share_prices[share]

        if pdata["loan"] > total_asset_value:
            # Force liquidation of all shares (line 3810)
            for share in SHARES:
                if pdata["shares"][share] > 0:
                    sale_value = pdata["shares"][share] * self.share_prices[share]
                    pdata["balance"] += sale_value
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

    def end_turn(self):
        print(
            f"DEBUG: end_turn called, current_player_index={self.current_player_index}, players={len(self.players)}"
        )

        # Find next non-bankrupt player (like original line 515-520)
        attempts = 0
        while attempts < len(self.players):
            self.current_player_index = (self.current_player_index + 1) % len(
                self.players
            )
            current_player = self.players[self.current_player_index]

            # Skip bankrupt players (like original pl(p)=-1 check)
            if not self.player_data[current_player].get("bankrupt", False):
                break

            attempts += 1

        # If all players are bankrupt, end game
        if attempts >= len(self.players):
            print("DEBUG: All players bankrupt - ending game")
            return ["GAME OVER - ALL BANKRUPT"], [], True

        news_events = []
        is_round_end = False

        if self.current_player_index == 0:
            print("DEBUG: Round end detected - generating market news")
            # End of round - all players have completed their turns
            is_round_end = True
            self.round += 1
            self.last_prices = self.share_prices.copy()

            # Reset suspended shares each round (like original line 760)
            self.suspended_shares.clear()
            self.suspended_shares_rounds.clear()

            # Collect loan interest
            self.collect_loan_interest()

            self.buy_volumes = {k: 0 for k in SHARES}
            self.sell_volumes = {k: 0 for k in SHARES}

            # Reset ch counter at start of each round (like original line 700)
            self.ch = 0

            # Generate market news at the end of each round (like gosub 4000)
            # This includes price updates
            news_events = self.generate_market_news()

            print(f"DEBUG: Generated {len(news_events)} news events")
        else:
            print(
                f"DEBUG: Not round end, next player index: {self.current_player_index}"
            )

        winners = []
        millionaires = self.check_millionaires()

        # Check for bankruptcy at end of each turn (like original line 6000-6080)
        bankruptcy_messages = self.check_end_of_turn_bankruptcy()
        if bankruptcy_messages:
            news_events.extend([""] + bankruptcy_messages)

        for name in self.players:
            pdata = self.player_data[name]
            total_value = (
                pdata["balance"]
                + sum(pdata["shares"][s] * self.share_prices[s] for s in SHARES)
                - pdata["loan"]
            )
            if total_value >= self.target_value:
                winners.append(name)

        # Check for millionaires (original way to end game)
        if millionaires:
            winners.extend(millionaires)

        return winners, news_events, is_round_end

    def check_end_of_turn_bankruptcy(self):
        """Check bankruptcy at end of turn like original line 6000-6080"""
        bankruptcy_messages = []
        
        for username, pdata in self.player_data.items():
            # Calculate total value (line 6020-6030)
            total_value = pdata["balance"]
            for share in SHARES:
                total_value += pdata["shares"][share] * self.share_prices[share]
            total_value -= pdata["loan"]
            
            # If total value <= 0, player goes bankrupt (line 6040)
            if total_value <= 0:
                pdata["balance"] = 0
                pdata["loan"] = 0
                pdata["bankrupt"] = True
                bankruptcy_messages.append(f"{username}: YOU ARE BANKRUPT SIR!")
        
        return bankruptcy_messages

    def collect_loan_interest(self):
        """Collect loan interest (original line 3800-3835)"""
        for username, pdata in self.player_data.items():
            if pdata["loan"] > 0:
                interest = int(pdata["loan"] * 0.10)
                pdata["loan"] += interest

    def update_share_prices_c64(self):
        total_now = {s: 0 for s in SHARES}
        for pdata in self.player_data.values():
            for s in SHARES:
                total_now[s] += pdata["shares"][s]

        difficulty_factor = {1: 0.3, 2: 0.6, 3: 1.0, 4: 1.2}[self.difficulty]

        for i, s in enumerate(SHARES):
            p = self.share_prices[s]
            tp = self.last_totals[s]
            tn = total_now[s]
            tc = tn - tp
            r = random.randint(0, 9)
            if tc > 10:
                r -= 1
            if tc > 100:
                r -= 1
            if tc < -10:
                r += 1
            if tc < -100:
                r += 1
            if tc == 0 and random.random() < 0.3:
                r = max(0, r - 1)
            r = max(0, min(9, r))
            trinn = [5, 25, 125, 625][i]
            pc = r * trinn - 0.4 * p
            pc *= difficulty_factor
            if self.market_trend == 1:
                pc += trinn
            elif self.market_trend == -1:
                pc -= trinn
            if pc >= 0:
                pc = int(pc // trinn) * trinn
            else:
                pc = int(-(-pc // trinn)) * trinn
            if abs(pc) < trinn / 2:
                pc = 0
            if pc > trinn:
                pc = trinn
            elif pc < -trinn:
                pc = -trinn
            if self.market_trend == 1:
                pc += int(p * 0.05)
            elif self.market_trend == -1:
                pc -= int(p * 0.05)
            new_price = p + pc
            new_price = max(MIN_PRICES[s], min(self.max_prices[s], new_price))
            self.share_prices[s] = int(new_price)
        self.last_totals = total_now.copy()

    def generate_flash_news(self):
        """Generate flash news during player turn (exact copy of gosub 2600)"""
        import random

        news_events = []

        # Original: r=fnb(10):if r<5 then return
        r = random.randint(0, 9)
        if r < 5:
            return news_events

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

        # Original difficulty check: if r>4+di then 2810
        if r > 4 + self.difficulty:
            # Bonus share issues or other events (line 2810 onwards)
            r_bonus = random.randint(0, 9)
            if r_bonus == 0:
                news_events.append("MARKET VERY WEAK")
                return news_events
            elif r_bonus > 4:
                # Capital gains tax path (line 2870)
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
                share_idx = r_bonus
                if share_idx < len(SHARES):
                    share = SHARES[share_idx]
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
            share = SHARES[r_main] if r_main < len(SHARES) else random.choice(SHARES)
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

    def generate_market_news(self):
        """Generate market news at end of round (exact copy of gosub 4000)"""
        import random
        import traceback

        print(f"DEBUG: generate_market_news called for round {self.round}")  # Debug
        print("DEBUG: Call stack:")
        traceback.print_stack()

        news_events = []
        news_events.append("=== MARKET NEWS ===")

        # Reset totals for each share (line 4000-4010)
        current_totals = {share: 0 for share in SHARES}

        # Calculate current share totals for all players (line 4060)
        for share in SHARES:
            for player in self.player_data.values():
                current_totals[share] += player["shares"][share]

        # Process each share (line 4030)
        for i, share in enumerate(SHARES):
            r = random.randint(0, 9)

            # Check for special "nasty" events (gosub4500)
            if r == 0:
                nasty_news = self.generate_nasty_events(i, share)
                if nasty_news:
                    news_events.extend(nasty_news)
                    continue

            # Skip if market suspended (line 4040)
            if share in self.suspended_shares:
                news_events.append(f"{share} DEALINGS SUSPENDED")
                continue

            # Calculate price changes based on trading volume (line 4060-4110)
            tc = current_totals[share] - self.last_totals[share]

            # Adjust random based on volume changes (line 4080)
            if tc > 10:
                r -= 1
            if tc > 100:
                r -= 1
            if tc < -10:
                r += 1
            if tc < -100:
                r += 1

            # Keep r in bounds (line 4090-4100)
            if r < 0:
                r = 0
            if r > 9:
                r = 9

            # Calculate price change (line 4110)
            # Original: pc=r*(5^(i-1))-0.4*p(i)
            base_change = r * (5**i)  # 5^(i-1) in BASIC is 5^i in 0-based
            price_adjustment = 0.4 * self.share_prices[share]
            pc = base_change - price_adjustment
            pc = int(pc * 100) / 100  # Round to 2 decimals

            # Small changes become zero (line 4110)
            if abs(pc) < 0.1:
                pc = 0

            # Show price movement (line 4120-4160)
            if pc == 0:
                news_events.append(f"{share} HOLDING AT PRESENT VALUE")
            else:
                pc_str = f"{abs(pc):.2f}"
                if pc > 0:
                    news_events.append(f"{share} UP BY {pc_str}")
                else:
                    news_events.append(f"{share} DOWN BY {pc_str}")

                # Apply price change (line 4160)
                self.share_prices[share] = int(
                    max(
                        MIN_PRICES[share],
                        min(self.max_prices[share], self.share_prices[share] + pc),
                    )
                )

        # Update last totals (line 4170)
        self.last_totals = current_totals.copy()

        # Bank events (line 4180-4290)
        br = random.randint(1, 20) + random.randint(1, 21)  # fna(20)+fna(21)

        if br <= 2:  # Bank failure events
            r = random.randint(0, 9)
            if r != 0:
                news_events.append("")
                news_events.append("BANK ALMOST FAILED....NO INTEREST PAID")
            else:
                news_events.append("")
                news_events.append("BANK FAILS !!")
                # All players lose money and loans (line 4210)
                for player in self.player_data.values():
                    player["balance"] = 0
                    player["loan"] = 0
                news_events.append("A NEW BANK HAS BEEN SET UP")
        else:
            # Normal bank interest (line 4230-4280)
            news_events.append("")
            news_events.append(f"Bank interest rate {br}%")

            # Apply interest to all players (line 4260-4280)
            for player in self.player_data.values():
                # Interest on deposits
                interest_earned = int(player["balance"] * (br / 100))
                player["balance"] += interest_earned

                # Interest on loans (2% higher)
                if player["loan"] > 0:
                    loan_interest = int(player["loan"] * ((br + 2) / 100))
                    player["loan"] += loan_interest

        return news_events

    def generate_nasty_events(self, share_index, share):
        """Generate nasty market events (gosub 4500 from original)"""
        import random

        r = random.randint(0, 9)
        news_events = []

        # Don't generate if market already suspended and r in range (line 4500)
        if len(self.suspended_shares) > 0 and 1 < r < 6:
            return news_events

        news_events.append("!! NEWSFLASH !!")

        if r > 5:  # Takeover events (line 4600)
            news_events.append(f"{share} TAKEN OVER BY A CONSORTIUM")
            r = random.randint(0, 9)
            if r == 0:
                news_events.append("TAKE-OVER BID HAS FAILED !")
            else:
                payout_percent = 20 * r
                news_events.append(f"SHARES SOLD OFF AT {payout_percent}% OF VALUE")

                # Pay out shareholders and remove shares (line 4640)
                for player in self.player_data.values():
                    if share in player["shares"] and player["shares"][share] > 0:
                        payout = int(
                            0.2 * r * self.share_prices[share] * player["shares"][share]
                        )
                        player["balance"] += payout
                        player["shares"][share] = 0
        elif r > 1:  # Share suspension (line 4540)
            news_events.append(f"ALL DEALINGS IN {share} SUSPENDED")
            self.suspended_shares.add(share)
            self.suspended_shares_rounds[share] = 3
        else:  # Company bankruptcy (line 4550)
            news_events.append(f"{share} BANKRUPT...{share} SHARES WORTHLESS")

            # All shares become worthless (line 4560)
            for player in self.player_data.values():
                player["shares"][share] = 0

            # Company restarts with new price (line 4580-4590)
            news_events.append(f"{share} ARE TRADING AGAIN")
            self.share_prices[share] = 10 * (5**share_index)

        return news_events

    def calculate_final_scores(self):
        """Calculate final scores like original (line 1120)"""
        results = []

        for name in self.players:
            pdata = self.player_data[name]

            # Calculate total value (all shares sold at face value)
            total_value = pdata["balance"]
            for share in SHARES:
                total_value += pdata["shares"][share] * self.share_prices[share]
            total_value -= pdata["loan"]

            # Calculate profit made (line 1120)
            profit_made = total_value - 1000

            # Calculate score: total_value / (rounds + difficulty*5) (line 1120)
            divisor = (
                self.round + self.difficulty * 5
                if self.round > 0
                else 1 + self.difficulty * 5
            )
            score = int(total_value / divisor)

            results.append(
                {
                    "name": name,
                    "total_value": int(total_value),
                    "profit_made": int(profit_made),
                    "score": score,
                }
            )

        # Sort by total value (highest first)
        results.sort(key=lambda x: x["total_value"], reverse=True)
        return results

    def check_millionaires(self):
        """Check if any player has become a millionaire (line 6050)"""
        millionaires = []

        for name in self.players:
            pdata = self.player_data[name]
            total_value = pdata["balance"]
            for share in SHARES:
                total_value += pdata["shares"][share] * self.share_prices[share]
            total_value -= pdata["loan"]

            if total_value >= 1000000:
                millionaires.append(name)

        return millionaires
