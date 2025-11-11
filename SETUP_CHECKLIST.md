# 🚀 Quick Setup Checklist

Follow this checklist to get your bot running in 5 minutes!

## ☐ Step 1: Get Riot API Key
- [ ] Go to https://developer.riotgames.com/
- [ ] Sign in with your League account
- [ ] Click "REGENERATE API KEY" (yellow button)
- [ ] Copy the key (starts with RGAPI-)
- [ ] ⚠️ Remember: Dev keys expire in 24 hours!

## ☐ Step 2: Create Discord Bot
- [ ] Go to https://discord.com/developers/applications
- [ ] Click "New Application" (top right)
- [ ] Name it (e.g., "BoostBuster")
- [ ] Go to "Bot" tab on left
- [ ] Click "Add Bot"
- [ ] Click "Reset Token" and copy it
- [ ] Scroll down and enable these intents (if needed):
  - [ ] Message Content Intent (optional)

## ☐ Step 3: Get Bot Invite Link
- [ ] Still in Discord Developer Portal
- [ ] Click "OAuth2" > "URL Generator" (left sidebar)
- [ ] Select scopes:
  - [ ] `bot`
  - [ ] `applications.commands`
- [ ] Select permissions:
  - [ ] Send Messages
  - [ ] Embed Links
  - [ ] Use Slash Commands
- [ ] Copy the generated URL at bottom
- [ ] Paste in browser and invite to your server

## ☐ Step 4: Configure Bot
- [ ] Open `bot.py` in a text editor
- [ ] Find these lines (around line 10-13):
  ```python
  RIOT_API_KEY = "RGAPI-..."
  WEBHOOK_URL = "https://..."  # Optional
  BOT_TOKEN = "MTQz..."
  ROUTING = "europe"  # Change if needed
  ```
- [ ] Replace with your actual values
- [ ] Save the file

## ☐ Step 5: Install Python Packages
- [ ] Open terminal/command prompt
- [ ] Navigate to bot folder: `cd /path/to/boostbuster`
- [ ] Run: `pip install discord.py aiohttp`
- [ ] Wait for installation to complete

## ☐ Step 6: Run the Bot
- [ ] In terminal, run: `python bot.py`
- [ ] You should see:
  ```
  ==================================================
    League Boost Detector v2.5.0
  ==================================================
    Bot: YourBot#1234
    Status: ✓ READY
  ==================================================
  ```
- [ ] If you see this, it's working! 🎉

## ☐ Step 7: Test It!
- [ ] Go to Discord
- [ ] In a channel where the bot is, type: `/lookup`
- [ ] You should see the command appear
- [ ] Type a League username: `/lookup Faker#KR1`
- [ ] Wait for results!

---

## 🆘 Common Issues

### "No module named 'discord'"
**Fix:** Run `pip install discord.py aiohttp`

### "401 Unauthorized" or "403 Forbidden"
**Fix:** Your Riot API key is invalid or expired. Get a new one.

### Bot appears offline in Discord
**Fix:** Check your bot token is correct in `bot.py`

### Commands don't show up
**Fix:** 
1. Make sure bot has "applications.commands" permission
2. Wait a few minutes (commands can take time to sync)
3. Try kicking and re-inviting the bot

### "Rate limit hit"
**Fix:** This is normal! The bot will automatically wait and continue.

---

## ✅ You're Done!

Your bot should now be working! Try these commands:

- `/lookup Username#TAG` - Quick scan (100 games)
- `/lookup-all Username#TAG` - Deep scan (all season games)

---

## 📝 Daily Maintenance

**If using Development API Key:**
- Your key expires every 24 hours
- Go to https://developer.riotgames.com/
- Click "REGENERATE API KEY"
- Update `RIOT_API_KEY` in `bot.py`
- Restart bot

**Or apply for Production Key:**
- Won't expire
- Apply at https://developer.riotgames.com/
- Fill out application form
- Usually approved in 1-2 weeks
