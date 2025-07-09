# Stockmarket 1982 Clone

En webbasert klon av det klassiske C64-spillet "Stockmarket 1982" bygget med Flask og Socket.IO.

## Features

- ✅ Autentisk retro C64-terminal UI
- ✅ Multiplayer støtte med WebSocket
- ✅ Alle originale markedshendelser og newsflash
- ✅ Komplett lånesystem som i originalen
- ✅ Aktivitetslogg med fargekoding
- ✅ Poengberegning og millionær-sjekk
- ✅ "ch"-teller som påvirker nyhetssannsynlighet
- ✅ Linje-for-linje visning av nyheter

## Teknologi

- **Backend**: Python Flask + Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Kommunikasjon**: WebSocket (Socket.IO)
- **UI Style**: Retro C64-terminal design

## Installasjon

1. Klon repository:
```bash
git clone <repository-url>
cd stockmarket_clone
```

2. Opprett og aktiver virtual environment:
```bash
python -m venv venv_stockmarket
# Windows:
venv_stockmarket\Scripts\activate
# Linux/Mac:
source venv_stockmarket/bin/activate
```

3. Installer dependencies:
```bash
pip install -r requirements.txt
```

## Kjøring

1. Start serveren:
```bash
python app.py
```

2. Åpne nettleser på: `http://localhost:5000`

## Spilleregler

Spillet følger de originale reglene fra C64 "Stockmarket 1982":

- Kjøp og selg aksjer (A, B, C, D)
- Bruk lån for å kjøpe flere aksjer
- Målet er å nå $1,000,000 (eller annet satt mål)
- Markedshendelser påvirker aksjeprisene
- Newsflash kan skje under handelen
- Renter på lån trekkes automatisk

## Kommandoer

- `B <aksje> <antall>` - Kjøp aksjer (f.eks. "B A 100")
- `S <aksje> <antall>` - Selg aksjer (f.eks. "S B 50")
- `P` - Betal tilbake hele lånet
- `P <beløp>` - Betal tilbake deler av lånet
- `E` - Avslutt tur

## Prosjektstruktur

```
stockmarket_clone/
├── app.py              # Flask/SocketIO backend
├── engine.py           # Spillmotor og logikk
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Hovedside
└── static/
    ├── style.css      # Retro styling
    └── game.js        # Frontend logikk
```

## API Endpoints

- `GET /` - Main application page
- `GET /api/stock/<symbol>` - Get stock data for a symbol
- `GET /api/search/<query>` - Search for stocks

## Usage

1. **View Popular Stocks**: The main page displays popular stocks with current prices and changes
2. **Search Stocks**: Use the search bar to find specific stocks
3. **Add to Watchlist**: Click the "+" button to add stocks to your personal watchlist
4. **Manage Watchlist**: Remove stocks from your watchlist using the "×" button

## Note

This is a demo application. For production use, consider:
- Adding user authentication
- Using a proper database
- Implementing real-time data updates
- Adding more comprehensive error handling
- Using a professional stock data API
