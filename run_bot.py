"""
Standalone Runner cho Ma Sói (Werewolf) - Discord Bot & Discord Activity
Chạy bot độc lập kèm Web Server xử lý WebSocket cho Discord Activity (Agrou Rebuild)
"""
import os
import sys
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from aiohttp import web

# Load config
try:
    import config
except ImportError:
    class config:
        DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
        DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
        DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
        WEB_PORT = int(os.getenv("PORT", 31378))
        GUILD_IDS = []

from backend.server import MasoiActivityServer
from backend.cog import handle_masoi_command
from backend.classic import WerewolfGame, LobbyView

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MasoiBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.masoi_activity_server = None

    async def setup_hook(self):
        self.masoi_activity_server = MasoiActivityServer(self)
        print("🐺 [Ma Sói] Activity Server đã sẵn sàng!")

        # Khởi chạy Web Server xử lý API & WebSocket Discord Activity
        asyncio.create_task(self.start_web_server())

        # Đồng bộ Slash Commands
        if hasattr(config, "GUILD_IDS") and config.GUILD_IDS:
            for gid in config.GUILD_IDS:
                try:
                    guild = discord.Object(id=gid)
                    self.tree.copy_global_to(guild=guild)
                    await self.tree.sync(guild=guild)
                    print(f"🔄 Synced slash commands cho Guild {gid}")
                except Exception as e:
                    print(f"⚠️ Sync guild error {gid}: {e}")
        else:
            try:
                await self.tree.sync()
                print("🔄 Synced global slash commands")
            except Exception as e:
                print(f"⚠️ Global sync error: {e}")

    async def start_web_server(self):
        app = web.Application()

        # 1. Static Assets (hình ảnh, css, js cho Activity)
        frontend_assets = os.path.join(os.path.dirname(__file__), "frontend", "assets")
        if os.path.exists(frontend_assets):
            app.router.add_static('/masoi', path=frontend_assets)
            app.router.add_static('/.proxy/masoi', path=frontend_assets)

        # 2. Activity Routes & WebSocket
        server = self.masoi_activity_server

        async def masoi_config_handler(request):
            return await server.handle_config(request)

        async def masoi_token_handler(request):
            return await server.handle_token(request)

        async def masoi_ws_handler(request):
            return await server.handle_ws(request)

        app.router.add_route('*', '/api/masoi/config', masoi_config_handler)
        app.router.add_route('*', '/api/masoi/token', masoi_token_handler)
        app.router.add_route('*', '/api/masoi/ws', masoi_ws_handler)

        app.router.add_route('*', '/.proxy/api/masoi/config', masoi_config_handler)
        app.router.add_route('*', '/.proxy/api/masoi/token', masoi_token_handler)
        app.router.add_route('*', '/.proxy/api/masoi/ws', masoi_ws_handler)

        port = getattr(config, "WEB_PORT", 31378)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"🌐 [Ma Sói Web Server] Đang lắng nghe tại cổng {port}")

bot = MasoiBot()

# ==========================================
# SLASH COMMAND: /masoi
# ==========================================
@bot.tree.command(name="masoi", description="🐺 Chơi Ma Sói (Hỗ trợ Discord Activity & Bot thường)")
@app_commands.describe(che_do="Chọn chế độ: Activity (Giao diện 3D/lửa trại Agrou) hoặc Thường (Text Embed)")
@app_commands.choices(che_do=[
    app_commands.Choice(name="Làng Sương Mù (Discord Activity)", value="activity"),
    app_commands.Choice(name="Giao diện Text Embed (Bot thường)", value="classic")
])
async def masoi_cmd(interaction: discord.Interaction, che_do: app_commands.Choice[str] = None):
    mode = che_do.value if che_do else "activity"
    if mode == "activity":
        await handle_masoi_command(interaction, bot)
    else:
        # Chế độ Text Embed kinh điển
        game = WerewolfGame(interaction.channel, interaction.user)
        view = LobbyView(game)
        embed = discord.Embed(
            title="🐺 MA SÓI — SẢNH CHỜ KINH ĐIỂN",
            description=f"Chủ phòng: {interaction.user.mention}\nSố người tham gia tối thiểu: 4 người\nBấm nút bên dưới để tham gia sảnh chờ!",
            color=0x2B2D31
        )
        embed.set_footer(text="Game Ma Sói độc lập")
        await interaction.response.send_message(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f"✅ Bot Ma Sói đã online với tên: {bot.user} (ID: {bot.user.id})")

if __name__ == "__main__":
    token = getattr(config, "DISCORD_TOKEN", "")
    if not token:
        print("❌ Chưa cấu hình DISCORD_TOKEN trong config.py hoặc biến môi trường!")
    else:
        bot.run(token)
