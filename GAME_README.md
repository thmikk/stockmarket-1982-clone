# Stockmarket 1982 - C64 Edition

A faithful recreation of the classic Commodore 64 "Stockmarket 1982" game as a modern web application with multiplayer support.

## Features

### 🎮 Authentic C64 Experience
- **Original blue C64 color scheme** with classic VT323 monospace font
- **Retro terminal interface** with authentic startup screen
- **Original game mechanics** including all market events and flash news
- **Classic command system** with both interactive and quick commands

### 💰 Complete Stock Trading System
- **Four companies**: LEAD, ZINC, TIN, and GOLD
- **Dynamic pricing** based on market events and trading volumes
- **Loan system** with automatic repayment and manual payback option
- **Market volatility** with trending effects and company-specific events

### 📰 News & Events System
- **Market News** displayed at end of each round (8-second display)
- **Flash News** during player turns (5-second display)
- **All original events** including:
  - Tax events and bonus payments
  - Share suspensions and market crashes
  - Company takeovers and bankruptcies
  - Government interventions and trade wars

### 👥 Multiplayer Support
- **Host-based lobby system** with configurable settings
- **Turn-based gameplay** with visual turn indicators
- **Real-time updates** via WebSocket connections
- **Multiple difficulty levels** (1-4)
- **Customizable win conditions** ($1M - $5M+ goals)

## How to Play

### Getting Started
1. **Enter your name** (max 15 characters)
2. **First player becomes host** and can configure:
   - Difficulty level (1-4)
   - Win goal amount (e.g., $1,000,000)
3. **Host starts the game** with START command

### Trading Commands
- **B** - Buy shares (interactive menu)
- **S** - Sell shares (interactive menu)
- **BL10** - Quick buy 10 LEAD shares
- **SG5** - Quick sell 5 GOLD shares
- **P** - Pay back loan (in sell menu)
- **Q** - Quit turn
- **H** or **HELP** - Show help screen

### Game Mechanics
- **Starting capital**: $1,000
- **Loan system**: Borrow up to 50% of your total assets
- **Auto-repayment**: Loans automatically repaid when selling shares
- **Market events**: Watch for news that affects share prices
- **Win condition**: First to reach the target amount wins

### Share Companies
- **LEAD** - Starting at $10
- **ZINC** - Starting at $50  
- **TIN** - Starting at $250
- **GOLD** - Starting at $1,250

## Technical Implementation

### Backend (Python/Flask)
- **Flask-SocketIO** for real-time multiplayer communication
- **Game Engine** with authentic C64 logic
- **Event System** with market news and flash events
- **Loan Management** with automatic and manual repayment

### Frontend (JavaScript)
- **Pure JavaScript** with Socket.IO client
- **State Management** for different game modes
- **Real-time UI updates** with proper turn management
- **Authentic C64 styling** with CSS animations

### Original C64 Code Compliance
- **Market events** based on original BASIC code lines 2600-4000
- **Price calculations** matching original algorithms
- **News generation** using authentic event triggers
- **Turn structure** identical to original game flow

## Installation & Running

### Prerequisites
- Python 3.13+
- Virtual environment support

### Setup
```bash
# Clone or download project
cd stockmarket_clone

# Activate virtual environment
venv_stockmarket\Scripts\activate  # Windows
# source venv_stockmarket/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the game
python app.py
```

### Access
- Open browser to `http://localhost:5000`
- For multiplayer, share your IP address: `http://YOUR_IP:5000`

## Game Files

- **app.py** - Flask server with SocketIO multiplayer handling
- **engine.py** - Game logic, market events, and trading mechanics
- **static/game.js** - Frontend JavaScript with C64-style interface
- **static/style.css** - Authentic C64 blue color scheme and styling
- **templates/index.html** - Main game HTML template
- **Aksjespillet.txt** - Original C64 BASIC code (reference)

## Features Implemented

✅ **Core Gameplay**
- All four companies with proper pricing
- Buy/sell mechanics with loan support
- Turn-based multiplayer system
- Win condition checking

✅ **Market Events**
- All original market news events
- Flash news during trading
- Price volatility and trending
- Company-specific events

✅ **User Interface**
- Authentic C64 terminal look
- Real-time status updates
- Two-column layout (holdings vs prices)
- Visual feedback for all actions

✅ **Multiplayer**
- Host-based lobby system
- Real-time synchronization
- Turn management
- Game state persistence

✅ **Loan System**
- Automatic loan approval for trades
- Manual loan repayment option
- Proper loan calculations
- Integration with all trading functions

## Development Notes

This recreation was built by carefully analyzing the original C64 BASIC code to ensure authentic gameplay mechanics. All market events, pricing algorithms, and game flow match the original 1982 version while adding modern multiplayer capabilities.

The game maintains the spirit of the original while providing a smooth web-based experience that can be enjoyed by multiple players simultaneously.

---

**Enjoy trading and may your portfolio prosper!** 📈
