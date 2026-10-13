import discord
from discord.ui import View, Button, Select
import asyncio
import random
from utils import safe_edit

# --- CẤU HÌNH ---
IMG_NIGHT = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExNmEwajd4a2hobnZ6cXdhY3Nzbjluc3dvaGg4eHV2ZGZtNjcxY2lybSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/rMpEJ6E10Uw5G/giphy.gif" 
IMG_DAY = "https://img.freepik.com/free-vector/medieval-village-scene-daytime_1308-50073.jpg"   
IMG_LOBBY = "https://png.pngtree.com/background/20210710/original/pngtree-simple-board-game-werewolf-kill-poster-design-background-illustration-picture-image_1044759.jpg" 

ROLE_DATA = {
    "Sói": {"url": "https://cdn.discordapp.com/attachments/1252533555779866716/1459092528698495062/sc3b3i.png", "desc": "😈 **Nhiệm vụ:** Giết hết dân làng.\n🌙 **Ban đêm:** Thảo luận chọn con mồi.", "color": 0xFF0000},
    "Dân làng": {"url": "https://cdn.discordapp.com/attachments/1252533555779866716/1459092630687191072/dc3a2n-lc3a0ng.png", "desc": "👨‍🌾 **Nhiệm vụ:** Tìm ra sói.\n☀️ **Ban ngày:** Suy luận và bỏ phiếu.", "color": 0x00FF00},
    "Bảo vệ": {"url": "https://cdn.discordapp.com/attachments/1252533555779866716/1459092696533831816/be1baa3o-ve1bb87.png", "desc": "🛡️ **Nhiệm vụ:** Bảo vệ dân làng.\n🌙 **Ban đêm:** Chọn 1 người để bảo vệ.", "color": 0x3498DB},
    "Tiên tri": {"url": "https://cdn.discordapp.com/attachments/1252533555779866716/1459092765869609122/tic3aan-tri.png", "desc": "🔮 **Nhiệm vụ:** Soi role.\n🌙 **Ban đêm:** Chọn người để soi danh tính.", "color": 0x9B59B6},
    "Phù thuỷ": {"url": "https://cdn.discordapp.com/attachments/1252533555779866716/1459092829212246209/phc3b9-the1bba7y.png", "desc": "🧙‍♀️ **Nhiệm vụ:** Dùng thuốc.\n🌙 **Ban đêm:** 1 bình Cứu, 1 bình Độc.", "color": 0xE91E63},
    "Thợ săn": {"url": "https://cdn.discordapp.com/attachments/1252533555779866716/1459092897357103136/the1bba3-sc483n.png", "desc": "🔫 **Nhiệm vụ:** Kéo theo kẻ thù.\n☠️ **Khi chết:** Bắn chết 1 người khác.", "color": 0xE67E22}
}

CHANNEL_PREFIX = "🐺-hang-sói-"

