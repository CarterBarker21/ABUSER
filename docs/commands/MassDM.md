# Mass DM Commands Documentation

> ⚠️ **WARNING**: Mass DMing is against Discord's Terms of Service and can result in immediate account termination. This documentation is for educational purposes only.

---

## Table of Contents

1. [Overview](#overview)
2. [Server Mass DM](#server-mass-dm)
3. [Global Mass DM](#global-mass-dm)
4. [DM All Friends](#dm-all-friends)
5. [Targeted DM](#targeted-dm)
6. [Advanced Features](#advanced-features)
7. [Rate Limiting](#rate-limiting)
8. [Implementation Examples](#implementation-examples)

---

## Overview

Mass DM commands allow sending direct messages to multiple users simultaneously. These are commonly used for:
- Advertising/Spam
- Server announcements
- Phishing attempts (malicious)

### Risk Assessment

| Risk Factor | Level | Description |
|-------------|-------|-------------|
| Account Ban | ★★★★★ | Almost guaranteed detection |
| Rate Limits | ★★★★☆ | Strict 3-6 second delays required |
| User Reports | ★★★★★ | High likelihood of reports |
| Token Lock | ★★★☆☆ | Possible temporary restrictions |

---

## Server Mass DM

### `dmall` / `massdm` / `dm_server`

**Source**: Alucard, Exeter, selfbot.py, Karuma

Sends a DM to all members in the current server.

**Parameters**:
- `message` (str): Message content to send
- `embed` (bool, optional): Include embed
- `delay` (float, optional): Delay between DMs (default: 3-6s)

**Implementation**:
```python
async def dmall(ctx, *, message: str):
    """Mass DM all server members"""
    await ctx.message.delete()
    
    # Get all human members (exclude bots)
    members = [m for m in ctx.guild.members if not m.bot]
    total = len(members)
    
    # Send progress message
    progress = await ctx.send(
        f"Starting DM process for `{total}` members.\n"
        f"Estimated time: `{total * 4.5:.0f}` seconds (~{total * 4.5 / 60:.1f} minutes)"
    )
    
    success = 0
    failed = 0
    
    for idx, member in enumerate(members, 1):
        # Skip self
        if member.id == ctx.bot.user.id:
            continue
            
        try:
            await member.send(message)
            success += 1
            print(f"[{idx}/{total}] Sent to {member}")
        except discord.Forbidden:
            failed += 1
            print(f"[{idx}/{total}] Cannot DM {member} (DMs disabled)")
        except discord.HTTPException as e:
            failed += 1
            print(f"[{idx}/{total}] Failed to DM {member}: {e}")
        
        # Rate limit protection
        await asyncio.sleep(random.uniform(3, 6))
    
    # Report results
    await progress.edit(content=
        f"DM process completed.\n"
        f"Successfully sent: `{success}`\n"
        f"Failed: `{failed}`"
    )
```

---

### `dmall_embed` / `massdm_embed`

**Source**: Karuma

Sends embedded messages to all server members.

**Parameters**:
- `message_type` (str): "text", "embed", or "both"
- `text_content` (str): Text message content
- `embed_title` (str): Embed title
- `embed_description` (str): Embed description
- `embed_color` (str): Hex color code

**Implementation**:
```python
async def create_embed():
    """Interactive embed builder for Mass DM"""
    embed = discord.Embed()
    
    title = input("Embed title (leave blank for none): ")
    if title:
        embed.title = title
    
    description = input("Embed description: ")
    if description:
        embed.description = description
    
    color = input("Embed color (hex without #): ")
    if color:
        try:
            embed.color = int(color, 16)
        except:
            embed.color = discord.Color.random()
    
    # Add fields
    while True:
        field_name = input("Add field? Enter name (blank to stop): ")
        if not field_name:
            break
        field_value = input("Field value: ")
        inline = input("Inline? (y/n): ").lower() == 'y'
        embed.add_field(name=field_name, value=field_value, inline=inline)
    
    return embed

async def mass_dm_users(users, message_type, text_content=None, embed_content=None):
    """Send DMs to list of users with embed support"""
    total = len(users)
    
    for idx, user in enumerate(users, 1):
        try:
            # Skip bots and self
            if user.id == bot.user.id or user.bot:
                continue
            
            if message_type == "both" and text_content and embed_content:
                await user.send(content=text_content, embed=embed_content)
            elif message_type == "text" and text_content:
                await user.send(content=text_content)
            elif message_type == "embed" and embed_content:
                await user.send(embed=embed_content)
            
            print(f"[{idx}/{total}] Sent to {user}")
        except Exception as e:
            print(f"[{idx}/{total}] Failed to send to {user}: {e}")
        
        if idx < total:
            await asyncio.sleep(random.uniform(3, 6))
```

---

## Global Mass DM

### `dmall_global` / `massdm_all` / `dm_everyone`

**Source**: Karuma

Sends DMs to ALL users the bot can see across all servers.

**Parameters**:
- `message` (str): Message content

**Warning**: Extremely high risk - will DM thousands of users.

**Implementation**:
```python
async def dmall_global(ctx, *, message: str):
    """DM all users across all guilds"""
    await ctx.message.delete()
    
    # Get unique users across all guilds
    all_users = set()
    for guild in ctx.bot.guilds:
        for member in guild.members:
            if not member.bot:
                all_users.add(member)
    
    users = list(all_users)
    total = len(users)
    
    await ctx.send(f"Starting global DM to `{total}` unique users...")
    
    success = failed = 0
    
    for user in users:
        if user.id == ctx.bot.user.id:
            continue
            
        try:
            await user.send(message)
            success += 1
        except:
            failed += 1
        
        await asyncio.sleep(random.uniform(4, 7))
    
    await ctx.send(f"Global DM complete. Success: {success}, Failed: {failed}")
```

---

## DM All Friends

### `dmfriends` / `dm_friends` / `friend_dm`

**Source**: Alucard Selfbot

Sends DMs to all friends.

**Implementation**:
```python
async def dmfriends(ctx, *, message: str):
    """DM all friends"""
    await ctx.message.delete()
    
    friends = ctx.bot.user.friends
    total = len(friends)
    
    for idx, friend in enumerate(friends, 1):
        try:
            await friend.send(message)
            print(f"[{idx}/{total}] Sent to {friend}")
        except:
            print(f"[{idx}/{total}] Failed: {friend}")
        
        await asyncio.sleep(random.uniform(3, 5))
```

---

## Targeted DM

### `dm` / `direct_message`

**Source**: Alucard, Exeter

Sends DM to specific user.

**Parameters**:
- `user` (discord.Member): User to DM
- `message` (str): Message content

**Implementation**:
```python
async def dm(ctx, user: discord.Member, *, message: str):
    """DM a specific user"""
    await ctx.message.delete()
    
    try:
        await user.send(message)
        await ctx.send(f"Message sent to {user.mention}", delete_after=3)
    except discord.Forbidden:
        await ctx.send(f"Cannot DM {user.mention} (DMs disabled)", delete_after=3)
    except Exception as e:
        await ctx.send(f"Error: {e}", delete_after=3)
```

---

## Advanced Features

### Message Rotation

Rotate through multiple messages to avoid detection:

```python
import itertools

class MassDMRotator:
    def __init__(self, messages):
        self.messages = itertools.cycle(messages)
    
    def get_next(self):
        return next(self.messages)

# Usage
rotator = MassDMRotator([
    "Check out my server! discord.gg/xxx",
    "Join our community! discord.gg/xxx", 
    "Cool server here: discord.gg/xxx"
])

for user in users:
    msg = rotator.get_next()
    await user.send(msg)
```

---

### Delay Jitter

Randomize delays to appear more human:

```python
import random

async def jittered_delay(min_delay=3.0, max_delay=6.0):
    """Random delay with jitter"""
    base = random.uniform(min_delay, max_delay)
    jitter = random.uniform(-0.5, 0.5)
    await asyncio.sleep(max(0, base + jitter))

# Usage
for user in users:
    await user.send(message)
    await jittered_delay()
```

---

### Progress Tracking

Track and report progress:

```python
class MassDMProgress:
    def __init__(self, total):
        self.total = total
        self.success = 0
        self.failed = 0
        self.blocked = 0
        self.start_time = time.time()
    
    def update(self, status):
        if status == "success":
            self.success += 1
        elif status == "blocked":
            self.blocked += 1
        else:
            self.failed += 1
    
    def get_stats(self):
        elapsed = time.time() - self.start_time
        rate = (self.success + self.failed) / elapsed if elapsed > 0 else 0
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "blocked": self.blocked,
            "elapsed": elapsed,
            "rate": rate
        }
```

---

## Rate Limiting

### Discord Rate Limits for DMs

| Action | Rate Limit | Burst |
|--------|------------|-------|
| Send DM | 5 per 5s | 5 |
| Open DM Channel | 5 per 60s | 5 |
| Group DM Create | 10 per 10s | 10 |

### Recommended Safe Limits

```python
# Conservative (safest)
CONSERVATIVE_DELAY = (5.0, 8.0)  # 5-8 seconds

# Moderate
MODERATE_DELAY = (3.5, 6.0)  # 3.5-6 seconds

# Aggressive (high risk)
AGGRESSIVE_DELAY = (2.5, 4.0)  # 2.5-4 seconds
```

### Adaptive Rate Limiting

```python
class AdaptiveRateLimiter:
    def __init__(self):
        self.base_delay = 3.0
        self.failures = 0
        self.successes = 0
    
    async def wait(self):
        """Calculate delay based on recent performance"""
        if self.failures > 3:
            # Increase delay after failures
            delay = self.base_delay * 2 + random.uniform(0, 2)
        elif self.successes > 10:
            # Can slightly decrease after consistent success
            delay = max(2.5, self.base_delay - 0.5)
        else:
            delay = self.base_delay + random.uniform(0, 2)
        
        await asyncio.sleep(delay)
    
    def report_success(self):
        self.successes += 1
        self.failures = max(0, self.failures - 1)
    
    def report_failure(self):
        self.failures += 1
        self.successes = max(0, self.successes - 1)
```

---

## Implementation Examples

### Complete Mass DM with All Features

```python
import discord
import asyncio
import random
import time
from datetime import timedelta

class MassDMManager:
    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.cancelled = False
    
    async def mass_dm_server(
        self, 
        ctx, 
        message: str,
        use_embed: bool = False,
        embed_data: dict = None,
        min_delay: float = 3.0,
        max_delay: float = 6.0,
        exclude_bots: bool = True,
        exclude_self: bool = True
    ):
        """
        Complete mass DM implementation with all features
        """
        if self.running:
            return await ctx.send("Mass DM already in progress!")
        
        self.running = True
        self.cancelled = False
        
        await ctx.message.delete()
        
        # Build member list
        members = ctx.guild.members
        if exclude_bots:
            members = [m for m in members if not m.bot]
        if exclude_self:
            members = [m for m in members if m.id != self.bot.user.id]
        
        total = len(members)
        
        # Create embed for progress
        progress_embed = discord.Embed(
            title="Mass DM Progress",
            description=f"Sending to {total} members...",
            color=discord.Color.blue()
        )
        progress_embed.add_field(name="Sent", value="0")
        progress_embed.add_field(name="Failed", value="0")
        progress_embed.add_field(name="Progress", value="0%")
        
        progress_msg = await ctx.send(embed=progress_embed)
        
        # Statistics
        stats = {"success": 0, "failed": 0, "blocked": 0}
        start_time = time.time()
        
        for idx, member in enumerate(members, 1):
            if self.cancelled:
                break
            
            # Check if user has DMs enabled by attempting to create DM channel
            try:
                dm_channel = await member.create_dm()
                
                # Prepare message
                if use_embed and embed_data:
                    embed = discord.Embed(
                        title=embed_data.get("title"),
                        description=embed_data.get("description"),
                        color=int(embed_data.get("color", "5865F2"), 16)
                    )
                    await dm_channel.send(embed=embed)
                else:
                    await dm_channel.send(message)
                
                stats["success"] += 1
                
            except discord.Forbidden:
                stats["blocked"] += 1
            except discord.HTTPException:
                stats["failed"] += 1
            except Exception as e:
                stats["failed"] += 1
                print(f"Error DMing {member}: {e}")
            
            # Update progress every 10 users
            if idx % 10 == 0:
                percent = (idx / total) * 100
                elapsed = time.time() - start_time
                eta = (elapsed / idx) * (total - idx) if idx > 0 else 0
                
                progress_embed.set_field_at(0, name="Sent", value=str(stats["success"]))
                progress_embed.set_field_at(1, name="Failed", value=str(stats["failed"] + stats["blocked"]))
                progress_embed.set_field_at(2, name="Progress", value=f"{percent:.1f}%")
                progress_embed.description = f"Processing {idx}/{total} | ETA: {timedelta(seconds=int(eta))}"
                
                await progress_msg.edit(embed=progress_embed)
            
            # Rate limit delay
            await asyncio.sleep(random.uniform(min_delay, max_delay))
        
        # Final update
        elapsed = time.time() - start_time
        progress_embed.title = "Mass DM Complete"
        progress_embed.color = discord.Color.green()
        progress_embed.description = f"Completed in {timedelta(seconds=int(elapsed))}"
        progress_embed.clear_fields()
        progress_embed.add_field(name="Success", value=str(stats["success"]), inline=True)
        progress_embed.add_field(name="Failed", value=str(stats["failed"]), inline=True)
        progress_embed.add_field(name="Blocked", value=str(stats["blocked"]), inline=True)
        
        await progress_msg.edit(embed=progress_embed)
        self.running = False
    
    def cancel(self):
        self.cancelled = True

# Command usage
@bot.command()
async def dmall(ctx, *, message: str):
    manager = MassDMManager(bot)
    await manager.mass_dm_server(ctx, message)

@bot.command()
async def canceldm(ctx):
    # Would need to track active managers
    await ctx.send("Cancelled all active mass DMs")
```

---

## References

- **Alucard**: `Main.py` lines 1255-1263
- **Karuma**: `karuma.py` lines 405-468
- **selfbot.py**: `main.py` dmall command
- **Exeter**: Similar implementation with delay customization
