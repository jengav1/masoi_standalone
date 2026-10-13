// frontend/src/games/masoi/ui.js
import './masoi.css';
/**
 * UI Renderer cho Ma Sói Activity — Làng Sương Mù (Mục 4, 5, 9, 10).
 * Bám đúng chuẩn Preview:
 * - Nền làng 3D Low-Poly ngày / đêm (village-day.jpg, village-night.jpg)
 * - Lửa trại trung tâm và embers
 * - Vòng tròn avatar người chơi với góc nhìn tự nhiên
 * - Thẻ vai cá nhân có hiệu ứng lật và cất thẻ
 * - Chat làng và Hang Sói riêng biệt theo quyền
 * - Bảng vote, bầu trưởng làng và tổng kết kết quả
 */

export function initMasoiUI(container) {
  let currentState = null;
  let selectedTarget = null;
  let activeJournalTab = 'chat';
  let sendCallback = null;

  // Cấu trúc DOM Ma Sói Activity chuẩn theo Preview Reference
  container.innerHTML = `
    <div id="masoi-agrou-activity">
      <div class="am-window">
        <header class="am-header">
          <div class="am-brand">
            <span class="am-brand-mark" aria-hidden="true">🐺</span>
            <div>
              <h2>MA SÓI</h2>
              <small>CRAZY GAME · LÀNG SƯƠNG MÙ</small>
            </div>
          </div>
          <div class="am-header-actions">
            <span class="am-occupancy"><span data-count>0</span> / 12</span>
            <button type="button" class="am-icon-button" data-action="sound" aria-label="Âm nền">🔊</button>
            <button type="button" class="am-icon-button" data-action="rules" aria-label="Luật phòng">📖</button>
          </div>
        </header>

        <div class="am-stage">
          <div class="am-world-column">
            <section class="am-world" aria-label="Vòng lửa trại Làng Sương Mù">
              <div class="am-scenery am-day-scenery"></div>
              <div class="am-scenery am-night-scenery"></div>
              <div class="am-location">🌲 Làng Sương Mù</div>
              <div class="am-turn">
                <span data-turn>Chờ bắt đầu...</span>
                <span>·</span>
                <strong data-timer>--:--</strong>
              </div>
              <div class="am-scene-title">
                <h3 data-scene-title>Hội đồng làng</h3>
                <p data-scene-sub>Hãy cảnh giác với những kẻ ẩn mình trong bóng tối...</p>
              </div>

              <!-- Danh sách ghế ngồi quanh lửa trại -->
              <div class="am-seats"></div>

              <!-- Lửa trại trung tâm -->
              <div class="am-embers" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
              <button type="button" class="am-fire" data-action="skip" aria-label="Phiếu trắng">
                <span>🏳️ Phiếu trắng</span>
              </button>

              <div class="am-bottom-hint">
                <span data-hint>Bấm avatar để chọn mục tiêu · Bấm lửa trại để bỏ qua</span>
              </div>
            </section>

            <!-- Thanh vai trò cá nhân & Thao tác hành động -->
            <div class="am-role-bar">
              <button type="button" class="am-private-role" data-action="role">
                <span class="am-role-visual" aria-hidden="true">❓</span>
                <span>
                  <small>🔒 Vai của bạn</small>
                  <strong data-my-role-name>Thẻ bí mật</strong>
                  <em>Chạm để xem</em>
                </span>
              </button>

              <div class="am-action-content">
                <div class="am-action-title" data-action-title>Chờ lượt hành động...</div>
                <div class="am-action-row">
                  <div class="am-selection" data-selection>Chưa chọn ai</div>
                  <button type="button" class="am-primary" data-action="confirm" disabled>Xác nhận</button>
                </div>
                <div class="am-status" data-status></div>
              </div>
            </div>
          </div>

          <!-- Bảng Chat & Diễn biến -->
          <aside class="am-journal">
            <div class="am-journal-top">
              <h3>Lời của làng</h3>
              <span data-alive>--</span>
            </div>
            <div class="am-journal-tabs">
              <button type="button" class="active" data-journal="chat">Trò chuyện</button>
              <button type="button" data-journal="log">Diễn biến</button>
            </div>
            <div class="am-journal-content" data-journal-content></div>

            <form class="am-chat-form">
              <div class="am-chat-channel-select" style="display:none; margin-bottom:4px;">
                <label style="font-size:11px; color:#d6b479;">Kênh: </label>
                <select data-chat-channel style="background:#151f1e; color:#f1eadc; border:1px solid #3d4841; border-radius:4px; font-size:11px;">
                  <option value="village">Làng</option>
                  <option value="wolves">Hang Sói 🐺</option>
                </select>
              </div>
              <input aria-label="Tin nhắn" maxlength="160" placeholder="Nói với làng…" autocomplete="off">
              <button type="submit" aria-label="Gửi">➤</button>
            </form>

            <div class="am-room-deck">
              <div class="am-room-deck-title">
                <span>Bộ bài</span>
                <button type="button" data-action="deck">Chi tiết</button>
              </div>
              <div class="am-deck-mini" data-deck-mini></div>
            </div>
          </aside>
        </div>

        <footer class="am-footer">
          <span>Discord Activity</span>
          <span>·</span>
          <span data-footer-status>Đang kết nối...</span>
          <div class="am-reactions">
            <button type="button" data-reaction="👀">👀</button>
            <button type="button" data-reaction="🤔">🤔</button>
            <button type="button" data-reaction="😂">😂</button>
            <button type="button" data-reaction="💀">💀</button>
          </div>
        </footer>

        <!-- Modal chi tiết vai / luật -->
        <div class="am-modal-layer" hidden>
          <section class="am-modal">
            <button type="button" class="am-close" data-action="close">✕</button>
            <div data-modal-content></div>
          </section>
        </div>
      </div>
    </div>
  `;

  const root = container.querySelector('#masoi-agrou-activity');
  const seatsEl = root.querySelector('.am-seats');
  const journalContentEl = root.querySelector('[data-journal-content]');
  const chatForm = root.querySelector('.am-chat-form');
  const chatInput = chatForm.querySelector('input');
  const chatChannelSelect = chatForm.querySelector('[data-chat-channel]');
  const confirmBtn = root.querySelector('[data-action="confirm"]');
  const modalLayer = root.querySelector('.am-modal-layer');
  const modalContent = root.querySelector('[data-modal-content]');

  // Thiết lập ảnh nền Làng Sương Mù từ asset đã trích xuất
  root.querySelector('.am-day-scenery').style.backgroundImage = 'url("/.proxy/masoi/village-day.jpg")';
  root.querySelector('.am-night-scenery').style.backgroundImage = 'url("/.proxy/masoi/village-night.jpg")';

  // Toggle Chat Tabs
  root.querySelectorAll('[data-journal]').forEach(btn => {
    btn.addEventListener('click', () => {
      root.querySelectorAll('[data-journal]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeJournalTab = btn.dataset.journal;
      renderJournal();
    });
  });

  // Modal Close
  root.querySelector('[data-action="close"]').addEventListener('click', () => {
    modalLayer.hidden = true;
  });

  // Xem thẻ bài cá nhân
  root.querySelector('[data-action="role"]').addEventListener('click', () => {
    if (!currentState || !currentState.me) return;
    const me = currentState.me;
    modalContent.innerHTML = `
      <h3>${me.role_emoji || '❓'} ${me.role_name || 'Vai của bạn'}</h3>
      <p style="color:#e2c894; margin:8px 0;">Phe: <strong>${me.team === 'werewolf' ? 'Ma Sói 🐺' : 'Dân Làng 👨‍🌾'}</strong></p>
      <div class="am-secret-art" style="font-size:54px; text-align:center; padding:18px 0;">${me.role_emoji || '❓'}</div>
      <p style="margin-top:14px; line-height:1.6; font-size:13px;">${me.role_desc || 'Chưa phân vai.'}</p>
      <button type="button" class="am-primary" style="margin-top:16px; width:100%; padding:10px;" onclick="this.closest('.am-modal-layer').hidden=true">Cất thẻ</button>
    `;
    modalLayer.hidden = false;
  });

  // Gửi Chat
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text || !sendCallback) return;
    const channel = chatChannelSelect.value || 'village';
    sendCallback({
      kind: 'chat',
      channel: channel,
      text: text
    });
    chatInput.value = '';
  });

  // Nút Xác Nhận / Sẵn Sàng / Bắt Đầu
  confirmBtn.addEventListener('click', () => {
    if (!sendCallback || !currentState) return;
    const me = currentState.me || {};
    const phase = currentState.phase || 'LOBBY';

    if (phase === 'LOBBY') {
      if (me.is_host) {
        sendCallback({ kind: 'start' });
      } else {
        sendCallback({ kind: 'ready', ready: !me.ready });
      }
      return;
    }

    const actions = me.available_actions || [];
    if (actions.includes('vote')) {
      sendCallback({ kind: 'vote', target_id: selectedTarget });
    } else if (actions.includes('wolf_vote')) {
      sendCallback({ kind: 'wolf_vote', target_id: selectedTarget });
    } else if (actions.includes('seer_inspect')) {
      sendCallback({ kind: 'seer_inspect', target_id: selectedTarget });
    } else if (actions.includes('guard_protect')) {
      sendCallback({ kind: 'guard_protect', target_id: selectedTarget });
    } else if (actions.includes('hunter_shoot')) {
      sendCallback({ kind: 'hunter_shoot', target_id: selectedTarget });
    } else if (actions.includes('witch_heal')) {
      sendCallback({ kind: 'witch_action', heal: true });
    }

    selectedTarget = null;
    confirmBtn.disabled = true;
    root.querySelector('[data-selection]').textContent = 'Đã gửi hành động!';
  });

  // Bấm vào Lửa Trại (Phiếu trắng)
  root.querySelector('[data-action="skip"]').addEventListener('click', () => {
    selectedTarget = null;
    root.querySelector('[data-selection]').textContent = '🏳️ Phiếu trắng';
    confirmBtn.disabled = false;
    updateSeatSelectionUI();
  });

  function updateSeatSelectionUI() {
    seatsEl.querySelectorAll('.am-seat').forEach(st => {
      const uid = Number(st.dataset.uid);
      if (uid === selectedTarget) {
        st.classList.add('am-selected');
      } else {
        st.classList.remove('am-selected');
      }
    });
  }

  function renderJournal() {
    if (!currentState) return;
    journalContentEl.innerHTML = '';

    if (activeJournalTab === 'chat') {
      const messages = currentState.chat || [];
      messages.forEach(m => {
        const row = document.createElement('div');
        row.className = 'am-chat-msg';
        const isWolf = (m.channel === 'wolves');
        row.innerHTML = `
          <strong style="color:${isWolf ? '#e74c3c' : '#d6b479'}; font-size:11px;">
            ${isWolf ? '[Hang Sói] ' : ''}${m.sender_name}:
          </strong>
          <span style="font-size:12px; color:#f1eadc;">${m.text}</span>
        `;
        journalContentEl.appendChild(row);
      });
      journalContentEl.scrollTop = journalContentEl.scrollHeight;
    } else {
      const events = currentState.recap_events || [];
      events.forEach(ev => {
        const item = document.createElement('div');
        item.className = 'am-log-item';
        item.textContent = ev;
        journalContentEl.appendChild(item);
      });
      journalContentEl.scrollTop = journalContentEl.scrollHeight;
    }
  }

  // Cập nhật State từ WebSocket Snapshot
  function applyState(state) {
    currentState = state;
    const me = state.me || {};
    const seats = state.seats || [];
    const phase = state.phase || 'LOBBY';

    // 1. Cập nhật ngày / đêm (Scenery Transition)
    const isNight = (phase === 'NIGHT');
    root.querySelector('.am-night-scenery').style.opacity = isNight ? '1' : '0';
    root.querySelector('.am-day-scenery').style.opacity = isNight ? '0' : '1';

    // 2. Tiêu đề cảnh & Thời gian
    root.querySelector('[data-count]').textContent = seats.length;
    root.querySelector('[data-alive]').textContent = `${seats.filter(s => s.alive).length} còn sống`;
    
    let phaseTitle = 'Sảnh chờ';
    let phaseSub = 'Chờ đủ người sẵn sàng và chủ phòng bắt đầu...';
    let turnText = `Ngày ${state.day_number || 1}`;

    if (phase === 'LOBBY') {
      phaseTitle = 'Vòng tròn Sảnh Chờ';
      phaseSub = 'Bấm Sẵn sàng để chuẩn bị bước vào ván đấu.';
      turnText = 'Sảnh chờ';
    } else if (phase === 'ROLE_REVEAL') {
      phaseTitle = 'Phân chia vai trò';
      phaseSub = 'Hãy chạm vào thẻ bí mật để xem vai của bạn.';
      turnText = 'Nhận vai';
    } else if (phase === 'NIGHT') {
      turnText = `🌙 Đêm ${state.day_number}`;
      phaseTitle = `Đêm buông xuống · ${state.night_subphase || ''}`;
      phaseSub = 'Dân làng đang ngủ... Các thế lực bóng tối đang hành động.';
    } else if (phase === 'DAY_DISCUSSION') {
      turnText = `☀️ Ngày ${state.day_number}`;
      phaseTitle = 'Hội đồng tranh luận';
      phaseSub = 'Hãy đối chiếu lời khai và tìm ra kẻ đáng nghi!';
    } else if (phase === 'DAY_VOTE') {
      turnText = `⚖️ Bỏ phiếu Ngày ${state.day_number}`;
      phaseTitle = 'Biểu quyết treo cổ';
      phaseSub = 'Chọn người bạn muốn loại bỏ hoặc bấm lửa trại để bỏ qua.';
    } else if (phase === 'HUNTER_REACTION') {
      phaseTitle = 'Phát súng của Thợ Săn';
      phaseSub = 'Thợ Săn đang nhắm bắn một kẻ theo cùng trước khi gục ngã!';
    } else if (phase === 'FINISHED') {
      phaseTitle = 'Vụ án kết thúc';
      phaseSub = state.winner_team === 'werewolf' ? '🏆 Phe Ma Sói chiến thắng!' : '🏆 Phe Dân Làng chiến thắng!';
    }

    root.querySelector('[data-turn]').textContent = turnText;
    root.querySelector('[data-scene-title]').textContent = phaseTitle;
    root.querySelector('[data-scene-sub]').textContent = phaseSub;

    // 3. Render danh sách ghế tròn quanh lửa trại
    seatsEl.innerHTML = '';
    const totalSeats = Math.max(seats.length, 8);
    const radiusX = 40; // %
    const radiusY = 32; // %

    seats.forEach((seat, idx) => {
      const angle = (idx / totalSeats) * (2 * Math.PI) - Math.PI / 2;
      const left = 50 + radiusX * Math.cos(angle);
      const top = 50 + radiusY * Math.sin(angle);

      const seatEl = document.createElement('div');
      seatEl.className = `am-seat ${seat.alive ? '' : 'am-dead'}`;
      seatEl.dataset.uid = seat.uid;
      seatEl.style.left = `${left}%`;
      seatEl.style.top = `${top}%`;

      const avatarSrc = seat.avatar_url || 'https://cdn.discordapp.com/embed/avatars/0.png';
      seatEl.innerHTML = `
        <div class="am-avatar-wrap">
          <img src="${avatarSrc}" alt="${seat.name}">
          ${seat.is_mayor ? '<span class="am-crown">👑</span>' : ''}
          ${!seat.alive ? '<span class="am-skull">💀</span>' : ''}
        </div>
        <span class="am-name">${seat.name}</span>
        ${seat.public_role ? `<small style="font-size:9px; color:#c5acf1;">${seat.public_role}</small>` : ''}
      `;

      // Chọn mục tiêu khi click avatar
      seatEl.addEventListener('click', () => {
        if (!seat.alive) return;
        selectedTarget = seat.uid;
        root.querySelector('[data-selection]').textContent = `Đã chọn: ${seat.name}`;
        confirmBtn.disabled = false;
        updateSeatSelectionUI();
      });

      seatsEl.appendChild(seatEl);
    });

    // 4. Cập nhật thẻ vai
    if (me.role_name) {
      root.querySelector('[data-my-role-name]').textContent = me.role_name;
      root.querySelector('.am-role-visual').textContent = me.role_emoji || '❓';
    }

    // 5. Cập nhật nút điều khiển theo pha
    if (phase === 'LOBBY') {
      root.querySelector('[data-action-title]').textContent = me.is_host ? 'Chủ phòng điều khiển' : 'Trạng thái sẵn sàng';
      confirmBtn.textContent = me.is_host ? 'Bắt đầu ván' : (me.ready ? 'Hủy sẵn sàng' : 'Sẵn sàng');
      confirmBtn.disabled = false;
    } else {
      root.querySelector('[data-action-title]').textContent = 'Hành động của bạn';
      confirmBtn.textContent = 'Xác nhận';
      confirmBtn.disabled = (selectedTarget === null);
    }

    // 6. Hiển thị kênh Hang Sói nếu là Sói
    if (me.team === 'werewolf') {
      chatChannelSelect.parentElement.style.display = 'block';
    } else {
      chatChannelSelect.parentElement.style.display = 'none';
      chatChannelSelect.value = 'village';
    }

    renderJournal();
  }

  // Timer đếm ngược mượt mà mỗi giây
  setInterval(() => {
    if (!currentState || !currentState.deadline_at) return;
    const rem = Math.max(0, Math.ceil(currentState.deadline_at - Date.now() / 1000));
    const mins = String(Math.floor(rem / 60)).padStart(2, '0');
    const secs = String(rem % 60).padStart(2, '0');
    const timerEl = root.querySelector('[data-timer]');
    if (timerEl) timerEl.textContent = `${mins}:${secs}`;
  }, 1000);

  return {
    apply: applyState,
    bindSend: (cb) => { sendCallback = cb; },
    connected: (ok, msg) => {
      const st = root.querySelector('[data-footer-status]');
      if (st) st.textContent = ok ? 'Đã kết nối máy chủ' : (msg || 'Đang kết nối...');
    }
  };
}
