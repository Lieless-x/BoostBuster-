# 🔍 BoostBuster

**A Discord bot that analyzes League of Legends ranked accounts for boosting indicators**

BoostBuster uses advanced pattern detection to identify suspicious player behavior across multiple metrics including duo dependency, champion pool changes, role swaps, KDA variance, and more.

---

## ✨ Features

- **Quick Scan** (`/lookup`) - Analyze last 100 ranked games in seconds
- **Deep Analysis** (`/lookup-all`) - Comprehensive scan of ALL ranked games from current season
- **Multi-Factor Detection** - 7 different boosting indicators analyzed
- **Smart Scoring** - 0-100 boost score with weighted algorithm
- **Beautiful Embeds** - Clean Discord embeds with player stats and verdict
- **Rate-Limited** - Respects Riot API rate limits automatically
- **Region Auto-Detection** - Works with all League regions

---

## 🎯 Detection Methods

BoostBuster analyzes the following indicators:

| Indicator | Weight | Description |
|-----------|--------|-------------|
| **Duo Dependency** | 9/10 | Detects suspicious duo-queue patterns (high winrate with specific players) |
| **Skill Metrics** | 9/10 | Sudden improvements in damage/min, vision score, etc. |
| **Champion Pool** | 8/10 | Sudden mastery of new champions |
| **KDA Variance** | 8/10 | Dramatic KDA changes or inconsistency |
| **Role Changes** | 7/10 | Sudden role/lane swaps |
| **Play Time Shifts** | 6/10 | Major changes in playing hours |
| **Flash Key Swap** | 5/10 | Flash position changes (D ↔ F) |

---

## 📋 Requirements

### Prerequisites
- **Python 3.8+**
- **Riot Games API Key** (Personal or Production)
- **Discord Bot Token**
- **Discord Webhook URL** (optional, for logging)

### Python Packages
```
discord.py >= 2.0
aiohttp
```

---

## 🚀 Setup Guide

### 1. Get Your Riot API Key

