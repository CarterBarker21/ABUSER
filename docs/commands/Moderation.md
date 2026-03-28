# Moderation Commands Documentation

Moderation commands help manage servers by enforcing rules and maintaining order.

---

## Table of Contents

1. [Ban Commands](#ban-commands)
2. [Kick Commands](#kick-commands)
3. [Mute Commands](#mute-commands)
4. [Message Management](#message-management)
5. [Role Management](#role-management)
6. [Channel Management](#channel-management)
7. [Lockdown Commands](#lockdown-commands)
8. [Warning System](#warning-system)

---

## Ban Commands

### `ban`

**Source**: All selfbots

Bans a member from the server.

**Parameters**:
- `member` (discord.Member): Member to ban
- `reason` (str, optional): Ban reason
- `delete_days` (int, optional): Days of messages to delete (0-7)

**Implementation**:
```python
async def ban(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await ctx.message.delete()
    
    # Check role hierarchy
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send("Cannot ban this user (higher or equal role)")
    
    if member.top_role >= ctx.author.top_role:
        return await ctx.send("You cannot ban this user")
    
    try:
        await member.ban(reason=reason, delete_message_days=1)
        
        embed = discord.Embed(title="Member Banned", color=discord.Color.red())
        embed.add_field(name="User", value=f"{member} ({member.id})")
        embed.add_field(name="Moderator", value=ctx.author)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await ctx.send("I don't have permission to ban this user")
    except Exception as e:
        await ctx.send(f"Error: {e}")
```

---

### `unban`

**Source**: selfbot.py, Discord-Selfbot

Unbans a user.

**Parameters**:
- `user_id` (str): User ID or username#discriminator
- `reason` (str, optional): Unban reason

**Implementation**:
```python
async def unban(ctx, user_id: str, *, reason: str = "No reason provided"):
    await ctx.message.delete()
    
    try:
        # Try to get ban entry
        ban_list = await ctx.guild.bans()
        
        target = None
        for ban_entry in ban_list:
            if str(ban_entry.user.id) == user_id or str(ban_entry.user) == user_id:
                target = ban_entry.user
                break
        
        if target:
            await ctx.guild.unban(target, reason=reason)
            await ctx.send(f"Unbanned {target}")
        else:
            await ctx.send("User not found in ban list")
            
    except Exception as e:
        await ctx.send(f"Error: {e}")
```

---

### `hackban` / `idban`

**Source**: Discord-Selfbot, selfbot.py

Bans a user by ID who is not in the server.

**Implementation**:
```python
async def hackban(ctx, user_id: int, *, reason: str = "No reason"):
    await ctx.message.delete()
    
    try:
        await ctx.guild.ban(discord.Object(id=user_id), reason=reason)
        await ctx.send(f"Hackbanned user ID {user_id}")
    except discord.NotFound:
        await ctx.send("Invalid user ID")
    except discord.Forbidden:
        await ctx.send("Cannot ban this user")
```

---

### `softban`

**Source**: Discord-Selfbot

Bans and immediately unbans (deletes messages).

**Implementation**:
```python
async def softban(ctx, member: discord.Member, *, reason: str = "Softban"):
    await ctx.message.delete()
    
    try:
        await member.ban(reason=reason, delete_message_days=7)
        await ctx.guild.unban(member)
        
        await ctx.send(f"Softbanned {member.mention}")
    except:
        await ctx.send("Failed to softban")
```

---

### `bans` / `banlist`

**Source**: selfbot.py

Lists all banned users.

**Implementation**:
```python
async def bans(ctx):
    await ctx.message.delete()
    
    ban_list = await ctx.guild.bans()
    
    if not ban_list:
        return await ctx.send("No banned users")
    
    entries = [f"{entry.user} ({entry.user.id})" for entry in ban_list]
    
    # Paginate if too long
    await ctx.send(f"**Banned Users ({len(ban_list)}):**\n```\n{chr(10).join(entries[:20])}\n```")
```

---

## Kick Commands

### `kick`

**Source**: All selfbots

Kicks a member from the server.

**Parameters**:
- `member` (discord.Member): Member to kick
- `reason` (str, optional): Kick reason

**Implementation**:
```python
async def kick(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    await ctx.message.delete()
    
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send("Cannot kick this user")
    
    try:
        await member.kick(reason=reason)
        
        embed = discord.Embed(title="Member Kicked", color=discord.Color.orange())
        embed.add_field(name="User", value=f"{member} ({member.id})")
        embed.add_field(name="Moderator", value=ctx.author)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await ctx.send("I don't have permission to kick this user")
```

---

## Mute Commands

### `mute`

**Source**: selfbot.py, Discord-Selfbot

Mutes a member (removes send permissions).

**Parameters**:
- `member` (discord.Member): Member to mute
- `duration` (str, optional): Duration like "10m", "2h", "1d"
- `reason` (str, optional): Mute reason

**Implementation**:
```python
import re

async def mute(ctx, member: discord.Member, duration: str = None, *, reason: str = "No reason"):
    await ctx.message.delete()
    
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send("Cannot mute this user")
    
    # Parse duration
    seconds = 0
    if duration:
        time_regex = re.compile(r"(\d+)([smhd])")
        matches = time_regex.findall(duration)
        
        for amount, unit in matches:
            if unit == 's':
                seconds += int(amount)
            elif unit == 'm':
                seconds += int(amount) * 60
            elif unit == 'h':
                seconds += int(amount) * 3600
            elif unit == 'd':
                seconds += int(amount) * 86400
    
    # Apply mute in all text channels
    muted_channels = 0
    for channel in ctx.guild.text_channels:
        try:
            perms = channel.overwrites_for(member)
            perms.send_messages = False
            await channel.set_permissions(member, overwrite=perms)
            muted_channels += 1
        except:
            pass
    
    embed = discord.Embed(title="Member Muted", color=discord.Color.orange())
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Moderator", value=ctx.author.mention)
    embed.add_field(name="Channels", value=f"{muted_channels}/{len(ctx.guild.text_channels)}")
    if seconds > 0:
        embed.add_field(name="Duration", value=duration)
    embed.add_field(name="Reason", value=reason, inline=False)
    
    await ctx.send(embed=embed)
    
    # Auto unmute after duration
    if seconds > 0:
        await asyncio.sleep(seconds)
        await ctx.invoke(unmute, member=member, reason="Auto unmute after duration")
```

---

### `unmute`

**Source**: selfbot.py, Discord-Selfbot

Unmutes a member.

**Implementation**:
```python
async def unmute(ctx, member: discord.Member, *, reason: str = "No reason"):
    await ctx.message.delete()
    
    unmuted_channels = 0
    for channel in ctx.guild.text_channels:
        try:
            perms = channel.overwrites_for(member)
            perms.send_messages = None
            await channel.set_permissions(member, overwrite=perms)
            unmuted_channels += 1
        except:
            pass
    
    await ctx.send(f"Unmuted {member.mention} in {unmuted_channels} channels")
```

---

### `tempmute` / `tmute`

Temporary mute with automatic unmute.

```python
async def tempmute(ctx, member: discord.Member, duration: str, *, reason: str = "No reason"):
    await ctx.message.delete()
    
    # Mute the user
    await ctx.invoke(mute, member=member, reason=reason)
    
    # Parse duration
    time_dict = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    unit = duration[-1]
    amount = int(duration[:-1])
    
    seconds = amount * time_dict.get(unit, 60)
    
    # Wait and unmute
    await asyncio.sleep(seconds)
    await ctx.invoke(unmute, member=member, reason="Temporary mute expired")
```

---

## Message Management

### `purge` / `clear` / `prune`

**Source**: All selfbots

Deletes messages.

**Parameters**:
- `limit` (int): Number of messages to delete
- `member` (discord.Member, optional): Only delete from this member
- `contains` (str, optional): Only delete messages containing text

**Implementation**:
```python
async def purge(ctx, limit: int, member: discord.Member = None, *, contains: str = None):
    await ctx.message.delete()
    
    def check(message):
        if member and message.author != member:
            return False
        if contains and contains.lower() not in message.content.lower():
            return False
        return True
    
    deleted = await ctx.channel.purge(limit=limit, check=check)
    
    msg = await ctx.send(f"Deleted {len(deleted)} messages")
    await asyncio.sleep(3)
    await msg.delete()
```

---

### `purgeuser` / `cleanuser`

Purge messages from a specific user.

```python
async def purgeuser(ctx, member: discord.Member, limit: int = 100):
    await ctx.message.delete()
    
    deleted = 0
    async for message in ctx.channel.history(limit=limit * 2):
        if message.author == member:
            await message.delete()
            deleted += 1
            if deleted >= limit:
                break
            await asyncio.sleep(0.5)
    
    await ctx.send(f"Deleted {deleted} messages from {member.mention}", delete_after=3)
```

---

### `purgebots` / `cleanbots`

Purge messages from bots.

```python
async def purgebots(ctx, limit: int = 100):
    await ctx.message.delete()
    
    def is_bot(m):
        return m.author.bot
    
    deleted = await ctx.channel.purge(limit=limit, check=is_bot)
    await ctx.send(f"Deleted {len(deleted)} bot messages", delete_after=3)
```

---

### `purgebetween` / `purgefrom`

Purge messages between two message IDs.

```python
async def purgebetween(ctx, start_id: int, end_id: int):
    await ctx.message.delete()
    
    try:
        start_msg = await ctx.channel.fetch_message(start_id)
        end_msg = await ctx.channel.fetch_message(end_id)
        
        deleted = 0
        async for message in ctx.channel.history(after=start_msg, before=end_msg):
            await message.delete()
            deleted += 1
            await asyncio.sleep(0.3)
        
        await ctx.send(f"Deleted {deleted} messages", delete_after=3)
    except:
        await ctx.send("Invalid message IDs")
```

---

### `nuke` / `clonechannel`

Deletes and recreates a channel (clears all messages).

```python
async def nuke(ctx, channel: discord.TextChannel = None):
    await ctx.message.delete()
    
    if channel is None:
        channel = ctx.channel
    
    # Clone the channel
    new_channel = await channel.clone()
    
    # Delete original
    await channel.delete()
    
    # Send confirmation to new channel
    await new_channel.send(f"Channel nuked by {ctx.author.mention} 💥")
```

---

## Role Management

### `addrole` / `giverole`

**Source**: selfbot.py

Adds a role to a member.

**Parameters**:
- `member` (discord.Member): Target member
- `role` (str): Role name

**Implementation**:
```python
async def addrole(ctx, member: discord.Member, *, role_name: str):
    await ctx.message.delete()
    
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
    
    if not role:
        return await ctx.send(f"Role '{role_name}' not found")
    
    if role.position >= ctx.guild.me.top_role.position:
        return await ctx.send("Cannot manage this role")
    
    try:
        await member.add_roles(role)
        await ctx.send(f"Added {role.mention} to {member.mention}")
    except:
        await ctx.send("Failed to add role")
```

---

### `removerole` / `takerole`

Removes a role from a member.

```python
async def removerole(ctx, member: discord.Member, *, role_name: str):
    await ctx.message.delete()
    
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
    
    if not role:
        return await ctx.send(f"Role '{role_name}' not found")
    
    try:
        await member.remove_roles(role)
        await ctx.send(f"Removed {role.mention} from {member.mention}")
    except:
        await ctx.send("Failed to remove role")
```

---

### `createrole` / `makerole`

**Source**: Discord-Selfbot

Creates a new role.

```python
async def createrole(ctx, color: str, *, name: str):
    await ctx.message.delete()
    
    try:
        color_int = int(color.lstrip('#'), 16)
        role = await ctx.guild.create_role(
            name=name,
            color=discord.Color(color_int)
        )
        await ctx.send(f"Created role {role.mention}")
    except:
        await ctx.send("Invalid color format. Use hex like #FF0000")
```

---

### `deleterole`

Deletes a role.

```python
async def deleterole(ctx, *, role_name: str):
    await ctx.message.delete()
    
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)
    
    if not role:
        return await ctx.send("Role not found")
    
    if role.position >= ctx.guild.me.top_role.position:
        return await ctx.send("Cannot delete this role")
    
    await role.delete()
    await ctx.send(f"Deleted role '{role_name}'")
```

---

## Channel Management

### `slowmode` / `setslowmode`

Sets slowmode delay in a channel.

```python
async def slowmode(ctx, seconds: int, channel: discord.TextChannel = None):
    await ctx.message.delete()
    
    if channel is None:
        channel = ctx.channel
    
    await channel.edit(slowmode_delay=seconds)
    
    if seconds == 0:
        await ctx.send(f"Slowmode disabled in {channel.mention}")
    else:
        await ctx.send(f"Slowmode set to {seconds} seconds in {channel.mention}")
```

---

### `renamechannel`

Renames a channel.

```python
async def renamechannel(ctx, *, new_name: str, channel: discord.TextChannel = None):
    await ctx.message.delete()
    
    if channel is None:
        channel = ctx.channel
    
    old_name = channel.name
    await channel.edit(name=new_name)
    await ctx.send(f"Renamed channel from '{old_name}' to '{new_name}'")
```

---

### `createchannel` / `createchannels`

Creates channel(s).

```python
async def createchannel(ctx, channel_type: str, *, name: str):
    await ctx.message.delete()
    
    channel_type = channel_type.lower()
    
    if channel_type == "text":
        channel = await ctx.guild.create_text_channel(name)
    elif channel_type == "voice":
        channel = await ctx.guild.create_voice_channel(name)
    elif channel_type == "category":
        channel = await ctx.guild.create_category(name)
    else:
        return await ctx.send("Invalid type. Use 'text', 'voice', or 'category'")
    
    await ctx.send(f"Created {channel_type} channel {channel.mention}")
```

---

### `deletechannel`

Deletes a channel.

```python
async def deletechannel(ctx, channel: discord.TextChannel = None):
    await ctx.message.delete()
    
    if channel is None:
        channel = ctx.channel
    
    confirm = await ctx.send(f"React to confirm deletion of {channel.mention}")
    # Wait for reaction... or just delete
    
    await channel.delete()
```

---

## Lockdown Commands

### `lockdown` / `lock`

**Source**: Discord-Selfbot

Locks a channel (prevents @everyone from sending).

**Implementation**:
```python
async def lockdown(ctx, channel: discord.TextChannel = None):
    await ctx.message.delete()
    
    if channel is None:
        channel = ctx.channel
    
    # Get @everyone role
    everyone = ctx.guild.default_role
    
    perms = channel.overwrites_for(everyone)
    perms.send_messages = False
    await channel.set_permissions(everyone, overwrite=perms)
    
    await ctx.send(f"🔒 {channel.mention} has been locked down")
```

---

### `unlock`

**Source**: Discord-Selfbot

Unlocks a channel.

```python
async def unlock(ctx, channel: discord.TextChannel = None):
    await ctx.message.delete()
    
    if channel is None:
        channel = ctx.channel
    
    everyone = ctx.guild.default_role
    
    perms = channel.overwrites_for(everyone)
    perms.send_messages = None  # Reset to default
    await channel.set_permissions(everyone, overwrite=perms)
    
    await ctx.send(f"🔓 {channel.mention} has been unlocked")
```

---

### `lockserver` / `serverlock`

Locks all channels in the server.

```python
async def lockserver(ctx):
    await ctx.message.delete()
    
    everyone = ctx.guild.default_role
    locked = 0
    
    for channel in ctx.guild.text_channels:
        try:
            perms = channel.overwrites_for(everyone)
            perms.send_messages = False
            await channel.set_permissions(everyone, overwrite=perms)
            locked += 1
        except:
            pass
    
    await ctx.send(f"🔒 Locked {locked} channels")
```

---

### `unlockserver`

Unlocks all channels.

```python
async def unlockserver(ctx):
    await ctx.message.delete()
    
    everyone = ctx.guild.default_role
    unlocked = 0
    
    for channel in ctx.guild.text_channels:
        try:
            perms = channel.overwrites_for(everyone)
            perms.send_messages = None
            await channel.set_permissions(everyone, overwrite=perms)
            unlocked += 1
        except:
            pass
    
    await ctx.send(f"🔓 Unlocked {unlocked} channels")
```

---

## Warning System

### `warn`

Issues a warning to a member.

```python
import json
import os

WARNINGS_FILE = 'data/warnings.json'

async def warn(ctx, member: discord.Member, *, reason: str):
    await ctx.message.delete()
    
    # Load warnings
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, 'r') as f:
            warnings = json.load(f)
    else:
        warnings = {}
    
    guild_id = str(ctx.guild.id)
    member_id = str(member.id)
    
    if guild_id not in warnings:
        warnings[guild_id] = {}
    
    if member_id not in warnings[guild_id]:
        warnings[guild_id][member_id] = []
    
    warning = {
        'reason': reason,
        'moderator': ctx.author.id,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    warnings[guild_id][member_id].append(warning)
    
    # Save warnings
    with open(WARNINGS_FILE, 'w') as f:
        json.dump(warnings, f)
    
    count = len(warnings[guild_id][member_id])
    
    embed = discord.Embed(title="Member Warned", color=discord.Color.orange())
    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Total Warnings", value=count)
    
    await ctx.send(embed=embed)
    
    # Optional: Auto-ban after X warnings
    if count >= 5:
        await member.ban(reason="Reached 5 warnings")
        await ctx.send(f"{member.mention} has been banned for reaching 5 warnings")
```

---

### `warnings` / `warns`

Shows warnings for a member.

```python
async def warnings(ctx, member: discord.Member = None):
    await ctx.message.delete()
    
    if member is None:
        member = ctx.author
    
    # Load warnings
    if not os.path.exists(WARNINGS_FILE):
        return await ctx.send("No warnings recorded")
    
    with open(WARNINGS_FILE, 'r') as f:
        warnings = json.load(f)
    
    guild_id = str(ctx.guild.id)
    member_id = str(member.id)
    
    user_warnings = warnings.get(guild_id, {}).get(member_id, [])
    
    if not user_warnings:
        return await ctx.send(f"{member.mention} has no warnings")
    
    embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.orange())
    
    for i, warn in enumerate(user_warnings, 1):
        moderator = ctx.guild.get_member(warn['moderator'])
        mod_name = moderator.mention if moderator else "Unknown"
        embed.add_field(
            name=f"Warning #{i}",
            value=f"Reason: {warn['reason']}\nBy: {mod_name}",
            inline=False
        )
    
    await ctx.send(embed=embed)
```

---

### `clearwarns` / `delwarn`

Clears warnings for a member.

```python
async def clearwarns(ctx, member: discord.Member):
    await ctx.message.delete()
    
    if not os.path.exists(WARNINGS_FILE):
        return await ctx.send("No warnings recorded")
    
    with open(WARNINGS_FILE, 'r') as f:
        warnings = json.load(f)
    
    guild_id = str(ctx.guild.id)
    member_id = str(member.id)
    
    if guild_id in warnings and member_id in warnings[guild_id]:
        del warnings[guild_id][member_id]
        
        with open(WARNINGS_FILE, 'w') as f:
            json.dump(warnings, f)
        
        await ctx.send(f"Cleared all warnings for {member.mention}")
    else:
        await ctx.send(f"{member.mention} has no warnings")
```

---

## References

- **selfbot.py**: Mute/unmute system
- **Discord-Selfbot**: Purge, lockdown commands
- **Exeter**: Role management
- **Alucard**: Basic moderation
