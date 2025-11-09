import os
import certifi

# Ensure the Python SSL layer uses the certifi CA bundle (fixes macOS "unable to get local issuer" errors)
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import discord
from discord.ext import commands
import io
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus

from dotenv import load_dotenv

# Load tokens
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
GUILD_ID = os.getenv("GUILD_ID")

# Initialize Alpaca clients
try:
    alpaca_data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    alpaca_trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
    print("✅ Alpaca clients initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Alpaca clients: {e}")
    alpaca_data_client = None
    alpaca_trading_client = None

# Discord setup
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} is now available ✅")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# ==================== STOCK COMMANDS ====================

@bot.tree.command(name="price", description="Get the latest price of a stock")
async def get_price(interaction: discord.Interaction, symbol: str):
    """Get the latest stock price"""
    await interaction.response.defer()
    
    try:
        symbol = symbol.upper()
        
        # Get the latest bar (1-minute data)
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=datetime.now() - timedelta(days=1)
        )
        
        bars = alpaca_data_client.get_stock_bars(request_params)
        
        if symbol in bars.data and len(bars.data[symbol]) > 0:
            latest_bar = bars.data[symbol][-1]
            
            embed = discord.Embed(
                title=f"📈 {symbol} Stock Price",
                color=discord.Color.green() if latest_bar.close >= latest_bar.open else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Price", value=f"${latest_bar.close:.2f}", inline=True)
            embed.add_field(name="Open", value=f"${latest_bar.open:.2f}", inline=True)
            embed.add_field(name="High", value=f"${latest_bar.high:.2f}", inline=True)
            embed.add_field(name="Low", value=f"${latest_bar.low:.2f}", inline=True)
            embed.add_field(name="Volume", value=f"{latest_bar.volume:,}", inline=True)
            
            change = latest_bar.close - latest_bar.open
            change_pct = (change / latest_bar.open) * 100
            embed.add_field(
                name="Change",
                value=f"{'📈' if change >= 0 else '📉'} ${change:.2f} ({change_pct:+.2f}%)",
                inline=True
            )
            
            embed.set_footer(text=f"Data from Alpaca • {latest_bar.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ Could not find data for symbol: {symbol}")
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching price: {str(e)}")


@bot.tree.command(name="chart", description="Display a stock price chart")
async def get_chart(interaction: discord.Interaction, symbol: str, days: int = 30):
    """Generate a stock price chart"""
    await interaction.response.defer()
    
    try:
        symbol = symbol.upper()
        
        if days > 365:
            days = 365
        elif days < 1:
            days = 1
        
        # Get historical data
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=datetime.now() - timedelta(days=days)
        )
        
        bars = alpaca_data_client.get_stock_bars(request_params)
        
        if symbol in bars.data and len(bars.data[symbol]) > 0:
            data = bars.data[symbol]
            dates = [bar.timestamp for bar in data]
            closes = [bar.close for bar in data]
            
            # Create the chart
            plt.figure(figsize=(12, 6))
            plt.plot(dates, closes, linewidth=2, color='#00A3E0')
            plt.fill_between(dates, closes, alpha=0.3, color='#00A3E0')
            
            min_price = min(closes)
            max_price = max(closes)
            price_range = max_price - min_price
            padding = price_range * 0.05  # 5% padding
            
            plt.ylim(min_price - padding, max_price + padding)
            
            plt.title(f'{symbol} Stock Price - Last {days} Days', fontsize=16, fontweight='bold')
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Price ($)', fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            # Calculate stats
            first_price = closes[0]
            last_price = closes[-1]
            change = last_price - first_price
            change_pct = (change / first_price) * 100
            
            embed = discord.Embed(
                title=f"📊 {symbol} Chart ({days} days)",
                color=discord.Color.green() if change >= 0 else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(name="Current Price", value=f"${last_price:.2f}", inline=True)
            embed.add_field(name="Period Change", value=f"${change:+.2f} ({change_pct:+.2f}%)", inline=True)
            embed.add_field(name="High", value=f"${max(closes):.2f}", inline=True)
            embed.add_field(name="Low", value=f"${min(closes):.2f}", inline=True)
            
            file = discord.File(buffer, filename=f"{symbol}_chart.png")
            embed.set_image(url=f"attachment://{symbol}_chart.png")
            
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(f"❌ Could not find data for symbol: {symbol}")
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error generating chart: {str(e)}")


@bot.tree.command(name="account", description="Check your Alpaca account status")
async def get_account(interaction: discord.Interaction):
    """Get account information"""
    await interaction.response.defer()
    
    try:
        account = alpaca_trading_client.get_account()
        
        embed = discord.Embed(
            title="💼 Account Information",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Equity", value=f"${float(account.equity):,.2f}", inline=True)
        embed.add_field(name="Cash", value=f"${float(account.cash):,.2f}", inline=True)
        embed.add_field(name="Buying Power", value=f"${float(account.buying_power):,.2f}", inline=True)
        
        portfolio_value = float(account.portfolio_value)
        last_equity = float(account.last_equity)
        daily_change = portfolio_value - last_equity
        daily_change_pct = (daily_change / last_equity) * 100 if last_equity != 0 else 0
        
        embed.add_field(
            name="Today's P&L",
            value=f"{'📈' if daily_change >= 0 else '📉'} ${daily_change:+,.2f} ({daily_change_pct:+.2f}%)",
            inline=False
        )
        
        embed.add_field(name="Account Status", value=account.status, inline=True)
        embed.add_field(name="Pattern Day Trader", value="Yes" if account.pattern_day_trader else "No", inline=True)
        embed.add_field(name="Trading Blocked", value="Yes" if account.trading_blocked else "No", inline=True)
        
        embed.set_footer(text="Paper Trading Account" if account.account_number.startswith('P') else "Live Trading Account")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching account info: {str(e)}")


@bot.tree.command(name="positions", description="View your current stock positions")
async def get_positions(interaction: discord.Interaction):
    """Get current positions"""
    await interaction.response.defer()
    
    try:
        positions = alpaca_trading_client.get_all_positions()
        
        if not positions:
            await interaction.followup.send("📭 You don't have any open positions.")
            return
        
        embed = discord.Embed(
            title="📊 Current Positions",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        total_value = 0
        total_pl = 0
        
        for position in positions[:10]:  # Limit to 10 positions
            qty = float(position.qty)
            current_price = float(position.current_price)
            market_value = float(position.market_value)
            unrealized_pl = float(position.unrealized_pl)
            unrealized_plpc = float(position.unrealized_plpc) * 100
            
            total_value += market_value
            total_pl += unrealized_pl
            
            field_value = (
                f"**Quantity:** {qty}\n"
                f"**Current Price:** ${current_price:.2f}\n"
                f"**Market Value:** ${market_value:,.2f}\n"
                f"**P&L:** {'📈' if unrealized_pl >= 0 else '📉'} ${unrealized_pl:+,.2f} ({unrealized_plpc:+.2f}%)"
            )
            
            embed.add_field(name=position.symbol, value=field_value, inline=True)
        
        if len(positions) > 10:
            embed.add_field(
                name="...",
                value=f"*And {len(positions) - 10} more positions*",
                inline=False
            )
        
        total_pl_pct = (total_pl / (total_value - total_pl)) * 100 if (total_value - total_pl) != 0 else 0
        embed.add_field(
            name="📊 Total",
            value=f"**Value:** ${total_value:,.2f}\n**P&L:** ${total_pl:+,.2f} ({total_pl_pct:+.2f}%)",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching positions: {str(e)}")


@bot.tree.command(name="market", description="Check if the market is open")
async def market_status(interaction: discord.Interaction):
    """Check market status"""
    await interaction.response.defer()
    
    try:
        clock = alpaca_trading_client.get_clock()
        
        embed = discord.Embed(
            title="🏦 Market Status",
            color=discord.Color.green() if clock.is_open else discord.Color.red(),
            timestamp=datetime.now()
        )
        
        status = "🟢 OPEN" if clock.is_open else "🔴 CLOSED"
        embed.add_field(name="Status", value=status, inline=False)
        
        embed.add_field(name="Current Time", value=clock.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z"), inline=True)
        embed.add_field(name="Next Open", value=clock.next_open.strftime("%Y-%m-%d %H:%M:%S %Z"), inline=True)
        embed.add_field(name="Next Close", value=clock.next_close.strftime("%Y-%m-%d %H:%M:%S %Z"), inline=True)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching market status: {str(e)}")


@bot.tree.command(name="compare", description="Compare multiple stocks")
async def compare_stocks(interaction: discord.Interaction, symbols: str, days: int = 30):
    """Compare multiple stocks on a chart"""
    await interaction.response.defer()
    
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        if len(symbol_list) > 5:
            await interaction.followup.send("❌ Please compare no more than 5 stocks at once.")
            return
        
        if days > 365:
            days = 365
        elif days < 1:
            days = 1
        
        plt.figure(figsize=(12, 6))
        
        colors = ['#00A3E0', '#FF6B6B', '#4ECDC4', '#FFD93D', '#A8E6CF']
        
        for idx, symbol in enumerate(symbol_list):
            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=datetime.now() - timedelta(days=days)
            )
            
            bars = alpaca_data_client.get_stock_bars(request_params)
            
            if symbol in bars.data and len(bars.data[symbol]) > 0:
                data = bars.data[symbol]
                dates = [bar.timestamp for bar in data]
                closes = [bar.close for bar in data]
                
                # Normalize to percentage change
                normalized = [(price / closes[0] - 1) * 100 for price in closes]
                
                plt.plot(dates, normalized, linewidth=2, label=symbol, color=colors[idx % len(colors)])
        
        plt.title(f'Stock Comparison - Last {days} Days (% Change)', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('% Change', fontsize=12)
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        embed = discord.Embed(
            title=f"📊 Stock Comparison",
            description=f"Comparing: {', '.join(symbol_list)}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        file = discord.File(buffer, filename="comparison_chart.png")
        embed.set_image(url="attachment://comparison_chart.png")
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error comparing stocks: {str(e)}")


@bot.tree.command(name="search", description="Search for stocks by symbol or name")
async def search_stocks(interaction: discord.Interaction, query: str):
    """Search for tradeable stocks"""
    await interaction.response.defer()
    
    try:
        query = query.upper().strip()
        
        # Get all active US equity assets
        search_params = GetAssetsRequest(
            asset_class=AssetClass.US_EQUITY,
            status=AssetStatus.ACTIVE
        )
        
        assets = alpaca_trading_client.get_all_assets(search_params)
        
        # Filter assets by query (symbol or name)
        matches = [
            asset for asset in assets 
            if query in asset.symbol.upper() or query in asset.name.upper()
        ]
        
        if not matches:
            await interaction.followup.send(f"❌ No stocks found matching: `{query}`")
            return
        
        # Limit to 15 results
        matches = matches[:15]
        
        embed = discord.Embed(
            title=f"🔍 Search Results for '{query}'",
            description=f"Top {len(matches)} stock{'s' if len(matches) != 1 else ''}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for asset in matches:
            tradeable = "✅" if asset.tradable else "❌"
            fractionable = "🔸" if asset.fractionable else ""
            
            value = (
                f"**Name:** {asset.name}\n"
                f"**Exchange:** {asset.exchange}\n"
                f"**Tradeable:** {tradeable} {fractionable}\n"
            )
            
            embed.add_field(name=asset.symbol, value=value, inline=True)
        
        if len(matches) == 15:
            embed.set_footer(text="Showing top 15 results \n 🔸 fractionable assest")
        else:
            embed.set_footer(text="Use /price <symbol> to check any stock")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error searching stocks: {str(e)}")


@bot.tree.command(name="popular", description="Browse popular stocks by category")
async def popular_stocks(interaction: discord.Interaction, category: str = "tech"):
    """Show popular stocks by category"""
    await interaction.response.defer()
    
    # Popular stock lists by category
    stock_categories = {
        "tech": {
            "name": "Technology Giants",
            "stocks": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMD", "INTC", "CRM", "ORCL"]
        },
        "finance": {
            "name": "Financial Services",
            "stocks": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "AXP", "SCHW", "USB"]
        },
        "healthcare": {
            "name": "Healthcare & Pharma",
            "stocks": ["JNJ", "UNH", "PFE", "ABBV", "TMO", "MRK", "ABT", "LLY", "DHR", "CVS"]
        },
        "consumer": {
            "name": "Consumer Goods",
            "stocks": ["AMZN", "WMT", "HD", "NKE", "MCD", "SBUX", "TGT", "LOW", "COST", "PG"]
        },
        "energy": {
            "name": "Energy & Oil",
            "stocks": ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "PSX", "VLO", "OXY"]
        },
        "entertainment": {
            "name": "Media & Entertainment",
            "stocks": ["DIS", "NFLX", "CMCSA", "WBD", "PARA", "EA", "TTWO", "LYV", "SPOT", "RBLX"]
        },
        "automotive": {
            "name": "Automotive",
            "stocks": ["TSLA", "F", "GM", "RIVN", "LCID", "NIO", "XPEV", "LI", "TM", "HMC"]
        },
        "airlines": {
            "name": "Airlines & Travel",
            "stocks": ["DAL", "AAL", "UAL", "LUV", "ALK", "JBLU", "SAVE", "HA", "SKYW", "ALGT"]
        }
    }
    
    category = category.lower()
    
    if category not in stock_categories:
        available = ", ".join([f"`{cat}`" for cat in stock_categories.keys()])
        await interaction.followup.send(
            f"❌ Invalid category. Available categories:\n{available}\n\n"
            f"Example: `/popular tech`"
        )
        return
    
    try:
        cat_info = stock_categories[category]
        symbols = cat_info["stocks"]
        
        embed = discord.Embed(
            title=f"⭐ Popular Stocks: {cat_info['name']}",
            description=f"Top {len(symbols)} stocks in {cat_info['name'].lower()}",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        # Get current prices for these stocks
        request_params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Minute,
            start=datetime.now() - timedelta(days=1)
        )
        
        bars = alpaca_data_client.get_stock_bars(request_params)
        
        for symbol in symbols:
            if symbol in bars.data and len(bars.data[symbol]) > 0:
                latest_bar = bars.data[symbol][-1]
                change = latest_bar.close - latest_bar.open
                change_pct = (change / latest_bar.open) * 100
                
                emoji = "📈" if change >= 0 else "📉"
                value = (
                    f"**Price:** ${latest_bar.close:.2f}\n"
                    f"**Change:** {emoji} {change_pct:+.2f}%"
                )
                
                embed.add_field(name=symbol, value=value, inline=True)
            else:
                embed.add_field(name=symbol, value="*Data unavailable*", inline=True)
        
        embed.set_footer(text=f"Use /price <symbol> for detailed info • Category: {category}")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching popular stocks: {str(e)}")


@bot.tree.command(name="browse", description="Browse all available stock categories")
async def browse_categories(interaction: discord.Interaction):
    """Show all available stock categories"""
    
    embed = discord.Embed(
        title="📂 Browse Stock Categories",
        description="Choose a category to explore popular stocks",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )
    
    categories = [
        ("💻 Tech", "`/popular tech`\nApple, Microsoft, Google, Meta, Nvidia, Tesla, AMD, Intel"),
        ("💰 Finance", "`/popular finance`\nJPMorgan, Bank of America, Wells Fargo, Goldman Sachs"),
        ("🏥 Healthcare", "`/popular healthcare`\nJohnson & Johnson, UnitedHealth, Pfizer, AbbVie"),
        ("🛒 Consumer", "`/popular consumer`\nAmazon, Walmart, Home Depot, Nike, McDonald's"),
        ("⚡ Energy", "`/popular energy`\nExxon, Chevron, ConocoPhillips, Schlumberger"),
        ("🎬 Entertainment", "`/popular entertainment`\nDisney, Netflix, Comcast, EA, Spotify"),
        ("🚗 Automotive", "`/popular automotive`\nTesla, Ford, GM, Rivian, Lucid, NIO"),
        ("✈️ Airlines", "`/popular airlines`\nDelta, American, United, Southwest"),
    ]
    
    for name, value in categories:
        embed.add_field(name=name, value=value, inline=False)
    
    embed.set_footer(text="Or use /search <query> to find specific stocks")
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Display help information"""
    embed = discord.Embed(
        title="📚 Stock Market Bot Commands",
        description="Track stocks and manage your portfolio with Alpaca API",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    commands_info = [
        ("🔍 /search <query>", "Search for stocks by symbol or name\nExample: `/search Apple` or `/search TSLA`"),
        ("📂 /browse", "Browse all available stock categories"),
        ("⭐ /popular [category]", "View popular stocks by category\nExample: `/popular tech` or `/popular finance`"),
        ("📈 /price <symbol>", "Get the latest price of a stock\nExample: `/price AAPL`"),
        ("📊 /chart <symbol> [days]", "Display a stock price chart\nExample: `/chart TSLA 60`"),
        ("📊 /compare <symbols> [days]", "Compare multiple stocks\nExample: `/compare AAPL,TSLA,MSFT 30`"),
        ("💼 /account", "View your Alpaca account information"),
        ("📊 /positions", "View your current stock positions"),
        ("🏦 /market", "Check if the stock market is open"),
        ("📚 /help", "Show this help message"),
    ]
    
    for name, value in commands_info:
        embed.add_field(name=name, value=value, inline=False)
    
    embed.set_footer(text="Powered by Alpaca API")
    
    await interaction.response.send_message(embed=embed)

bot.run(DISCORD_TOKEN)
