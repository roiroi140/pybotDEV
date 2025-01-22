from discord.ext import commands
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from os import urandom, environ
from datetime import datetime, timedelta
from discord.utils import get
import discord
import random
import json
from datetime import datetime

# Intents設定
intents = discord.Intents.default()
intents.members = True  # メンバー管理の権限
intents.message_content = True  # メッセージの内容を取得する権限

# Botをインスタンス化
bot = commands.Bot(
    command_prefix="$",  # $コマンド名 でコマンドを実行できるようになる
    case_insensitive=True,  # コマンドの大文字小文字を区別しない
    intents=intents  # 権限を設定
)

# AES暗号化用のキー
aes_key = urandom(32)  # 256ビットキー

# 管理者のID
OWNER_ID = 959378199895212043
# BAN ID
TARGET_USER_ID = 966448197310504970
# StartChannelID
CHANNEL_ID = 1321266748506243113
# ROLL ID
ROLE_ID = 1322869157070377003
# json PASS
DATA_FILE = "globalchat.json"


# Bot起動時のイベント
@bot.event
async def on_ready():
    print(f"discord.py version: {discord.__version__} bot ok owner_id = {OWNER_ID}")
    await bot.tree.sync()
    await greet()

async def greet():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Error: チャンネル ID {CHANNEL_ID} が見つかりません。")
        return

    await channel.send("こんにちは！ボットが起動しました。")
  

# メッセージイベント
@bot.event
async def on_member_join(member):
    embed = discord.Embed(
        title=f"{member.name}さん。参加してくれてありがとう。",
        color=0x00ffff
    )
    # 必要に応じて、メッセージ送信コードを追加
    channel = discord.utils.get(member.guild.text_channels, name="ようこそ")  # 'ようこそ' を適切なチャンネル名に変更
    if channel:
        await channel.send(embed=embed)
    
    # 特定のIDの場合にキックする処理
    target_ids = [1234567890]  # キック対象のユーザーIDリスト
    if member.id in target_ids:
        try:
            await member.ban(reason="特定のIDのため自動キックされました。")
            if channel:
                await channel.send(f"{member.name} さんは特定のIDのためキックされました。")
        except discord.Forbidden:
            if channel:
                await channel.send(f"{member.name} さんをキックできませんでした（権限不足）。")
        except Exception as e:
            if channel:
                await channel.send(f"{member.name} さんをキック中にエラーが発生しました: {e}")

# JSONデータを読み込む関数
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

# JSONデータを書き込む関数
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# スラッシュコマンドの登録
@bot.tree.command(name='globalchat', description='グローバルチャットに追加します。ベータ版')
async def save(interaction: discord.Interaction, value: str):
    data = load_data()
    
    # コマンド情報を保存
    user_id = str(interaction.user.id)
    if user_id not in data:
        data[user_id] = []
    
    data[user_id].append({
        "command": "save",
        "value": value,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    save_data(data)
    await interaction.response.send_message(f"Value '{value}' has been saved for user {interaction.user.name}.")

# AES暗号化コマンド
@bot.command()
async def aes_encrypt(ctx: commands.Context, *, text: str):
    """AESを使用してテキストを暗号化するコマンド"""
    iv = urandom(16)  # 暗号化ごとに新しいIVを生成
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padding_length = 16 - (len(text.encode("utf-8")) % 16)
    padded_data = text.encode("utf-8") + bytes([padding_length] * padding_length)

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    await ctx.send(f"暗号化結果: `{iv.hex()}:{encrypted_data.hex()}`")

# AES復号化コマンド
@bot.command()
async def aes_decrypt(ctx: commands.Context, *, hex_data: str):
    """AESを使用して暗号化されたデータを復号化するコマンド"""
    try:
        iv, encrypted_data = hex_data.split(":")
        iv = bytes.fromhex(iv)
        encrypted_data = bytes.fromhex(encrypted_data)

        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        decrypted_padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        padding_length = decrypted_padded_data[-1]
        decrypted_data = decrypted_padded_data[:-padding_length].decode("utf-8")

        await ctx.send(f"復号化結果: `{decrypted_data}`")
    except Exception as e:
        await ctx.send(f"エラーが発生しました: {e}")

# シーザー暗号関数
def caesar_cipher(text: str, shift: int) -> str:
    """シーザー暗号の暗号化または復号化を行う関数"""
    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + shift) % 26 + base))
        else:
            result.append(char)
    return ''.join(result)

# オーナーチェック関数
def is_owner(interaction: discord.Interaction):
    return interaction.user.id == OWNER_ID

# 挨拶コマンド
@bot.tree.command(name='hello', description='挨拶')
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.name}")

# ダイスコマンド
# 100面ダイス
@bot.tree.command(name='1d100', description='100面ダイス')
async def d100(interaction: discord.Interaction):
    result = random.randint(1, 100)
    await interaction.response.send_message(f"🎲 100面ダイス: {result} 1d100 >> {result}")
# 20面ダイス
@bot.tree.command(name='1d20', description='20面ダイス')
async def d20(interaction: discord.Interaction):
    result = random.randint(1, 20)
    await interaction.response.send_message(f"🎲 20面ダイス: {result} 1d100 >> {result}")
