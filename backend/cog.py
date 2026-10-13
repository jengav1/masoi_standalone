# games/masoi_activity/cog.py
"""
Discord Cog điều phối lệnh /masoi (Mục 1, 3, 11).
Tạo phòng Ma Sói Activity và gửi embed cùng nút Mở Activity.
"""
import discord
from discord import app_commands
from discord.ext import commands
import os
import config

class MasoiActivityView(discord.ui.View):
    def __init__(self, room_id: str, client_id: str):
        super().__init__(timeout=None)
        self.room_id = room_id
        
        # Link Activity qua Discord Launch Protocol hoặc URL
        activity_url = f"https://discord.com/activities/{client_id}"
        self.add_item(discord.ui.Button(
            label="🎮 Mở Ma Sói Activity",
            style=discord.ButtonStyle.link,
            url=activity_url,
            emoji="🐺"
        ))

    @discord.ui.button(label="📋 Thông tin phòng", style=discord.ButtonStyle.secondary, emoji="ℹ️")
    async def info_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🐺 **Phòng Ma Sói:** `{self.room_id}`\n"
            f"Hãy bấm nút **Mở Ma Sói Activity** bên trên để tham gia vào vòng lửa trại Làng Sương Mù!",
            ephemeral=True
        )

async def handle_masoi_command(interaction: discord.Interaction, bot):
    """Xử lý lệnh /masoi tạo hoặc tham gia phòng Activity"""
    if not interaction.guild_id:
        return await interaction.response.send_message("Hãy chơi Ma Sói trong server Discord!", ephemeral=True)

    client_id = os.getenv("DISCORD_CLIENT_ID") or getattr(config, "DISCORD_CLIENT_ID", "")
    server = getattr(bot, "masoi_activity_server", None)
    
    room_id = f"masoi_{interaction.channel_id}"
    if server:
        server.room_service.get_or_create_room(
            room_id=room_id,
            host_uid=interaction.user.id,
            channel_id=interaction.channel_id,
            guild_id=interaction.guild_id,
            on_broadcast=server.broadcast_room_state
        )

    embed = discord.Embed(
        title="🐺 MA SÓI — LÀNG SƯƠNG MÙ (DISCORD ACTIVITY)",
        description=(
            f"**Chủ phòng:** {interaction.user.mention}\n"
            f"**Khu vực:** <#{interaction.channel_id}>\n\n"
            "🔥 **Lửa trại đã được thắp sáng!**\n"
            "Tất cả người chơi hãy bấm nút **Mở Ma Sói Activity** bên dưới để ngồi vào vòng ghế, xem vai trò và bắt đầu cuộc chiến sinh tồn!"
        ),
        color=0xD6B479
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3209/3209990.png")
    embed.set_image(url="https://media.discordapp.net/attachments/1458674262293614685/1460560226506903685/Season_3_Revolver_GIF_by_The_Simpsons.gif")
    embed.set_footer(text="Hỗ trợ từ 4 đến 12 người · Không khí Agrou 3D Low-Poly")

    view = MasoiActivityView(room_id, client_id)
    await interaction.response.send_message(embed=embed, view=view)
