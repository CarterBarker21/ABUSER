# Fun Commands Documentation

Fun commands add entertainment value to the selfbot with games, memes, animations, and text manipulation.

---

## Table of Contents

1. [Games](#games)
2. [Text Manipulation](#text-manipulation)
3. [Animations](#animations)
4. [Image Generation](#image-generation)
5. [Memes & Reactions](#memes--reactions)
6. [Random Generators](#random-generators)
7. [NSFW Commands](#nsfw-commands)

---

## Games

### `8ball` / `ball8`

**Source**: Alucard, Exeter, SharpBot

Magic 8-ball fortune teller.

**Parameters**:
- `question` (str): Question to ask

**Implementation**:
```python
async def ball8(ctx, *, question: str):
    await ctx.message.delete()
    
    responses = [
        'That is a resounding no',
        'It is not looking likely',
        'Too hard to tell',
        'It is quite possible',
        'That is a definite yes!',
        'Maybe',
        'There is a good chance'
    ]
    
    answer = random.choice(responses)
    
    embed = discord.Embed()
    embed.add_field(name="Question", value=question, inline=False)
    embed.add_field(name="Answer", value=answer, inline=False)
    embed.set_thumbnail(url="https://www.horoscope.com/images-US/games/game-magic-8-ball-no-text.png")
    
    await ctx.send(embed=embed)
```

---

### `minesweeper`

**Source**: Alucard, selfbot.py

Creates a Discord spoiler-tag minesweeper game.

**Parameters**:
- `size` (int): Grid size (default: 5, max: 8)

**Implementation**:
```python
async def minesweeper(ctx, size: int = 5):
    await ctx.message.delete()
    
    size = max(min(size, 8), 2)
    
    # Generate bombs
    bombs = [[random.randint(0, size - 1), random.randint(0, size - 1)] 
             for _ in range(size - 1)]
    
    # Offsets for checking adjacent cells
    m_offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), 
                 (-1, 1), (0, 1), (1, 1)]
    m_numbers = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:"]
    
    is_on_board = lambda x, y: 0 <= x < size and 0 <= y < size
    has_bomb = lambda x, y: [i for i in bombs if i[0] == x and i[1] == y]
    
    message = "**Click to play**:\n"
    
    for y in range(size):
        for x in range(size):
            tile = "||{}||".format(chr(11036))  # White square
            
            if has_bomb(x, y):
                tile = "||{}||".format(chr(128163))  # Bomb
            else:
                count = 0
                for xmod, ymod in m_offsets:
                    if is_on_board(x + xmod, y + ymod) and has_bomb(x + xmod, y + ymod):
                        count += 1
                if count != 0:
                    tile = "||{}||".format(m_numbers[count - 1])
            
            message += tile
        message += "\n"
    
    await ctx.send(message)
```

---

### `slot` / `slots`

**Source**: Alucard, Exeter

Slot machine game.

**Implementation**:
```python
async def slot(ctx):
    await ctx.message.delete()
    
    emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"
    
    a = random.choice(emojis)
    b = random.choice(emojis)
    c = random.choice(emojis)
    
    slotmachine = f"**[ {a} {b} {c} ]\n{ctx.author.name}**"
    
    if a == b == c:
        result = "All matchings, you won! 🎉"
        color = discord.Color.green()
    elif a == b or a == c or b == c:
        result = "2 in a row, you won! 🎉"
        color = discord.Color.yellow()
    else:
        result = "No match, you lost 😢"
        color = discord.Color.red()
    
    embed = discord.Embed(title="Slot Machine", 
                         description=f"{slotmachine}, {result}",
                         color=color)
    await ctx.send(embed=embed)
```

---

### `dice` / `roll`

**Source**: SharpBot, Discord-Selfbot

Rolls dice.

**Parameters**:
- `notation` (str): Dice notation (e.g., "2d6", "3d20")

**Implementation**:
```python
async def dice(ctx, notation: str = "1d6"):
    await ctx.message.delete()
    
    try:
        count, sides = map(int, notation.lower().split('d'))
        count = min(count, 20)  # Limit dice count
        
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        
        embed = discord.Embed(title=f"🎲 Rolling {notation}")
        embed.add_field(name="Rolls", value=", ".join(map(str, rolls)))
        embed.add_field(name="Total", value=str(total))
        
        await ctx.send(embed=embed)
        
    except ValueError:
        await ctx.send("Invalid notation. Use format like `2d6`")
```

---

### `rps` / `rockpaperscissors`

Rock paper scissors game.

**Implementation**:
```python
async def rps(ctx, choice: str):
    await ctx.message.delete()
    
    choices = ['rock', 'paper', 'scissors']
    bot_choice = random.choice(choices)
    user_choice = choice.lower()
    
    if user_choice not in choices:
        return await ctx.send("Choose rock, paper, or scissors")
    
    # Determine winner
    if user_choice == bot_choice:
        result = "It's a tie!"
    elif (user_choice == 'rock' and bot_choice == 'scissors') or \
         (user_choice == 'paper' and bot_choice == 'rock') or \
         (user_choice == 'scissors' and bot_choice == 'paper'):
        result = "You win! 🎉"
    else:
        result = "I win! 😁"
    
    emojis = {'rock': '🤚', 'paper': '✋', 'scissors': '✌️'}
    
    await ctx.send(f"You: {emojis[user_choice]} vs Me: {emojis[bot_choice]}\n{result}")
```

---

## Text Manipulation

### `ascii`

**Source**: Alucard, selfbot.py, SharpBot

Converts text to ASCII art.

**Parameters**:
- `text` (str): Text to convert
- `font` (str, optional): Font name

**Implementation**:
```python
async def ascii(ctx, *, text: str):
    await ctx.message.delete()
    
    # Using artii API
    r = requests.get(f'http://artii.herokuapp.com/make?text={urllib.parse.quote_plus(text)}')
    ascii_art = r.text
    
    if len(ascii_art) > 1990:
        await ctx.send("Text too long!")
    else:
        await ctx.send(f"```{ascii_art}```")
```

---

### `reverse`

**Source**: Alucard, Exeter, SharpBot

Reverses text.

**Implementation**:
```python
async def reverse(ctx, *, text: str):
    await ctx.message.delete()
    await ctx.send(text[::-1])
```

---

### `upper` / `uppercase`

**Source**: Alucard Selfbot

Converts text to uppercase.

```python
async def upper(ctx, *, text: str):
    await ctx.message.delete()
    await ctx.send(text.upper())
```

---

### `1337` / `1337speak` / `leet`

**Source**: Alucard, selfbot.py, SharpBot

Converts text to leet speak.

**Implementation**:
```python
async def leet(ctx, *, text: str):
    await ctx.message.delete()
    
    leet_map = {
        'a': '4', 'A': '4',
        'e': '3', 'E': '3',
        'i': '1', 'I': '1',
        'o': '0', 'O': '0',
        't': '7', 'T': '7',
        's': '5', 'S': '5',
        'b': '8', 'B': '8'
    }
    
    result = ''.join(leet_map.get(c, c) for c in text)
    await ctx.send(f"`{result}`")
```

---

### `space` / `spaceout`

**Source**: SharpBot, Discord-Selfbot

Adds spaces between letters.

**Parameters**:
- `amount` (int): Number of spaces (default: 1)
- `text` (str): Text to space out

**Implementation**:
```python
async def space(ctx, amount: int = 1, *, text: str):
    await ctx.message.delete()
    amount = min(amount, 15)
    spaced = (' ' * amount).join(text)
    await ctx.send(spaced)
```

---

### `clap`

**Source**: SharpBot

Adds :clap: between words with random case.

**Implementation**:
```python
async def clap(ctx, *, text: str):
    await ctx.message.delete()
    
    def randomize_case(word):
        return ''.join(random.choice([c.upper(), c.lower()]) for c in word)
    
    words = [randomize_case(w) for w in text.split()]
    result = ' :clap: '.join(words)
    await ctx.send(result)
```

---

### `tiny`

**Source**: SharpBot

Converts text to tiny Unicode letters.

```python
async def tiny(ctx, *, text: str):
    await ctx.message.delete()
    
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    tiny = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘｑʀѕᴛᴜᴠᴡхʏｚᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘｑʀѕᴛᴜᴠᴡхʏｚ"
    
    trans = str.maketrans(normal, tiny)
    await ctx.send(text.translate(trans))
```

---

### `fliptext`

**Source**: SharpBot

Flips text upside down.

```python
async def fliptext(ctx, *, text: str):
    await ctx.message.delete()
    
    flip_map = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
        "ɐqɔpǝɟƃɥᴉɾʞןɯnuodbɹsʇnʌʍxʎz∀qƆpℲפHIſʞץWNOԀQɹS┴∩ΛMXʎzƒ1Ɩεη͡٩٨60"
    )
    
    await ctx.send(text.translate(flip_map)[::-1])
```

---

### `regional` / `fanceh`

Converts text to regional indicator emojis.

```python
async def regional(ctx, *, text: str):
    await ctx.message.delete()
    
    regional_map = {
        'a': '🇦', 'b': '🇧', 'c': '🇨',
        'd': '🇩', 'e': '🇪', 'f': '🇫',
        # ... complete alphabet
    }
    
    result = ' '.join(regional_map.get(c.lower(), c) for c in text)
    await ctx.send(result)
```

---

## Animations

### `abc`

**Source**: Alucard Selfbot

Cycles through alphabet.

**Implementation**:
```python
async def abc(ctx):
    await ctx.message.delete()
    
    abc = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
           'n', 'ñ', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    
    msg = await ctx.send(abc[0])
    
    for letter in abc[1:]:
        await asyncio.sleep(2)
        await msg.edit(content=letter)
```

---

### `count` / `100`

**Source**: Exeter Selfbot

Counts to 100 with edits.

```python
async def count(ctx):
    await ctx.message.delete()
    
    msg = await ctx.send("0")
    for i in range(1, 100):
        await asyncio.sleep(1)
        await msg.edit(content=str(i))
```

---

### `airplane` / `9/11` / `911`

**Source**: selfbot.py, Exeter

9/11 attack animation.

```python
async def airplane(ctx):
    await ctx.message.delete()
    
    frames = [
        ':man_wearing_turban::airplane:\t\t\t\t:office:',
        ':man_wearing_turban:\t:airplane:\t\t\t:office:',
        ':man_wearing_turban:\t\t::airplane:\t\t:office:',
        ':man_wearing_turban:\t\t\t:airplane:\t:office:',
        ':man_wearing_turban:\t\t\t\t:airplane::office:',
        ':boom::boom::boom:'
    ]
    
    msg = await ctx.send(frames[0])
    for frame in frames[1:]:
        await asyncio.sleep(0.5)
        await msg.edit(content=frame)
```

---

### `cum` / `jerkoff`

**Source**: Exeter Selfbot

ASCII animation (NSFW).

```python
async def cum(ctx):
    await ctx.message.delete()
    
    frames = [
        "8=:fist::skin-tone-3:===D:sweat_drops:",
        "8==:fist::skin-tone-3:==D:sweat_drops:",
        "8===:fist::skin-tone-3:=D:sweat_drops:",
        "8====:fist::skin-tone-3:D:sweat_drops:",
        "8=====:fist::skin-tone-3::sweat_drops:",
        "8====:fist::skin-tone-3:D:sweat_drops:",
        "8===:fist::skin-tone-3:=D:sweat_drops:",
        "8==:fist::skin-tone-3:==D:sweat_drops:"
    ]
    
    msg = await ctx.send(frames[0])
    for _ in range(5):  # Repeat 5 times
        for frame in frames:
            await asyncio.sleep(0.5)
            await msg.edit(content=frame)
```

---

### `wizz` / `fakehack`

**Source**: Exeter Selfbot

Fake hacking animation.

```python
async def wizz(ctx):
    await ctx.message.delete()
    
    stages = [
        "`​WIZZING...`",
        "`DELETING ROLES...`",
        "`DELETING CHANNELS...`",
        "`BANNING MEMBERS...`",
        "`@everyone SERVER HAS BEEN WIZZED`"
    ]
    
    msg = await ctx.send(stages[0])
    for stage in stages[1:]:
        await asyncio.sleep(1)
        await msg.edit(content=stage)
```

---

## Image Generation

### `magik` / `distort`

**Source**: Exeter Selfbot

Distorts user avatar.

**Parameters**:
- `user` (discord.Member, optional): Target user

**Implementation**:
```python
async def magik(ctx, user: discord.Member = None):
    await ctx.message.delete()
    
    if user is None:
        user = ctx.author
    
    avatar_url = str(user.avatar.url if user.avatar else user.default_avatar.url)
    api_url = f"https://nekobot.xyz/api/imagegen?type=magik&intensity=3&image={avatar_url}"
    
    r = requests.get(api_url)
    data = r.json()
    
    embed = discord.Embed()
    embed.set_image(url=data["message"])
    await ctx.send(embed=embed)
```

---

### `deepfry` / `fry`

**Source**: Exeter Selfbot

Deep-fries an avatar.

```python
async def deepfry(ctx, user: discord.Member = None):
    await ctx.message.delete()
    
    if user is None:
        user = ctx.author
    
    avatar_url = str(user.avatar.url if user.avatar else user.default_avatar.url)
    api_url = f"https://nekobot.xyz/api/imagegen?type=deepfry&image={avatar_url}"
    
    r = requests.get(api_url)
    data = r.json()
    
    embed = discord.Embed()
    embed.set_image(url=data["message"])
    await ctx.send(embed=embed)
```

---

### `blurpify`

**Source**: Exeter Selfbot

Applies blurple filter to avatar.

```python
async def blurpify(ctx, user: discord.Member = None):
    await ctx.message.delete()
    
    if user is None:
        user = ctx.author
    
    avatar_url = str(user.avatar.url if user.avatar else user.default_avatar.url)
    api_url = f"https://nekobot.xyz/api/imagegen?type=blurpify&image={avatar_url}"
    
    r = requests.get(api_url)
    data = r.json()
    
    embed = discord.Embed()
    embed.set_image(url=data["message"])
    await ctx.send(embed=embed)
```

---

### `meme`

**Source**: SharpBot

Creates custom meme images.

**Parameters**:
- `template` (str): Meme template name
- `top_text` (str): Top text
- `bottom_text` (str): Bottom text

```python
async def meme(ctx, template: str, top: str, bottom: str):
    await ctx.message.delete()
    
    # Using meme API
    url = f"https://api.imgflip.com/caption_image"
    params = {
        'template_id': template_id,  # Need to map template names to IDs
        'username': 'username',
        'password': 'password',
        'text0': top,
        'text1': bottom
    }
    
    r = requests.post(url, data=params)
    data = r.json()
    
    if data['success']:
        await ctx.send(data['data']['url'])
    else:
        await ctx.send("Failed to create meme")
```

---

### `tweet` / `faketweet`

**Source**: Alucard Selfbot

Creates fake tweet image.

**Parameters**:
- `username` (str): Twitter username
- `text` (str): Tweet text

```python
async def tweet(ctx, username: str, *, text: str):
    await ctx.message.delete()
    
    api_url = f"https://nekobot.xyz/api/imagegen?type=tweet&username={username}&text={urllib.parse.quote_plus(text)}"
    
    r = requests.get(api_url)
    data = r.json()
    
    embed = discord.Embed()
    embed.set_image(url=data["message"])
    await ctx.send(embed=embed)
```

---

### `supreme`

**Source**: Exeter Selfbot

Creates Supreme logo.

```python
async def supreme(ctx, *, text: str):
    await ctx.message.delete()
    
    url = f"https://api.alexflipnote.dev/supreme?text={urllib.parse.quote_plus(text)}"
    
    embed = discord.Embed()
    embed.set_image(url=url)
    await ctx.send(embed=embed)
```

---

### `facts` / `fax`

**Source**: Exeter Selfbot

Creates "facts" book meme.

```python
async def facts(ctx, *, text: str):
    await ctx.message.delete()
    
    url = f"https://api.alexflipnote.dev/facts?text={urllib.parse.quote_plus(text)}"
    
    embed = discord.Embed()
    embed.set_image(url=url)
    await ctx.send(embed=embed)
```

---

## Memes & Reactions

### `dick` / `dong` / `penis`

**Source**: Alucard, Exeter, selfbot.py

Shows random "dick size".

```python
async def dick(ctx, user: discord.Member = None):
    await ctx.message.delete()
    
    if user is None:
        user = ctx.author
    
    size = random.randint(1, 15)
    dong = "=" * size
    
    embed = discord.Embed(title=f"{user.name}'s Dick Size")
    embed.description = f"8{dong}D"
    await ctx.send(embed=embed)
```

---

### `hack`

**Source**: Exeter Selfbot

Fake "hacking" user information.

```python
async def hack(ctx, user: discord.Member = None):
    await ctx.message.delete()
    
    if user is None:
        user = ctx.author
    
    # Generate fake data
    genders = ["Male", "Female", "Non-binary", "Transgender"]
    hair_colors = ["Black", "Blonde", "Brown", "Red", "White", "Grey", "Bald"]
    
    # Animation stages
    stages = [
        f"💻 Hacking {user.name}...",
        f"💾 Finding Discord login...",
        f"🔐 Found:\nEmail: {user.name}{random.randint(100,999)}@gmail.com\nPassword: {RandString(12)}",
        f"📁 Fetching DMs...",
        f"💾 Finding most common word...",
        f"✅ Injecting Trojan virus...",
        f"💾 Selling data to government...",
        f"💾 Finished hacking {user.name}"
    ]
    
    msg = await ctx.send(stages[0])
    for stage in stages[1:]:
        await asyncio.sleep(1.5)
        await msg.edit(content=f"```{stage}```")
```

---

### `token` / `faketoken`

Generates fake Discord token.

```python
async def token(ctx, user: discord.Member = None):
    await ctx.message.delete()
    
    if user is None:
        user = ctx.author
    
    # Generate fake token format
    part1 = "ODA" + random.choice(string.ascii_letters)
    part1 += ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(20))
    part2 = random.choice(string.ascii_letters).upper()
    part2 += ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))
    part3 = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(27))
    
    fake_token = f"{part1}.{part2}.{part3}"
    
    await ctx.send(f"> {user.mention}'s token is: ||{fake_token}||")
```

---

### `nitro` / `fakenitro`

**Source**: Alucard, selfbot.py

Generates fake Nitro code.

```python
async def nitro(ctx):
    await ctx.message.delete()
    
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    await ctx.send(f"https://discord.gift/{code}")
```

---

### `shoot`

**Source**: SharpBot

Shoots users with emoji.

```python
async def shoot(ctx, *users: discord.Member):
    await ctx.message.delete()
    
    if not users:
        return await ctx.send("Mention someone to shoot")
    
    mentions = ' '.join(u.mention for u in users)
    await ctx.send(f"🔫 {mentions}")
```

---

### `lenny` / `shrug` / `tableflip` / `unflip`

**Source**: Discord-Selfbot, SharpBot

Sends ASCII faces.

```python
async def lenny(ctx):
    await ctx.message.delete()
    await ctx.send('( ͡° ͜ʖ ͡°)')

async def shrug(ctx):
    await ctx.message.delete()
    await ctx.send(r'¯\_(ツ)_/¯')

async def tableflip(ctx):
    await ctx.message.delete()
    await ctx.send('(╯°□°)╯︵ ┻━┻')

async def unflip(ctx):
    await ctx.message.delete()
    await ctx.send('┬━┬ ノ( ゜-゜ノ)')
```

---

## Random Generators

### `joke` / `dadjoke`

**Source**: Alucard Selfbot

Fetches random joke.

```python
async def joke(ctx):
    await ctx.message.delete()
    
    headers = {"Accept": "application/json"}
    r = requests.get("https://icanhazdadjoke.com", headers=headers)
    data = r.json()
    
    await ctx.send(data["joke"])
```

---

### `topic` / `conversation`

**Source**: Alucard Selfbot

Gets random conversation starter.

```python
async def topic(ctx):
    await ctx.message.delete()
    
    from bs4 import BeautifulSoup
    
    r = requests.get('https://www.conversationstarters.com/generator.php')
    soup = BeautifulSoup(r.content, 'html.parser')
    topic = soup.find(id="random").text
    
    await ctx.send(topic)
```

---

### `wyr` / `wouldyourather`

Would you rather questions.

```python
async def wyr(ctx):
    await ctx.message.delete()
    
    from bs4 import BeautifulSoup
    
    r = requests.get('https://www.conversationstarters.com/wyrqlist.php')
    soup = BeautifulSoup(r.text, 'html.parser')
    
    qa = soup.find(id='qa').text
    qor = soup.find(id='qor').text
    qb = soup.find(id='qb').text
    
    embed = discord.Embed(description=f'{qa}\n{qor}\n{qb}')
    await ctx.send(embed=embed)
```

---

### `cat`

**Source**: Alucard, SharpBot

Random cat image.

```python
async def cat(ctx):
    await ctx.message.delete()
    
    api_key = config.get('cat_key')
    if api_key:
        r = requests.get(f"https://api.thecatapi.com/v1/images/search?api_key={api_key}")
    else:
        r = requests.get("https://api.thecatapi.com/v1/images/search")
    
    data = r.json()
    
    embed = discord.Embed()
    embed.set_image(url=data[0]["url"])
    await ctx.send(embed=embed)
```

---

### `dog`

**Source**: Alucard, SharpBot

Random dog image.

```python
async def dog(ctx):
    await ctx.message.delete()
    
    r = requests.get("https://dog.ceo/api/breeds/image/random")
    data = r.json()
    
    embed = discord.Embed()
    embed.set_image(url=data['message'])
    await ctx.send(embed=embed)
```

---

### `fox`

**Source**: Alucard Selfbot

Random fox image.

```python
async def fox(ctx):
    await ctx.message.delete()
    
    r = requests.get('https://randomfox.ca/floof/')
    data = r.json()
    
    embed = discord.Embed(title="Random Fox")
    embed.set_image(url=data["image"])
    await ctx.send(embed=embed)
```

---

## NSFW Commands

> ⚠️ These commands require NSFW channels and appropriate age verification.

### `hentai`

**Source**: Alucard Selfbot

Fetches random hentai image.

```python
async def hentai(ctx):
    await ctx.message.delete()
    
    if not ctx.channel.is_nsfw():
        return await ctx.send("This command only works in NSFW channels")
    
    r = requests.get("https://nekos.life/api/v2/img/Random_hentai_gif")
    data = r.json()
    
    embed = discord.Embed()
    embed.set_image(url=data['url'])
    await ctx.send(embed=embed)
```

---

### Other NSFW Commands

From Alucard Selfbot:
- `anal` - Anal content
- `blowjob` - Blowjob content
- `boobs` / `tits` - Boobs content
- `erofeet` - Erotic feet
- `feet` - Feet content
- `lesbian` - Lesbian content
- `lewdneko` - Lewd neko

All use the same nekos.life API pattern.

---

## References

- **Alucard**: Fun and image commands
- **SharpBot**: Text manipulation and memes
- **Exeter**: Animations and fake commands
- **selfbot.py**: ASCII and games