1. Go to [Riot Developer Portal](https://developer.riotgames.com/)
2. Sign in with your League account
3. Generate a **Development API Key** (expires every 24h) or apply for **Production Key**
4. Copy your API key

> ⚠️ **Development keys expire every 24 hours** - You'll need to regenerate and update the bot daily, or apply for a production key.

### 2. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** and give it a name
3. Go to **"Bot"** tab → Click **"Add Bot"**
4. Under **Token**, click **"Reset Token"** and copy it
5. Enable these **Privileged Gateway Intents**:
   - Message Content Intent *(optional)*
6. Go to **"OAuth2"** → **"URL Generator"**
7. Select scopes: `bot`, `applications.commands`
8. Select permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
9. Copy the generated URL and invite bot to your server

### 3. Create Discord Webhook (Optional)

1. Go to your Discord server settings
2. **Integrations** → **Webhooks** → **Create Webhook**
3. Choose channel for bot logs
4. Copy webhook URL

### 4. Configure the Bot

Open `bot.py` and update these values:

```python
# Configuration
RIOT_API_KEY = "RGAPI-your-key-here"
WEBHOOK_URL = "https://discord.com/api/webhooks/your-webhook-url"  # Optional
BOT_TOKEN = "your-discord-bot-token-here"
ROUTING = "europe"  # Change based on your region
```

#### Region Routing Options:
- `americas` - North America, Brazil, Latin America
- `europe` - Europe West, Europe Nordic & East, Turkey, Russia
- `asia` - Korea, Japan
- `sea` - Southeast Asia (Singapore, Thailand, Taiwan, Vietnam, Philippines, Oceania)

### 5. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install required packages
pip install discord.py aiohttp
```

### 6. Run the Bot

```bash
python bot.py
```

You should see:
```
==================================================
  League Boost Detector v2.5.0
==================================================
  Bot: YourBot#1234
  Status: ✓ READY
==================================================
```

---

## 💻 Usage

### Commands

#### `/lookup <Username#TAG>`
Quick analysis of the last 100 ranked games.

**Example:**
```
/lookup Faker#KR1
```

**Output:**
- Boost score (0-100)
- Top 3 suspicious indicators
- Current rank and stats
- Player profile information

---

#### `/lookup-all <Username#TAG>`
Deep analysis of ALL ranked games from the current season.

**Example:**
```
/lookup-all Faker#KR1
```

**Output:**
- Same as `/lookup` but analyzes complete season history
- More accurate detection with larger sample size
- Takes 3-5 minutes depending on total games played

---

## 🎨 Example Output

```
┌─────────────────────────────────┐
│ Faker - ✅ Likely Clean          │
│ Boost Score: 15/100             │
├─────────────────────────────────┤
│ Level/Region: 487 / KR          │
│ Last Game: 11 Nov 2025          │
│                                 │
│ 🔍 Main Indicators:             │
│ • No significant indicators     │
│                                 │
│ Ranked Stats:                   │
│ Challenger 0 / 1247LP           │
│ 328W 301L / 52% WR              │
└─────────────────────────────────┘
```

---

## ⚙️ Configuration Options

### Bot Version
```python
BOT_VERSION = "v2.5.0"  # Update this when making changes
```

### API Routing Region
```python
ROUTING = "europe"  # americas, europe, asia, sea
```

### Rate Limiting
The bot automatically handles Riot API rate limits:
- 90 requests per 2 minutes (conservative)
- Auto-retry on 429 status
- Progress updates every 50 games

---

## 🐛 Troubleshooting

### "Account not found"
- Make sure you're using the correct format: `Username#TAG`
- Check that the account exists and has played ranked games
- Verify your Riot API key is valid

### "API Key Expired"
- Development keys expire every 24 hours
- Generate a new key at [developer.riotgames.com](https://developer.riotgames.com/)
- Apply for a production key for permanent access

### "Rate Limit" Messages
- This is normal for large analyses
- The bot will automatically wait and retry
- Don't restart the bot during analysis

### "No ranked games found"
- Player hasn't played Solo/Duo ranked this season
- Only Solo Queue (Ranked 5v5) games are analyzed
- Flex queue and other modes are ignored

---

## 📊 How Scoring Works

The bot uses a weighted scoring system:

1. Each indicator returns a score from 0.0 to 1.0
2. Scores are multiplied by their weight (5-9)
3. Total is converted to a percentage (0-100)

**Verdict Thresholds:**
- **0-29**: ✅ Likely Clean (Green)
- **30-59**: ⚠️ Suspicious (Orange)
- **60-100**: 🚨 Likely Boosted (Red)

---

## 🔐 Security Notes

- **Never commit your API keys or tokens to GitHub**
- Add `bot.py` to `.gitignore` after configuring
- Regenerate tokens immediately if accidentally exposed
- Use environment variables for production deployments

---

## 📝 License

This project is provided as-is for educational purposes. Riot Games API usage must comply with their [Terms of Service](https://developer.riotgames.com/terms).

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional detection algorithms
- Multi-language support
- Database integration for historical tracking
- Machine learning models for scoring

---

## 📧 Support

If you encounter issues:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Verify all requirements are installed
3. Ensure API key and tokens are valid
4. Check bot has proper Discord permissions

---

## ⚡ Quick Start (TL;DR)

```bash
# 1. Clone and install
git clone [[https://github.com/Lieless-x/BoostBuster-/](https://github.com/Lieless-x/BoostBuster-/)](https://github.com/Lieless-x/BoostBuster-/)
cd boostbuster
pip install discord.py aiohttp

# 2. Edit bot.py - add your keys
# RIOT_API_KEY = "your-key"
# BOT_TOKEN = "your-token"

# 3. Run
python bot.py

# 4. Use in Discord
/lookup Username#TAG
```

---

**Made with ❤️ for the League community**
