import discord
from discord import app_commands
import aiohttp
import asyncio
from datetime import datetime, timezone
from collections import Counter
import statistics
from typing import Optional, List, Dict, Tuple

# Configuration
BOT_VERSION = "v2.5.0"  # Cleaned up logs and code structure
RIOT_API_KEY = "Your Riot API Key here"
WEBHOOK_URL = "Your Discord Webhook URL here"
BOT_TOKEN = "Your Discord bot token here"

# Auto-detect region from account, but default routing for API calls
ROUTING = "europe"  # Change if needed: americas, europe, asia, sea

class BoostDetector(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        
    async def setup_hook(self):
        # Sync commands globally
        await self.tree.sync()
        print("Commands synced!")

client = BoostDetector()

@client.event
async def on_ready():
    print(f"\n{'='*50}")
    print(f"  League Boost Detector {BOT_VERSION}")
    print(f"{'='*50}")
    print(f"  Bot: {client.user}")
    print(f"  Status: ✓ READY")
    print(f"{'='*50}\n")

@client.tree.command(name="lookup", description="Check if a League of Legends player is boosted (last 100 games)")
@app_commands.describe(username="Player name with tagline (e.g., PlayerName#EUW)")
async def lookup(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    
    # Parse username and tagline
    if '#' not in username:
        await interaction.followup.send("❌ Please use format: `Username#TAG`")
        return
    
    game_name, tag_line = username.split('#', 1)
    
    try:
        await analyze_player(interaction, game_name, tag_line, username, game_count=100)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")
        print(f"Error: {e}")

@client.tree.command(name="lookup-all", description="Deep analysis of ALL ranked games from this season")
@app_commands.describe(username="Player name with tagline (e.g., PlayerName#EUW)")
async def lookup_all(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    
    # Parse username and tagline
    if '#' not in username:
        await interaction.followup.send("❌ Please use format: `Username#TAG`")
        return
    
    game_name, tag_line = username.split('#', 1)
    
    try:
        # First check if account exists
        puuid = await get_puuid(game_name, tag_line)
        if not puuid:
            await interaction.followup.send(f"❌ Account not found: {username}")
            return
        
        # Get summoner info to determine region
        summoner = await get_summoner_by_puuid(puuid)
        if not summoner:
            await interaction.followup.send(f"❌ Could not fetch summoner data for: {username}")
            return
        
        # Get rank info to determine total season games
        rank_info = await get_rank_info_by_puuid(puuid, summoner.get('region', 'euw1'))
        if not rank_info:
            await interaction.followup.send(f"❌ No ranked stats found for: {username}")
            return
        
        total_season_games = rank_info.get('wins', 0) + rank_info.get('losses', 0)
        
        if total_season_games == 0:
            await interaction.followup.send(f"❌ No ranked games played this season for: {username}")
            return
        
        # Calculate estimated time (roughly 1 second per game with rate limits)
        estimated_minutes = max(1, int(total_season_games / 30))
        
        # Send initial message with actual game count
        await interaction.followup.send(
            f"🔍 Starting deep analysis of **{username}**...\n"
            f"📊 Found **{total_season_games} ranked games** this season ({rank_info.get('wins')}W {rank_info.get('losses')}L)\n"
            f"⏳ Estimated time: {estimated_minutes}-{estimated_minutes + 2} minutes\n"
            f"*Analyzing all Solo/Duo ranked games from Season 2025...*"
        )
        
        await analyze_player(interaction, game_name, tag_line, username, game_count=total_season_games, is_deep=True, rank_info=rank_info)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")
        print(f"Error: {e}")

async def analyze_player(interaction: discord.Interaction, game_name: str, tag_line: str, username: str, game_count: int = 100, is_deep: bool = False, rank_info: Optional[Dict] = None):
    
    try:
        # Get account PUUID
        puuid = await get_puuid(game_name, tag_line)
        if not puuid:
            await interaction.followup.send(f"❌ Account not found: {username}")
            return
        
        # Get summoner info
        summoner = await get_summoner_by_puuid(puuid)
        if not summoner:
            await interaction.followup.send(f"❌ Could not fetch summoner data for: {username}")
            return
        
        # Get match history
        matches = await get_match_history(puuid, count=game_count)
        if not matches:
            await interaction.followup.send(f"❌ No ranked games found for: {username}")
            return
        
        # Get rank info if not already provided
        if not rank_info:
            rank_info = await get_rank_info_by_puuid(puuid, summoner.get('region', 'euw1'))
        
        # Analyze matches
        boost_score, indicators = analyze_boosting(matches, puuid)
        
        # Create embed
        embed = create_result_embed(username, boost_score, indicators, summoner, matches, rank_info)
        
        # Add footer for deep analysis
        if is_deep:
            embed.set_footer(text=f"League Boost Detector • Deep Analysis ({len(matches)} games)")
        
        # Send result
        if is_deep:
            await interaction.followup.send(f"✅ **Deep analysis complete for {username}**", embed=embed)
        else:
            await interaction.followup.send(embed=embed)
        
    except Exception as e:
        raise e

async def get_account_info(game_name: str, tag_line: str) -> Optional[Dict]:
    """Get full account info including rank from Riot Account API"""
    url = f"https://{ROUTING}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data
            return None

async def get_puuid(game_name: str, tag_line: str) -> Optional[str]:
    """Get PUUID from Riot ID"""
    account_data = await get_account_info(game_name, tag_line)
    if account_data:
        return account_data.get('puuid')
    return None

async def get_summoner_by_puuid(puuid: str) -> Optional[Dict]:
    """Get summoner info by PUUID - tries multiple regions"""
    regions = ["euw1", "na1", "eun1", "kr", "br1", "la1", "la2", "oc1", "tr1", "ru", "jp1", "sg2", "th2", "tw2", "vn2", "ph2"]
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    async with aiohttp.ClientSession() as session:
        for region in regions:
            try:
                # Try the standard v4 endpoint
                url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        data = await response.json()
                        data['region'] = region
                        return data
                    elif response.status == 404:
                        continue
            except Exception:
                continue
            await asyncio.sleep(0.05)
        
        return None

async def get_rank_info_by_puuid(puuid: str, region: str) -> Optional[Dict]:
    """Get FULL ranked stats using PUUID - the correct endpoint we have access to!"""
    url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                for entry in data:
                    if entry['queueType'] == 'RANKED_SOLO_5x5':
                        return entry
                if data:
                    return data[0]
            return None

async def get_rank_info_by_id(summoner_id: str, region: str) -> Optional[Dict]:
    """Legacy function - no longer used"""
    return None

async def get_rank_info(matches: List[Dict]) -> Optional[Dict]:
    """Fallback: Extract rank info from recent match data"""
    if not matches:
        return None
    
    # Calculate wins/losses from match history
    wins = sum(1 for m in matches if m.get('win', False))
    losses = len(matches) - wins
    
    return {
        'tier': 'UNKNOWN',
        'rank': '',
        'leaguePoints': 0,
        'wins': wins,
        'losses': losses,
        'queueType': 'RANKED_SOLO_5x5'
    }

async def get_match_history(puuid: str, count: int = 100) -> List[Dict]:
    """Get match history for a player - SOLO/DUO RANKED ONLY (Queue 420)"""
    headers = {"X-Riot-Token": RIOT_API_KEY}
    all_matches = []
    request_count = 0
    start_time = asyncio.get_event_loop().time()
    
    print(f"\n[FETCH] Starting to fetch up to {count} Solo/Duo ranked games...")
    
    async with aiohttp.ClientSession() as session:
        # Fetch match IDs in batches of 100
        start_index = 0
        total_fetched = 0
        
        while total_fetched < count:
            batch_size = min(100, count - total_fetched)
            url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?type=ranked&start={start_index}&count={batch_size}"
            
            request_count += 1
            
            async with session.get(url, headers=headers) as response:
                if response.status == 429:
                    print("[RATE LIMIT] Waiting 60 seconds...")
                    await asyncio.sleep(60)
                    continue
                elif response.status != 200:
                    if start_index > 0:
                        print(f"[FETCH] Stopped at {len(all_matches)} games (no more available)")
                    break
                    
                match_ids = await response.json()
                
                if not match_ids:
                    print(f"[FETCH] Reached end of match history ({len(all_matches)} games)")
                    break
                
                # Get match details for this batch
                for idx, match_id in enumerate(match_ids):
                    # Rate limit check: 90 requests per 2 minutes (conservative)
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if request_count >= 90 and elapsed < 120:
                        wait_time = 120 - elapsed
                        print(f"[RATE LIMIT] Pausing {wait_time:.0f}s to respect API limits...")
                        await asyncio.sleep(wait_time)
                        request_count = 0
                        start_time = asyncio.get_event_loop().time()
                    
                    match_url = f"https://{ROUTING}.api.riotgames.com/lol/match/v5/matches/{match_id}"
                    request_count += 1
                    
                    async with session.get(match_url, headers=headers) as match_response:
                        if match_response.status == 429:
                            print("[RATE LIMIT] Waiting 60 seconds...")
                            await asyncio.sleep(60)
                            request_count = 0
                            start_time = asyncio.get_event_loop().time()
                            # Retry this request
                            async with session.get(match_url, headers=headers) as retry_response:
                                if retry_response.status == 200:
                                    match_data = await retry_response.json()
                                else:
                                    continue
                        elif match_response.status == 200:
                            match_data = await match_response.json()
                        else:
                            continue
                        
                        queue_id = match_data['info']['queueId']
                        # ONLY Solo/Duo queue (420)
                        if queue_id == 420:
                            player_team = None
                            for participant in match_data['info']['participants']:
                                if participant['puuid'] == puuid:
                                    participant['gameEndTimestamp'] = match_data['info'].get('gameEndTimestamp', 0)
                                    participant['gameCreation'] = match_data['info'].get('gameCreation', 0)
                                    player_team = participant['teamId']
                                    
                                    # Add teammates list
                                    teammates = []
                                    for p in match_data['info']['participants']:
                                        if p['teamId'] == player_team and p['puuid'] != puuid:
                                            teammates.append({
                                                'puuid': p['puuid'],
                                                'summonerName': p.get('riotIdGameName', p.get('summonerName', 'Unknown')),
                                                'championName': p['championName']
                                            })
                                    participant['teammates'] = teammates
                                    
                                    all_matches.append(participant)
                                    break
                    
                    await asyncio.sleep(0.05)  # Small delay between requests
                    
                    # Progress update every 50 games
                    if (idx + 1) % 50 == 0:
                        print(f"[PROGRESS] Fetched {len(all_matches)} Solo/Duo games...")
                
                total_fetched += len(match_ids)
                start_index += len(match_ids)
                
                # If we got fewer than requested, we've reached the end
                if len(match_ids) < batch_size:
                    break
                
                # If we have enough Solo/Duo games, stop
                if len(all_matches) >= count:
                    break
    
    print(f"[COMPLETE] Analyzed {len(all_matches)} Solo/Duo ranked games\n")
    return all_matches

def analyze_boosting(matches: List[Dict], puuid: str) -> Tuple[int, List[str]]:
    """Analyze matches for boosting indicators"""
    if not matches:
        return 0, ["No data available"]
    
    scores = {}
    indicators = []
    
    try:
        duo_score, duo_indicator = analyze_duo_dependency(matches)
        if duo_score > 0:
            scores['duo'] = duo_score * 9
            if duo_indicator:
                indicators.append(duo_indicator)
    except Exception:
        pass
    
    try:
        champ_score, champ_indicator = analyze_champion_pool(matches)
        if champ_score > 0:
            scores['champion'] = champ_score * 8
            if champ_indicator:
                indicators.append(champ_indicator)
    except Exception:
        pass
    
    try:
        role_score, role_indicator = analyze_role_changes(matches)
        if role_score > 0:
            scores['role'] = role_score * 7
            if role_indicator:
                indicators.append(role_indicator)
    except Exception:
        pass
    
    try:
        flash_score, flash_indicator = analyze_flash_swap(matches)
        if flash_score > 0:
            scores['flash'] = flash_score * 5
            if flash_indicator:
                indicators.append(flash_indicator)
    except Exception:
        pass
    
    try:
        kda_score, kda_indicator = analyze_kda_variance(matches)
        if kda_score > 0:
            scores['kda'] = kda_score * 8
            if kda_indicator:
                indicators.append(kda_indicator)
    except Exception:
        pass
    
    try:
        skill_score, skill_indicator = analyze_skill_metrics(matches)
        if skill_score > 0:
            scores['skill'] = skill_score * 9
            if skill_indicator:
                indicators.append(skill_indicator)
    except Exception:
        pass
    
    try:
        time_score, time_indicator = analyze_play_times(matches)
        if time_score > 0:
            scores['time'] = time_score * 6
            if time_indicator:
                indicators.append(time_indicator)
    except Exception:
        pass
    
    total_weight = 9 + 8 + 7 + 5 + 8 + 9 + 6
    total_score = sum(scores.values())
    boost_percentage = int((total_score / total_weight) * 100)
    
    if not indicators:
        indicators = ["No significant boosting indicators detected"]
    
    return boost_percentage, indicators[:3]

def analyze_duo_dependency(matches: List[Dict]) -> Tuple[float, str]:
    """Analyze duo queue dependency - detects boosting through duoing"""
    if len(matches) < 10:
        return 0, None
    
    # Track each teammate across all matches
    duo_stats = {}  # {puuid: {'games': X, 'wins': Y, 'name': 'Name'}}
    
    for match in matches:
        if 'teammates' not in match:
            continue
            
        # Check each teammate
        for teammate in match['teammates']:
            teammate_puuid = teammate['puuid']
            
            if teammate_puuid not in duo_stats:
                duo_stats[teammate_puuid] = {
                    'games': 0,
                    'wins': 0,
                    'name': teammate['summonerName']
                }
            
            duo_stats[teammate_puuid]['games'] += 1
            if match.get('win', False):
                duo_stats[teammate_puuid]['wins'] += 1
    
    # Find suspicious duo partners with tiered detection
    max_score = 0
    max_indicator = None
    
    for puuid, stats in duo_stats.items():
        games = stats['games']
        wins = stats['wins']
        winrate = wins / games if games > 0 else 0
        
        score = 0
        indicator = None
        
        # Tier 1 - Obviously Boosted (100% Boost Score = 1.0)
        if games >= 8 and winrate == 1.0:
            score = 1.0
            indicator = f"🚨 OBVIOUS BOOST: {games}G with {stats['name']} (100% WR)"
        elif games >= 15 and winrate >= 0.90:
            score = 1.0
            indicator = f"🚨 OBVIOUS BOOST: {games}G with {stats['name']} ({winrate*100:.0f}% WR)"
        
        # Tier 2 - Highly Suspicious (80-90% Boost Score)
        elif games >= 10 and winrate >= 0.85:
            score = 0.9
            indicator = f"⚠️ Highly suspicious duo: {games}G with {stats['name']} ({winrate*100:.0f}% WR)"
        elif 5 <= games <= 7 and winrate == 1.0:
            score = 0.8
            indicator = f"⚠️ Perfect record duo: {games}G with {stats['name']} (100% WR)"
        
        # Tier 3 - Suspicious (60-70% Boost Score)
        elif 5 <= games <= 9 and 0.75 <= winrate < 0.85:
            score = 0.7
            indicator = f"Suspicious duo: {games}G with {stats['name']} ({winrate*100:.0f}% WR)"
        
        # Keep the highest score
        if score > max_score:
            max_score = score
            max_indicator = indicator
    
    return max_score, max_indicator

def analyze_champion_pool(matches: List[Dict]) -> Tuple[float, str]:
    """Analyze champion pool changes"""
    if len(matches) < 20:
        return 0, None
    
    old_games = matches[20:]
    recent_games = matches[:20]
    
    old_champs = Counter([m['championName'] for m in old_games])
    recent_champs = Counter([m['championName'] for m in recent_games])
    
    old_top = set([c for c, _ in old_champs.most_common(5)])
    recent_top = set([c for c, _ in recent_champs.most_common(5)])
    
    new_champs = recent_top - old_top
    
    if len(new_champs) >= 3:
        new_champ_performance = []
        for champ in new_champs:
            champ_games = [m for m in recent_games if m['championName'] == champ]
            if champ_games:
                avg_kda = statistics.mean([(m['kills'] + m['assists']) / max(1, m['deaths']) for m in champ_games])
                if avg_kda > 3.0:
                    new_champ_performance.append(champ)
        
        if len(new_champ_performance) >= 2:
            return 0.8, f"Sudden mastery of new champions: {', '.join(list(new_champ_performance)[:3])}"
    
    return 0, None

def analyze_role_changes(matches: List[Dict]) -> Tuple[float, str]:
    """Analyze role/lane changes"""
    if len(matches) < 20:
        return 0, None
    
    old_roles = [m.get('teamPosition', 'UNKNOWN') for m in matches[20:]]
    recent_roles = [m.get('teamPosition', 'UNKNOWN') for m in matches[:10]]
    
    old_main_role = Counter(old_roles).most_common(1)[0][0] if old_roles else None
    recent_main_role = Counter(recent_roles).most_common(1)[0][0] if recent_roles else None
    
    if old_main_role and recent_main_role and old_main_role != recent_main_role:
        role_change_pct = sum(1 for r in recent_roles if r != old_main_role) / len(recent_roles)
        if role_change_pct > 0.6:
            return 0.8, f"Sudden role change: {old_main_role} → {recent_main_role}"
    
    return 0, None

def analyze_flash_swap(matches: List[Dict]) -> Tuple[float, str]:
    """Analyze flash key swaps (D ↔ F)"""
    if len(matches) < 20:
        return 0, None
    
    flash_positions = []
    for match in matches[:20]:
        spell1 = match.get('summoner1Id', 0)
        spell2 = match.get('summoner2Id', 0)
        
        if spell1 == 4:
            flash_positions.append('D')
        elif spell2 == 4:
            flash_positions.append('F')
    
    if len(flash_positions) < 10:
        return 0, None
    
    first_half = flash_positions[:10]
    second_half = flash_positions[10:]
    
    first_mode = Counter(first_half).most_common(1)[0][0] if first_half else None
    second_mode = Counter(second_half).most_common(1)[0][0] if second_half else None
    
    if first_mode and second_mode and first_mode != second_mode:
        return 0.7, f"Flash key swap detected: {first_mode} → {second_mode}"
    
    return 0, None

def analyze_kda_variance(matches: List[Dict]) -> Tuple[float, str]:
    """Analyze KDA variance and sudden changes"""
    if len(matches) < 20:
        return 0, None
    
    kdas = [(m['kills'] + m['assists']) / max(1, m['deaths']) for m in matches[:20]]
    
    if len(kdas) < 10:
        return 0, None
    
    first_half = kdas[:10]
    second_half = kdas[10:]
    
    avg_first = statistics.mean(first_half)
    avg_second = statistics.mean(second_half)
    
    variance = statistics.stdev(kdas) if len(kdas) > 1 else 0
    
    if avg_first > avg_second * 1.5 and avg_first > 4.0:
        return 0.8, f"Sudden KDA drop: {avg_first:.1f} → {avg_second:.1f}"
    elif avg_second > avg_first * 1.5 and avg_second > 4.0:
        return 0.8, f"Sudden KDA spike: {avg_first:.1f} → {avg_second:.1f}"
    elif variance > 3.0:
        return 0.6, f"High KDA inconsistency (σ={variance:.1f})"
    
    return 0, None

def analyze_skill_metrics(matches: List[Dict]) -> Tuple[float, str]:
    """Analyze sudden skill metric improvements"""
    if len(matches) < 20:
        return 0, None
    
    recent = matches[:10]
    old = matches[20:30] if len(matches) >= 30 else matches[10:20]
    
    if not old:
        return 0, None
    
    recent_dpm = statistics.mean([m.get('challenges', {}).get('damagePerMinute', 0) for m in recent])
    old_dpm = statistics.mean([m.get('challenges', {}).get('damagePerMinute', 0) for m in old])
    
    recent_vision = statistics.mean([m.get('visionScore', 0) for m in recent])
    old_vision = statistics.mean([m.get('visionScore', 0) for m in old])
    
    improvements = []
    
    if recent_dpm > old_dpm * 1.4 and recent_dpm > 500:
        improvements.append(f"damage/min: {old_dpm:.0f}→{recent_dpm:.0f}")
    
    if recent_vision > old_vision * 1.5 and recent_vision > 30:
        improvements.append(f"vision: {old_vision:.0f}→{recent_vision:.0f}")
    
    if len(improvements) >= 2:
        return 0.9, f"Sudden skill spike: {', '.join(improvements)}"
    elif len(improvements) == 1:
        return 0.5, f"Skill improvement: {improvements[0]}"
    
    return 0, None

def analyze_play_times(matches: List[Dict]) -> Tuple[float, str]:
    """Analyze play time patterns"""
    if len(matches) < 20:
        return 0, None
    
    try:
        old_hours = []
        for m in matches[20:]:
            if 'gameEndTimestamp' in m:
                old_hours.append(datetime.fromtimestamp(m['gameEndTimestamp'] / 1000).hour)
            elif 'gameCreation' in m:
                old_hours.append(datetime.fromtimestamp(m['gameCreation'] / 1000).hour)
        
        recent_hours = []
        for m in matches[:20]:
            if 'gameEndTimestamp' in m:
                recent_hours.append(datetime.fromtimestamp(m['gameEndTimestamp'] / 1000).hour)
            elif 'gameCreation' in m:
                recent_hours.append(datetime.fromtimestamp(m['gameCreation'] / 1000).hour)
        
        if not old_hours or not recent_hours:
            return 0, None
        
        old_avg = statistics.mean(old_hours)
        recent_avg = statistics.mean(recent_hours)
        
        if abs(old_avg - recent_avg) > 6:
            return 0.6, f"Play time shift: {old_avg:.0f}:00 → {recent_avg:.0f}:00"
    except Exception:
        return 0, None
    
    return 0, None

def create_result_embed(username: str, boost_score: int, indicators: List[str], summoner: Dict, 
                        matches: List[Dict], rank_info: Optional[Dict]) -> discord.Embed:
    """Create Discord embed with results"""
    
    if boost_score < 30:
        color = discord.Color.green()
        verdict = "✅ Likely Clean"
    elif boost_score < 60:
        color = discord.Color.orange()
        verdict = "⚠️ Suspicious"
    else:
        color = discord.Color.red()
        verdict = "🚨 Likely Boosted"
    
    display_name = username.split('#')[0]
    
    embed = discord.Embed(
        title=f"{display_name} - {verdict}",
        description=f"**Boost Score: {boost_score}/100**",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    
    if summoner.get('profileIconId'):
        icon_url = f"https://ddragon.leagueoflegends.com/cdn/14.23.1/img/profileicon/{summoner['profileIconId']}.png"
        embed.set_thumbnail(url=icon_url)
    
    region_display = summoner.get('region', 'NA').upper()
    embed.add_field(
        name="Level/Region:",
        value=f"{summoner.get('summonerLevel', 'N/A')} / {region_display}",
        inline=True
    )
    
    last_game = matches[0] if matches else None
    if last_game:
        try:
            timestamp_val = last_game.get('gameEndTimestamp', last_game.get('gameCreation', 0))
            if timestamp_val:
                game_date = datetime.fromtimestamp(timestamp_val / 1000)
                date_str = game_date.strftime("%d %b %Y")
                time_str = game_date.strftime("%I:%M %p")
                last_game_info = f"{date_str}\nat {time_str}"
            else:
                last_game_info = "No recent games"
        except Exception:
            last_game_info = "Date unavailable"
    else:
        last_game_info = "No recent games"
    
    embed.add_field(
        name="Last Game:",
        value=last_game_info,
        inline=True
    )
    
    indicators_text = "\n".join(f"• {ind}" for ind in indicators[:3])
    embed.add_field(
        name="🔍 Main Indicators:",
        value=indicators_text if indicators_text else "• No significant indicators",
        inline=False
    )
    
    if rank_info:
        tier = rank_info.get('tier', 'UNRANKED')
        rank = rank_info.get('rank', '')
        lp = rank_info.get('leaguePoints', 0)
        wins = rank_info.get('wins', 0)
        losses = rank_info.get('losses', 0)
        total = wins + losses
        winrate = int((wins / total * 100)) if total > 0 else 0
        
        rank_display = f"{tier.capitalize()} {rank}"
        stats_display = f"{rank_display} / {lp}LP\n{wins}W {losses}L / {winrate}% WR"
    else:
        stats_display = "No ranked stats available"
    
    embed.add_field(
        name="Ranked Stats:",
        value=stats_display,
        inline=False
    )
    
    embed.set_footer(text="League Boost Detector")
    
    return embed

async def send_to_webhook(embed: discord.Embed):
    """Send result to Discord webhook"""
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(WEBHOOK_URL, session=session)
        try:
            await webhook.send(embed=embed)
        except Exception as e:
            print(f"Failed to send to webhook: {e}")

client.run(BOT_TOKEN)