# --- CLASS LOGIC GAME ---
class WerewolfGame:
    def __init__(self, interaction):
        self.interaction = interaction
        self.channel = interaction.channel  
        self.user = interaction.user        
        
        self.players = [] 
        self.alive_players = [] 
        self.roles = {} 
        self.wolf_thread = None 
        
        self.lobby_message_obj = None 

        self.protected_id = None 
        self.last_protected_id = None 
        self.witch_potions = {"heal": True, "kill": True}
        self.votes = {}
        
        # --- BIẾN MỚI ĐỂ QUẢN LÝ TRẠNG THÁI GAME ---
        self.stop_game_flag = False      # Cờ để dừng game thủ công
        self.has_interaction_tonight = False # Cờ kiểm tra AFK

    async def start_lobby(self):
        self.players.append(self.user)
        embed = discord.Embed(title="🐺 MA SÓI", description=f"**Chủ phòng:** {self.user.mention}\n\n**Danh sách người chơi (1/10):**\n1. {self.user.display_name} 👑", color=discord.Color.dark_red())
        if IMG_LOBBY: embed.set_image(url=IMG_LOBBY)
        embed.set_footer(text="Cần ít nhất 4 người để bắt đầu")
        self.lobby_msg = await self.interaction.channel.send(embed=embed, view=LobbyView(self))

    async def update_lobby_ui(self):
        player_list = "\n".join([f"{i+1}. {p.display_name} {'👑' if p == self.user else ''}" for i, p in enumerate(self.players)])
        embed = discord.Embed(title="🐺 MA SÓI", description=f"**Chủ phòng:** {self.user.mention}\n\n**Danh sách người chơi ({len(self.players)}/10):**\n{player_list}", color=discord.Color.dark_red())
        if IMG_LOBBY: embed.set_image(url=IMG_LOBBY)
        embed.set_footer(text="Cần ít nhất 4 người để bắt đầu")
        await safe_edit(self.lobby_msg, embed=embed)

    def generate_roles(self, count):
        roles = []
        if count == 4: roles = ["Sói", "Dân làng", "Bảo vệ"]
        elif count == 5: roles = ["Sói", "Dân làng", "Dân làng", "Bảo vệ"]
        elif count == 6: roles = ["Sói", "Dân làng", "Dân làng", "Dân làng", "Bảo vệ"]
        elif count == 7: roles = ["Sói", "Sói", "Dân làng", "Dân làng", "Dân làng", "Bảo vệ"]
        elif count == 8: roles = ["Sói", "Sói", "Dân làng", "Dân làng", "Dân làng", "Bảo vệ", "Phù thuỷ"]
        elif count == 9: roles = ["Sói", "Sói", "Dân làng", "Dân làng", "Dân làng", "Bảo vệ", "Phù thuỷ", "Tiên tri"]
        elif count == 10: roles = ["Sói", "Sói", "Dân làng", "Dân làng", "Dân làng", "Dân làng", "Bảo vệ", "Phù thuỷ", "Tiên tri"]
        else: return ["Sói"] + ["Dân làng"] * (count - 1)
        random_pool = ["Thợ săn", "Dân làng"]
        if "Tiên tri" not in roles: random_pool.append("Tiên tri")
        if "Phù thuỷ" not in roles: random_pool.append("Phù thuỷ")
        roles.append(random.choice(random_pool))
        return roles

    async def start_game(self):
        if len(self.players) < 4: 
            await self.channel.send("⚠️ Cần ít nhất 4 người chơi!")
            return
        self.alive_players = self.players.copy()
        roles_pool = self.generate_roles(len(self.players))
        random.shuffle(roles_pool)
        for i, player in enumerate(self.alive_players):
            self.roles[player.id] = roles_pool[i]
        role_view = RoleCheckView(self)
        await self.channel.send(f"🎲 **Đã phân vai!** Hãy kiểm tra vai trò bí mật bên dưới.", view=role_view)
        wolves = [p for p in self.alive_players if self.roles[p.id] == "Sói"]
        await self.create_wolf_thread(wolves)
        await self.channel.send("⏳ Game sẽ bắt đầu sau 15 giây...")
        await asyncio.sleep(15)
        await self.game_loop()

    async def create_wolf_thread(self, wolves):
        thread_name = f"{CHANNEL_PREFIX}{random.randint(1000, 9999)}"
        try:
            self.wolf_thread = await self.channel.create_thread(name=thread_name, type=discord.ChannelType.private_thread, auto_archive_duration=60, invitable=False)
            for wolf in wolves: await self.wolf_thread.add_user(wolf)
            wolf_mentions = ", ".join([w.mention for w in wolves])
            await self.wolf_thread.send(f"🐺 **HANG Ổ SÓI**\nThành viên: {wolf_mentions}")
        except: pass

    async def cleanup_game(self):
        if self.wolf_thread:
            try:
                await self.wolf_thread.send("🏁 Game kết thúc. Kênh tự huỷ...")
                await asyncio.sleep(5)
                await self.wolf_thread.delete()
            except: pass 

    async def send_status_board(self, title="Cập nhật trạng thái"):
        desc = ""
        for p in self.players:
            status = "🟢 Còn sống" if p in self.alive_players else "💀 Đã chết"
            desc += f"**{p.display_name}**: {status}\n"
        embed = discord.Embed(title=title, description=desc, color=discord.Color.gold())
        await self.channel.send(embed=embed)

    async def game_loop(self):
        try:
            while True:
                # Kiểm tra cờ dừng game thủ công
                if self.stop_game_flag:
                    await self.channel.send("🛑 **Game đã bị huỷ bởi chủ phòng!**")
                    break

                # --- BAN ĐÊM ---
                embed_night = discord.Embed(title="🌑 MÀN ĐÊM BUÔNG XUỐNG", description="Tất cả cư dân đi ngủ...", color=discord.Color.dark_theme())
                if IMG_NIGHT: embed_night.set_image(url=IMG_NIGHT)
                await self.channel.send(embed=embed_night)
                
                self.protected_id = None 
                self.votes = {} 
                self.has_interaction_tonight = False # Reset cờ AFK

                if "Bảo vệ" in self.roles.values(): await self.run_phase("Bảo vệ", "🛡️ Bảo vệ dậy đi...", 20)
                if "Tiên tri" in self.roles.values(): await self.run_phase("Tiên tri", "🔮 Tiên tri dậy đi...", 20)

                await self.channel.send("🐺 **Sói đang đi săn...** (60s)")
                wolf_target = await self.wolf_phase_logic() 
                victim = wolf_target
                if self.protected_id and wolf_target and self.protected_id == wolf_target.id: victim = None 

                if "Phù thuỷ" in self.roles.values(): await self.witch_phase_logic(victim)
                elif victim: self.current_deaths = [victim]
                else: self.current_deaths = []

                # --- KIỂM TRA AFK (Nếu cả đêm không ai bấm nút nào) ---
                # Chỉ tính AFK nếu có vai trò Sói/Bảo vệ/Tiên tri/Phù thuỷ còn sống
                special_roles_alive = any(self.roles[p.id] in ["Sói", "Bảo vệ", "Tiên tri", "Phù thuỷ"] for p in self.alive_players)
                
                if special_roles_alive and not self.has_interaction_tonight:
                    await self.channel.send("💤 **Tất cả mọi người đã ngủ quên (AFK)!** Game kết thúc do không có tương tác.")
                    break

                # --- BAN NGÀY ---
                embed_day = discord.Embed(title="☀️ TRỜI ĐÃ SÁNG!", description="Mọi người thức dậy...", color=discord.Color.orange())
                if IMG_DAY: embed_day.set_image(url=IMG_DAY)
                await self.channel.send(embed=embed_day)
                
                if self.current_deaths:
                    dead_names = ", ".join([f"**{p.display_name}**" for p in self.current_deaths])
                    await self.channel.send(f"⚰️ Đêm qua: {dead_names} đã ra đi.")
                    for p in self.current_deaths:
                        if p in self.alive_players:
                            self.alive_players.remove(p)
                            if self.roles[p.id] == "Thợ săn": await self.hunter_trigger(p)
                else: await self.channel.send("🎉 Một đêm bình yên! Không ai chết cả.")

                await self.send_status_board(title="📋 Điểm danh sáng sớm")
                if self.check_win(): break

                # Vote (Sử dụng logic Live Update + Nút Huỷ Game)
                should_continue = await self.voting_phase()
                
                if self.stop_game_flag: # Kiểm tra lại sau khi vote xong
                    await self.channel.send("🛑 **Game đã bị huỷ bởi chủ phòng!**")
                    break

                if self.check_win(): break
                if not should_continue: break 

                await self.channel.send("🌇 **Màn Đêm buông xuống...** (5s)")
                await asyncio.sleep(5)
        
        except Exception as e:
            await self.channel.send(f"⚠️ Lỗi game: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup_game()

    async def run_phase(self, role_name, msg_content, duration):
        role_alive = any(self.roles[p.id] == role_name for p in self.alive_players)
        if role_alive:
            view = GenericTurnView(self, role_name)
            msg = await self.channel.send(f"{msg_content} (Bạn có {duration}s)", view=view)
            await asyncio.sleep(duration)
            await msg.delete()
        else:
            msg = await self.channel.send(f"{msg_content} (Đang chờ...)")
            await asyncio.sleep(duration) 
            await msg.delete()

    async def wolf_phase_logic(self):
        wolves = [p for p in self.alive_players if self.roles[p.id] == "Sói"]
        if wolves and self.wolf_thread: 
            view = WolfThreadView(self, wolves)
            await self.wolf_thread.send(f"🐺 **Đêm nay cắn ai?** (60s thảo luận)", view=view)
        await asyncio.sleep(60)
        return getattr(self, "wolf_target_temp", None)

    async def witch_phase_logic(self, victim):
        witches_alive = [p for p in self.alive_players if self.roles[p.id] == "Phù thuỷ"]
        if witches_alive:
            self.current_deaths = []
            if victim: self.current_deaths.append(victim)
            view = WitchCallView(self, victim)
            msg = await self.channel.send("🧙‍♀️ **Phù thuỷ dậy đi...** (20s)", view=view)
            await asyncio.sleep(20)
            await msg.delete()
        else:
            self.current_deaths = [victim] if victim else []
            msg = await self.channel.send("🧙‍♀️ **Phù thuỷ dậy đi...** (Đang chờ...)")
            await asyncio.sleep(20) 
            await msg.delete()

    # --- HÀM TÍNH TOÁN KẾT QUẢ VOTE ---
    def calculate_vote_result(self):
        skip_votes = list(self.votes.values()).count("skip")
        total_votes = len(self.votes)
        
        if not self.votes or (skip_votes == total_votes and total_votes > 0):
            return "skip", None

        tally = {}
        for target_id in self.votes.values():
            if target_id == "skip": continue
            tally[target_id] = tally.get(target_id, 0) + 1
        
        if not tally: return "skip", None

        max_vote = max(tally.values())
        candidates = [pid for pid, count in tally.items() if count == max_vote]
        
        if len(candidates) == 1:
            return "kill", candidates[0]
        else:
            return "draw", None

    async def voting_phase(self):
        view = VotingView(self)
        embed_board = view.generate_vote_board()
        await self.channel.send(embed=embed_board, view=view)
        
        await view.wait()
        
        # Nếu view dừng do bấm nút "Huỷ Game"
        if self.stop_game_flag: return False

        result_type, target_id = self.calculate_vote_result()
        
        if result_type == "skip":
            await self.channel.send("🏳️ **Kết quả:** Bỏ phiếu trắng / Không hợp lệ. Không ai bị treo cổ.")
            return True
        elif result_type == "draw":
            await self.channel.send("⚖️ **Kết quả:** Hoà phiếu! Không ai bị treo cổ.")
            return True
        elif result_type == "kill":
            victim = discord.utils.get(self.players, id=target_id)
            if victim in self.alive_players:
                self.alive_players.remove(victim)
                await self.channel.send(f"⚖️ **KẾT QUẢ:** **{victim.display_name}** đã bị treo cổ! Role ẩn.")
                if self.roles[victim.id] == "Thợ săn":
                    await self.hunter_trigger(victim)
            return True
        return True

    async def hunter_trigger(self, hunter):
        view = HunterView(self, hunter)
        msg = await self.channel.send(f"🔫 **{hunter.mention} LÀ THỢ SĂN!** (15s chọn mục tiêu)", view=view)
        await view.wait() 
        
        # Thợ săn cũng tính là tương tác (tránh AFK sai)
        if view.has_interacted: 
            self.has_interaction_tonight = True

        if view.target and view.target in self.alive_players:
            self.alive_players.remove(view.target)
            await self.channel.send(f"💥 **ĐOÀNG!** Thợ săn bắn chết **{view.target.display_name}**.")
            if self.roles[view.target.id] == "Thợ săn":
                 await self.hunter_trigger(view.target)

    def check_win(self):
        wolves = [p for p in self.alive_players if self.roles[p.id] == "Sói"]
        villagers = [p for p in self.alive_players if self.roles[p.id] != "Sói"]
        if not wolves:
            asyncio.create_task(self.channel.send("🏆 **PHE DÂN THẮNG!** (Hết Sói)"))
            return True
        if len(wolves) >= len(villagers):
            asyncio.create_task(self.channel.send("🐺 **PHE SÓI THẮNG!** (Số Sói áp đảo)"))
            return True
        return False

# --- UI VIEWS ---

class LobbyView(View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game

    @discord.ui.button(label="Tham gia", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: Button):
        if interaction.user not in self.game.players:
            self.game.players.append(interaction.user)
            await interaction.response.send_message("Đã tham gia!", ephemeral=True)
            await self.game.update_lobby_ui()
        else:
            await interaction.response.send_message("Bạn đã trong phòng rồi!", ephemeral=True)

    @discord.ui.button(label="Rời phòng", style=discord.ButtonStyle.grey)
    async def leave(self, interaction: discord.Interaction, button: Button):
        if interaction.user in self.game.players:
            if interaction.user == self.game.user:
                await interaction.response.send_message("Chủ phòng không thể rời! Hãy dùng nút Huỷ nếu muốn.", ephemeral=True)
                return
            self.game.players.remove(interaction.user)
            await interaction.response.send_message("Đã rời phòng!", ephemeral=True)
            await self.game.update_lobby_ui()
        else:
            await interaction.response.send_message("Bạn chưa tham gia!", ephemeral=True)

    @discord.ui.button(label="Bắt đầu", style=discord.ButtonStyle.red)
    async def start(self, interaction: discord.Interaction, button: Button):
        if interaction.user == self.game.user:
            await interaction.response.send_message("🚀 Game bắt đầu!", ephemeral=True)
            self.stop()
            await self.game.start_game()
        else:
            await interaction.response.send_message("Chỉ chủ phòng mới được bắt đầu!", ephemeral=True)

class RoleCheckView(View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game
    @discord.ui.button(label="🔍 Xem Role (Bí mật)", style=discord.ButtonStyle.primary, emoji="🤫")
    async def check_role(self, interaction: discord.Interaction, button: Button):
        if interaction.user not in self.game.alive_players:
            await interaction.response.send_message("Bạn không có trong game này!", ephemeral=True)
            return
        role_name = self.game.roles.get(interaction.user.id)
        data = ROLE_DATA.get(role_name, {"url": "", "desc": "Không có mô tả", "color": 0x95A5A6})
        embed = discord.Embed(title=f"🎭 BẠN LÀ: {role_name.upper()}", description=data["desc"], color=data["color"])
        if data["url"]: embed.set_image(url=data["url"])
        await interaction.response.send_message(embed=embed, ephemeral=True)

class GenericTurnView(View):
    def __init__(self, game, required_role):
        super().__init__(timeout=None) 
        self.game = game
        self.required_role = required_role
    @discord.ui.button(label="Thực hiện hành động", style=discord.ButtonStyle.blurple, emoji="✨")
    async def action(self, interaction: discord.Interaction, button: Button):
        user_id = interaction.user.id
        if user_id not in [p.id for p in self.game.alive_players]:
            await interaction.response.send_message("Bạn đã chết rồi!", ephemeral=True)
            return
        real_role = self.game.roles.get(user_id)
        if real_role != self.required_role:
            await interaction.response.send_message(f"Bạn không phải là {self.required_role}!", ephemeral=True)
            return
        # ĐÁNH DẤU LÀ CÓ TƯƠNG TÁC
        self.game.has_interaction_tonight = True
        
        if self.required_role == "Bảo vệ":
            await interaction.response.send_message("🛡️ Chọn người bảo vệ:", view=GuardSelect(self.game), ephemeral=True)
        elif self.required_role == "Tiên tri":
            await interaction.response.send_message("👁️ Chọn người để soi:", view=SeerSelect(self.game), ephemeral=True)

class GuardSelect(View):
    def __init__(self, game):
        super().__init__(timeout=20)
        options = []
        for p in game.alive_players:
            if game.last_protected_id == p.id: continue 
            options.append(discord.SelectOption(label=p.display_name, value=str(p.id)))
        select = Select(placeholder="Chọn người bảo vệ...", options=options)
        select.callback = self.callback
        self.add_item(select)
        self.game = game
    async def callback(self, interaction):
        self.game.has_interaction_tonight = True # Đánh dấu tương tác
        target_id = int(interaction.data['values'][0])
        self.game.protected_id = target_id
        self.game.last_protected_id = target_id
        target = discord.utils.get(self.game.players, id=target_id)
        await interaction.response.send_message(f"Đã bảo vệ **{target.display_name}**", ephemeral=True)

class SeerSelect(View):
    def __init__(self, game):
        super().__init__(timeout=20)
        self.game = game
        options = [discord.SelectOption(label=p.display_name, value=str(p.id)) for p in game.alive_players]
        select = Select(placeholder="Chọn người soi...", options=options)
        select.callback = self.callback
        self.add_item(select)
    async def callback(self, interaction: discord.Interaction):
        self.game.has_interaction_tonight = True # Đánh dấu tương tác
        target_id = int(interaction.data['values'][0])
        role = self.game.roles.get(target_id)
        target = discord.utils.get(self.game.players, id=target_id)
        msg = f"😈 **BÁO ĐỘNG!** {target.display_name} chính là **SÓI**!" if role == "Sói" else f"😇 **AN TOÀN.** {target.display_name} là **Người**."
        await interaction.response.send_message(msg, ephemeral=True)
        self.stop() 

class WolfThreadView(View):
    def __init__(self, game, wolves):
        super().__init__(timeout=60) 
        self.game = game
        self.game.wolf_target_temp = None 
        options = [discord.SelectOption(label=p.display_name, value=str(p.id)) for p in game.alive_players if game.roles[p.id] != "Sói"]
        if not options: options.append(discord.SelectOption(label="Tự hủy", value="none"))
        select = Select(placeholder="Chọn con mồi...", options=options)
        select.callback = self.callback
        self.add_item(select)
    async def callback(self, interaction):
        self.game.has_interaction_tonight = True # Đánh dấu tương tác
        if interaction.data['values'][0] == "none": self.game.wolf_target_temp = None
        else: 
            target = discord.utils.get(interaction.guild.members, id=int(interaction.data['values'][0]))
            self.game.wolf_target_temp = target
        target_name = self.game.wolf_target_temp.display_name if self.game.wolf_target_temp else "Không ai"
        await interaction.response.send_message(f"Đã chốt cắn: **{target_name}**", ephemeral=False)

class WitchCallView(View):
    def __init__(self, game, victim):
        super().__init__(timeout=None)
        self.game = game
        self.victim = victim
    @discord.ui.button(label="Hành động", style=discord.ButtonStyle.primary)
    async def action(self, interaction: discord.Interaction, button: Button):
        user_id = interaction.user.id
        if user_id not in [p.id for p in self.game.alive_players]: return
        if self.game.roles.get(user_id) != "Phù thuỷ":
            await interaction.response.send_message("Bạn không phải Phù thuỷ!", ephemeral=True)
            return
        
        self.game.has_interaction_tonight = True # Đánh dấu tương tác
        await interaction.response.send_message(f"🩸 Đêm nay **{self.victim.display_name if self.victim else 'không ai'}** bị cắn.", view=WitchActionView(self.game, self.victim), ephemeral=True)

class WitchActionView(View):
    def __init__(self, game, victim):
        super().__init__(timeout=20)
        self.game = game
        self.victim = victim
        if victim and game.witch_potions['heal']:
            btn_heal = Button(label="Cứu", style=discord.ButtonStyle.green)
            btn_heal.callback = self.heal
            self.add_item(btn_heal)
        if game.witch_potions['kill']:
            options = [discord.SelectOption(label=f"Giết {p.display_name}", value=str(p.id)) for p in game.alive_players]
            select = Select(placeholder="Dùng độc...", options=options)
            select.callback = self.kill
            self.add_item(select)
    async def heal(self, interaction):
        self.game.has_interaction_tonight = True
        if self.victim in self.game.current_deaths:
            self.game.current_deaths.remove(self.victim)
            self.game.witch_potions['heal'] = False
            await interaction.response.send_message("Đã cứu!", ephemeral=True)
        else: await interaction.response.send_message("Lỗi.", ephemeral=True)
    async def kill(self, interaction):
        self.game.has_interaction_tonight = True
        target_id = int(interaction.data['values'][0])
        target = discord.utils.get(interaction.guild.members, id=target_id)
        self.game.current_deaths.append(target)
        self.game.witch_potions['kill'] = False
        await interaction.response.send_message(f"Đã giết {target.display_name}!", ephemeral=True)

# --- SỬA: VOTING VIEW CÓ NÚT HUỶ GAME ---
class VotingView(View):
    def __init__(self, game):
        super().__init__(timeout=120) 
        self.game = game
        options = [discord.SelectOption(label=p.display_name, value=str(p.id)) for p in game.alive_players]
        options.append(discord.SelectOption(label="Bỏ phiếu trắng", value="skip", emoji="🏳️"))
        self.add_item(Select(placeholder="Treo cổ ai...", options=options, custom_id="vote_select"))

    # NÚT HUỶ GAME CHỈ DÀNH CHO CHỦ PHÒNG
    @discord.ui.button(label="Huỷ Game (Admin)", style=discord.ButtonStyle.danger, row=1)
    async def stop_game(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.game.user:
            await interaction.response.send_message("Chỉ chủ phòng mới được huỷ game!", ephemeral=True)
            return
        
        self.game.stop_game_flag = True
        await interaction.response.send_message("Đã kích hoạt huỷ game!", ephemeral=True)
        self.stop() # Dừng view ngay lập tức

    def generate_vote_board(self):
        desc = "Hãy chọn người bạn nghi ngờ là Sói!\n\n"
        if not self.game.votes:
            desc += "⏳ *Chưa có ai bỏ phiếu...*"
        else:
            for voter_id, target_id in self.game.votes.items():
                voter = discord.utils.get(self.game.players, id=voter_id)
                voter_name = voter.display_name if voter else "Unknown"
                if target_id == "skip": desc += f"⚪ **{voter_name}**: Phiếu trắng\n"
                else:
                    target = discord.utils.get(self.game.players, id=target_id)
                    target_name = target.display_name if target else "Unknown"
                    desc += f"👉 **{voter_name}** ➔ **{target_name}**\n"
        embed = discord.Embed(title="🗳️ BẢNG BỎ PHIẾU (LIVE)", description=desc, color=discord.Color.yellow())
        embed.set_footer(text=f"Đã vote: {len(self.game.votes)}/{len(self.game.alive_players)} người")
        return embed

    async def interaction_check(self, interaction):
        # Nếu là nút bấm (Huỷ game), bỏ qua check vote
        if interaction.type == discord.InteractionType.component and interaction.data.get("component_type") == 2:
            return True

        if interaction.user not in self.game.alive_players:
            await interaction.response.send_message("💀 Bạn đã chết, không được bỏ phiếu!", ephemeral=True)
            return False

        val = interaction.data['values'][0]
        self.game.votes[interaction.user.id] = int(val) if val != "skip" else "skip"
        new_embed = self.generate_vote_board()
        await interaction.response.edit_message(embed=new_embed, view=self)

        if len(self.game.votes) >= len(self.game.alive_players):
            await interaction.channel.send("⚡ Tất cả đã bỏ phiếu! Kết thúc thảo luận sớm.")
            self.stop() 
        return False 

class HunterView(View):
    def __init__(self, game, hunter):
        super().__init__(timeout=15)
        self.target = None
        self.hunter = hunter
        self.has_interacted = False # Thêm cờ tương tác cho thợ săn
        options = [discord.SelectOption(label=p.display_name, value=str(p.id)) for p in game.alive_players if p.id != hunter.id]
        select = Select(placeholder="Kéo ai theo...", options=options)
        select.callback = self.cb
        self.add_item(select)
    async def cb(self, interaction):
        if interaction.user.id != self.hunter.id: return
        self.has_interacted = True # Đánh dấu đã dùng
        self.target = discord.utils.get(interaction.guild.members, id=int(interaction.data['values'][0]))
        await interaction.response.send_message("Đã chọn!", ephemeral=True)
        self.stop()