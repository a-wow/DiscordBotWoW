import discord
from discord.ext import commands
import mysql.connector
from typing import Optional
import random

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', description="A Extazy WoW character information bot", intents=intents)

race_names = {
    1: 'Человек',
    2: 'Орк',
    3: 'Дворф',
    4: 'Ночной эльф',
    5: 'Нежить',
    6: 'Таурен',
    7: 'Гном',
    8: 'Тролль',
    10: 'Кровавый эльф',
    11: 'Дреней'
}

class_names = {
    1: 'Воин',
    2: 'Паладин',
    3: 'Охотник',
    4: 'Разбойник',
    5: 'Жрец',
    8: 'Маг',
    9: 'Чернокнижник',
    11: 'Друид'
}

gender_names = {
    0: 'Мужской',
    1: 'Женский'
}

DB_HOST = "HOST"
DB_USER = "USER"
DB_PASSWORD = "PASS"
DB_DATABASE = "CHARACTERS"

async def get_character_info(name: str) -> Optional[dict]:
    conn = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_DATABASE)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM characters WHERE name = '{name}';")

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return {
            'guid': row[0],
            'account': row[1],
            'name': row[2],
            'race': race_names[row[3]],
            'class': class_names[row[4]],
            'gender': gender_names[row[5]],
            'level': row[6],
            'totalkills': row[49],
            'online': row[15]
        }
    else:
        return None

async def get_online_players() -> list:
    conn = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, race, class, gender, level FROM characters WHERE online = 1;")

    online_players = []

    for row in cursor.fetchall():
        online_players.append({
            'name': row[0],
            'race': race_names[row[1]],
            'class': class_names[row[2]],
            'gender': gender_names[row[3]],
            'level': row[4]
        })

    cursor.close()
    conn.close()

    return online_players

def create_tables():
    conn = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_DATABASE)
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS members (user_id BIGINT UNIQUE, experience INT, level INT);")

    conn.commit()
    cursor.close()
    conn.close()

async def update_experience(ctx, author_id: int, amount: int):

    conn = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT experience, level FROM members WHERE user_id = %s;", (author_id,))
    row = cursor.fetchone()

    if row:
        new_exp = row[0] + amount
        new_level = row[1]

        if new_exp >= new_level * 100:
            new_level += 1
            new_exp = 0
            await ctx.send(f"Поздравляем {ctx.author.mention}, вы достигли {new_level} уровня!")

        cursor.execute("UPDATE members SET experience = %s, level = %s WHERE user_id = %s;", (new_exp, new_level, author_id))
    else:
        cursor.execute("INSERT INTO members (user_id, experience, level) VALUES (%s, %s, %s);", (author_id, amount, 1))

    conn.commit()
    cursor.close()
    conn.close()


async def get_member_level(author_id: int) -> Optional[dict]:
    conn = mysql.connector.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, database=DB_DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT experience, level FROM members WHERE user_id = %s;", (author_id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row:
        return {'experience': row[0], 'level': row[1]}
    else:
        return None

@bot.event
async def on_ready():
    print(f'Мы вошли в систему как {bot.user}')
    create_tables()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    author_id = message.author.id
    
    ctx = await bot.get_context(message)
    
    await update_experience(ctx, author_id, random.randint(5, 15))
    await bot.process_commands(message)


@bot.command()
async def rank(ctx):
    """Показать ранг и опыт пользователя"""
    author_id = ctx.author.id
    level_info = await get_member_level(author_id)

    if level_info:
        embed = discord.Embed(title=f"Ранг и опыт {ctx.author.name}", description=f"Уровень: {level_info['level']}", color=0x00ff00)
        embed.add_field(name="Опыт", value=level_info['experience'], inline=True)

        await ctx.send(embed=embed)
    else:
        await ctx.send("Вы еще не получили опыт на сервере.")

@bot.command()
async def character(ctx, name: str):
    """Отображаем информацию о символах"""
    char_info = await get_character_info(name)
    if char_info:
        embed = discord.Embed(title=f"Персонаж: {char_info['name']}", color=0x00ff00)
        embed.add_field(name="Раса", value=char_info['race'], inline=True)
        embed.add_field(name="Класс", value=char_info['class'], inline=True)
        embed.add_field(name="Пол", value=char_info['gender'], inline=True)
        embed.add_field(name="Уровень", value=char_info['level'], inline=True)
        embed.add_field(name="Всего убийств", value=char_info['totalkills'], inline=True)
        embed.set_image(url="https://i.postimg.cc/W3hnpgDw/K0-SAHtr2-jk.webp")  

        await ctx.send(embed=embed)
    else:
        await ctx.send(f"Персонаж '{name}' не найден.")

@bot.command()
async def online(ctx):
    """Показать онлайн-игроков"""
    online_players = await get_online_players()
    if online_players:
        embed = discord.Embed(title="Онлайн-игроки", color=0x00ff00)

        for player in online_players:
            player_info = f"{player['race']} {player['class']} ({player['gender']}, {player['level']} уровень)"
            embed.add_field(name=player['name'], value=player_info, inline=False)

        embed.set_image(url="https://i.postimg.cc/W3hnpgDw/K0-SAHtr2-jk.webp")

        await ctx.send(embed=embed)
    else:
        await ctx.send("Сейчас нет онлайн-игроков.")

@bot.command()
async def botinfo(ctx):
    """Отображаем информацию о боте"""
    embed = discord.Embed(title="Extazy WoW information bot", description="Этот бот отображает информацию о персонажах World of Warcraft на сервере Extazy.", color=0x00ff00)

    # Дополнительная информация о боте
    embed.add_field(name="Автор", value="null", inline=True)
    embed.add_field(name="Версия", value="0.1", inline=True)
    embed.add_field(name="Пример использования", value="!character ИмяПерсонажа", inline=False)

    # Добавляем фоновое изображение
    embed.set_image(url="https://i.postimg.cc/W3hnpgDw/K0-SAHtr2-jk.webp")

    await ctx.send(embed=embed)

@bot.command()
async def commands(ctx):
    """Отображает доступные команды для бота"""
    embed = discord.Embed(title="Доступные команды", description="Список доступных команд для использования Extazy WoW Information bot", color=0x00ff00)
    embed.add_field(name="!character <ИмяПерсонажа>", value="Отображает информацию о персонаже", inline=False)
    embed.add_field(name="!online", value="Показать онлайн-игроков", inline=False)
    embed.add_field(name="!botinfo", value="Отображает информацию о боте", inline=False)
    embed.add_field(name="!commands", value="Отображает список доступных команд", inline=False)

    # Добавляем фоновое изображение
    embed.set_image(url="https://i.postimg.cc/W3hnpgDw/K0-SAHtr2-jk.webp")

    await ctx.send(embed=embed)

bot.run("TOKEN")
      
