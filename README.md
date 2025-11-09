# 📈 Stock Market Discord Bot

A powerful Discord bot for tracking stock market data using the Alpaca API. Browse stocks, view real-time prices, generate charts, and manage your portfolio directly from Discord!

## ✨ Features

### 📊 Stock Information
- **Real-time Price Data** - Get current stock prices with OHLC (Open, High, Low, Close) values
- **Historical Charts** - Generate beautiful price charts for any time period (up to 365 days)
- **Stock Comparison** - Compare multiple stocks side-by-side with normalized percentage changes
- **Market Status** - Check if the market is currently open or closed

### 🔍 Stock Discovery
- **Search Stocks** - Search for any stock by symbol or company name
- **Browse Categories** - Explore stocks organized by industry sectors
- **Popular Stocks** - View top stocks in 8 different categories:
  - 💻 Technology
  - 💰 Finance
  - 🏥 Healthcare
  - 🛒 Consumer Goods
  - ⚡ Energy
  - 🎬 Entertainment
  - 🚗 Automotive
  - ✈️ Airlines

### 💼 Portfolio Management
- **Account Overview** - View your Alpaca account balance and equity
- **Position Tracking** - Monitor all your current stock positions with P&L
- **Paper Trading** - Practice trading with virtual money

## 🚀 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/search <query>` | Search for stocks by name or symbol | `/search Apple` |
| `/browse` | Browse all stock categories | `/browse` |
| `/popular [category]` | View popular stocks by category | `/popular tech` |
| `/price <symbol>` | Get real-time stock price | `/price AAPL` |
| `/chart <symbol> [days]` | Display price chart | `/chart TSLA 90` |
| `/compare <symbols> [days]` | Compare multiple stocks | `/compare AAPL,MSFT,GOOGL` |
| `/account` | View your account information | `/account` |
| `/positions` | View your current positions | `/positions` |
| `/market` | Check market status | `/market` |
| `/help` | Show all commands | `/help` |

## 🛠️ Setup

### Prerequisites
- Python 3.8 or higher
- Discord account and server
- Alpaca API account (free paper trading account)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ca7Mau/DSA230-Discord-Bot.git
   cd DSA230-Discord-Bot
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file**
   ```bash
   touch .env
   ```

5. **Add your API keys to `.env`**
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   ALPACA_API_KEY=your_alpaca_api_key_here
   ALPACA_SECRET_KEY=your_alpaca_secret_key_here
   GUILD_ID=your_discord_server_id_here
   ```

### Getting API Keys

#### Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token
6. Enable these intents:
   - Server Members Intent
   - Message Content Intent
7. Invite the bot to your server using OAuth2 URL Generator

#### Alpaca API Keys
1. Sign up at [Alpaca](https://alpaca.markets/)
2. Create a paper trading account (free)
3. Go to your dashboard
4. Generate API keys
5. Copy the API Key and Secret Key

### Running the Bot

```bash
python3 bot.py
```

You should see:
```
✅ Alpaca clients initialized successfully
Trading_Bot#5036 is now available ✅
Synced 10 command(s)
```

## 📦 Dependencies

- `discord.py` - Discord bot framework
- `alpaca-py` - Alpaca trading API
- `matplotlib` - Chart generation
- `python-dotenv` - Environment variable management
- `certifi` - SSL certificate handling

See `requirements.txt` for complete list with versions.

## ⚠️ Important Notes

- This bot uses **paper trading** by default (virtual money)
- Market data may be delayed depending on your Alpaca plan
- Free Alpaca accounts have rate limits
- Always verify information before making real trades

## 👨‍💻 Author

**Ca7Mau**
- GitHub: [@Ca7Mau](https://github.com/Ca7Mau)
- Project: DSA230 Final Project

---

**Disclaimer**: This bot is for educational purposes only. Not financial advice. Trade at your own risk.
