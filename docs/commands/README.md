# ABUSER Command Documentation

This directory contains comprehensive documentation for all command categories implemented in the ABUSER Discord selfbot framework.

## Available Documentation

### [🔥 Nuke.md](Nuke.md)
**Server Destruction Commands**

Complete documentation for destructive commands including:
- `destroy` / `nuke` - Total server annihilation
- `massban` / `masskick` - Mass member removal
- `delchannels` / `delroles` - Bulk deletion commands
- `spamchannels` / `massrole` - Mass creation spam
- `antinuke` protection system
- Rate limiting and safety considerations

**Warning**: These commands can permanently damage Discord servers. Use with extreme caution.

---

### [📧 MassDM.md](MassDM.md)
**Mass Direct Message Commands**

Documentation for DM automation:
- `dmall` - DM all server members
- `dmall_global` - DM across all servers
- `dmfriends` - DM all friends
- Embed support for rich messages
- Progress tracking and rate limiting
- Risk assessment and detection avoidance

**Warning**: Mass DMing violates Discord ToS and carries high ban risk.

---

### [🛠️ Utility.md](Utility.md)
**Utility & Information Commands**

Essential utility commands:
- `ping` / `uptime` / `stats` - Bot status
- `whois` / `userinfo` - User information
- `serverinfo` / `guildinfo` - Server details
- `avatar` / `guildicon` - Image retrieval
- `tokeninfo` - Token analysis
- `playing` / `streaming` - Status management
- `google` / `youtube` / `urban` - Search commands
- `calc` / `geoip` / `weather` - Utility tools

---

### [🎮 Fun.md](Fun.md)
**Entertainment Commands**

Fun and games:
- `8ball` / `minesweeper` / `slot` / `dice` - Games
- `ascii` / `reverse` / `leet` / `tiny` - Text manipulation
- `airplane` / `abc` / `count` - Animations
- `magik` / `deepfry` / `tweet` / `meme` - Image generation
- `dick` / `hack` / `nitro` - Meme commands
- `cat` / `dog` / `fox` / `joke` - Random content
- NSFW command documentation

---

### [🛡️ Moderation.md](Moderation.md)
**Moderation Commands**

Server management tools:
- `ban` / `unban` / `kick` / `softban` - Member discipline
- `mute` / `unmute` / `tempmute` - Silence members
- `purge` / `nuke` - Message cleanup
- `addrole` / `removerole` - Role management
- `lockdown` / `unlock` - Channel lockdown
- `warn` / `warnings` / `clearwarns` - Warning system

---

## Implementation Notes

### Command Structure

All commands follow this pattern:

```python
@bot.command(aliases=['alias1', 'alias2'])
async def command_name(ctx, param1: type = default, *, param2: str):
    """
    Command description.
    
    Usage: prefixcommand <required> [optional]
    """
    await ctx.message.delete()  # Selfbot stealth
    
    try:
        # Command logic
        await ctx.send("Result")
    except discord.Forbidden:
        await ctx.send("Missing permissions")
    except Exception as e:
        await ctx.send(f"Error: {e}")
```

### Rate Limiting

Always implement delays for bulk operations:

```python
# Recommended delays
BAN_DELAY = 1.5      # Between bans
KICK_DELAY = 1.0     # Between kicks  
DELETE_DELAY = 0.5   # Between deletions
CREATE_DELAY = 0.3   # Between creations
DM_DELAY = (3, 6)    # Between DMs (random range)
```

### Error Handling

Standard error handling pattern:

```python
try:
    await operation()
except discord.Forbidden:
    # Missing permissions
    pass
except discord.HTTPException as e:
    # Rate limited or API error
    if e.status == 429:
        await asyncio.sleep(e.retry_after)
except Exception as e:
    # Unexpected error
    print(f"Error: {e}")
```

### Permission Checks

Always check permissions before operations:

```python
def can_manage(ctx, member):
    """Check if we can manage a member"""
    return (ctx.guild.me.top_role > member.top_role and 
            ctx.guild.me.guild_permissions.administrator)

def has_perm(ctx, permission):
    """Check if bot has a permission"""
    return getattr(ctx.guild.me.guild_permissions, permission, False)
```

---

## Source References

Commands documented from:

1. **Alucard Selfbot** (`Main.py`)
   - 1902 lines of comprehensive commands
   - Categories: Nuke, Fun, Utility, NSFW

2. **Exeter Selfbot** (`exeter.py`)
   - 140+ commands
   - Advanced anti-nuke system
   - Image manipulation commands

3. **Karuma** (`karuma.py`)
   - Menu-driven CLI interface
   - Nuke and Mass DM focus

4. **selfbot.py** (`main.py`)
   - Clean command structure
   - Good moderation examples

5. **Discord-Selfbot** (`appuselfbot.py` + cogs)
   - 150+ commands
   - Modular cog architecture
   - Extensive utility commands

6. **SharpBot** (Node.js)
   - JavaScript implementation reference
   - Good text manipulation commands

7. **Zero-Attacker** (`nuke-bot/`)
   - Pure destruction focus
   - CLI-based operation

---

## Adding New Commands

To add a new command to ABUSER:

1. Choose appropriate category file
2. Follow existing documentation format
3. Include:
   - Command name and aliases
   - Parameter descriptions
   - Full implementation code
   - Error handling examples
   - Usage examples

4. Update this README if adding new category

---

## Safety Warnings

### ⚠️ High Risk Commands

| Command | Risk | Consequence |
|---------|------|-------------|
| `destroy` / `nuke` | ★★★★★ | Permanent server damage |
| `massban` | ★★★★☆ | Account termination |
| `dmall` | ★★★★★ | Immediate ban likely |
| `masskick` | ★★★★☆ | Rate limit & reports |
| `tokenfuck` | ★★★★★ | Account disable |

### Best Practices

1. **Test on private servers only**
2. **Use delays to avoid rate limits**
3. **Check permissions before operations**
4. **Keep backups of important data**
5. **Use alt accounts for testing**
6. **Never use on servers you don't own**

---

## License Notice

These commands are documented for educational purposes. Using selfbots violates Discord's Terms of Service and may result in account termination. Use at your own risk.

---

*Documentation generated from analysis of 10+ open-source Discord selfbot projects.*