# 12面ダイス
@bot.tree.command(name='1d12', description='12面ダイス')
async def d12(interaction: discord.Interaction):
    result = random.randint(1, 12)
    await interaction.response.send_message(f"🎲 12面ダイス: {result} 1d100 >> {result}")
# 10面ダイス
@bot.tree.command(name='1d10', description='10面ダイス')
async def d10(interaction: discord.Interaction):
    result = random.randint(1, 10)
    await interaction.response.send_message(f"🎲 10面ダイス: {result} 1d100 >> {result}")
# 8面ダイス
@bot.tree.command(name='1d8', description='8面ダイス')
async def d8(interaction: discord.Interaction):
    result = random.randint(1, 8)
    await interaction.response.send_message(f"🎲 8面ダイス: {result} 1d100 >> {result}")
# 6面ダイス
@bot.tree.command(name='1d6', description='6面ダイス')
async def d6(interaction: discord.Interaction):
    result = random.randint(1, 6)
    await interaction.response.send_message(f"🎲 6面ダイス: {result} 1d100 >> {result}")
# 4面ダイス
@bot.tree.command(name='1d4', description='4面ダイス')
async def d4(interaction: discord.Interaction):
    result = random.randint(1, 4)
    await interaction.response.send_message(f"🎲 4面ダイス: {result} 1d100 >> {result}")



# 足し算コマンド
@bot.command()
async def add(ctx: commands.Context, a: int, b: int):
    """足し算をするコマンド"""
    await ctx.send(a + b)

# メッセージ履歴取得コマンド
@bot.command(
    name="message",
    aliases=["msg", "m"],
)
async def get_message(ctx: commands.Context, channel: discord.TextChannel):
    """チャンネルのメッセージを取得し、テキストファイルに保存するコマンド"""
    with open("messages.txt", "w", encoding="utf-8") as file:
        async for message in channel.history(
            after=datetime.utcnow() - timedelta(hours=1),
            oldest_first=True,
        ):
            jst = message.created_at + timedelta(hours=9)
            file.write(f"{message.author.name}: {jst.strftime('%Y/%m/%d %H:%M:%S')}\n{message.content}\n\n")

    await ctx.send(file=discord.File("messages.txt"))

# オーナー限定コマンド
# ミュートコマンド
@bot.tree.command(name="mute", description="オーナーのみ使用可能なミュートコマンド")
async def mute(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction):
        await interaction.response.send_message("このコマンドはオーナーのみ使用できます。", ephemeral=True)
        return

    role = get(interaction.guild.roles, name="チャット制限")
    if role is None:
        role = await interaction.guild.create_role(name="チャット制限", mentionable=True)

    await member.add_roles(role)
    await interaction.response.send_message(f"{member.mention} をチャット制限しました。")

# ミュート解除コマンド
@bot.tree.command(name="unmute", description="オーナーのみ使用可能なミュート解除コマンド")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction):
        await interaction.response.send_message("このコマンドはオーナーのみ使用できます。", ephemeral=True)
        return

    role = get(interaction.guild.roles, name="チャット制限")
    if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(f"{member.mention} のミュートを解除しました。")
    else:
        await interaction.response.send_message(f"{member.mention} はミュートされていません。", ephemeral=True)

@bot.tree.command(name="ban_everywhere", description="特定のIDを全サーバーでBANします")
async def ban_everywhere(interaction: discord.Interaction, member: discord.Member):
    if not is_owner(interaction):
      await interaction.response.send_message("このコマンドはオーナーのみ使用できます。", ephemral=True)
      return
      
    banned_guilds = []  # BANが成功したサーバーのリスト
    failed_guilds = []  # BANに失敗したサーバーのリスト

    for guild in bot.guilds:  # Botが所属しているすべてのサーバーをループ
        member = guild.get_member(TARGET_USER_ID)
        if member:
            try:
                await member.ban(reason="特定のIDによる全サーバーBAN")
                banned_guilds.append(guild.name)
            except Exception as e:
                failed_guilds.append((guild.name, str(e)))
        else:
            failed_guilds.append((guild.name, "メンバーが見つかりませんでした"))

    # 結果を送信
    success_message = (
        f"以下のサーバーでBANが成功しました: {', '.join(banned_guilds)}" if banned_guilds else "BANに成功したサーバーはありません。"
    )
    failed_message = (
        f"\n以下のサーバーでBANが失敗しました:\n" + "\n".join([f"{guild}: {reason}" for guild, reason in failed_guilds])
        if failed_guilds
        else "全てのサーバーでBANが成功しました。"
    )

    await interaction.response.send_message(success_message + "\n" + failed_message, ephemeral=True)
# オーナー限定コマンド終了
# シーザー暗号コマンド
@bot.command()
async def encrypt(ctx: commands.Context, shift: int, *, text: str):
    """シーザー暗号でテキストを暗号化するコマンド"""
    encrypted_text = caesar_cipher(text, shift)
    await ctx.send(f"暗号化結果: {encrypted_text}")

@bot.command()
async def decrypt(ctx: commands.Context, shift: int, *, text: str):
    """シーザー暗号でテキストを復号化するコマンド"""
    decrypted_text = caesar_cipher(text, -shift)
    await ctx.send(f"復号化結果: {decrypted_text}")
# Botを実行
bot.run(environ['token'])
