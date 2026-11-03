import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import time
import os
from presets_manager import PresetsManager
from assistant import AstridCore
from voice_engine import VoiceEngine

BG_DARK = "#070b07"
BG_PANEL = "#0c140d"
BG_INPUT = "#0f1c10"
BG_CARD = "#0d180f"
TEXT_GREEN = "#00ff66"
TEXT_DIM = "#4d995c"
TEXT_WHITE = "#e0ffe5"
ACCENT_CYAN = "#00f0ff"
ACCENT_YELLOW = "#ffcc00"
ACCENT_RED = "#ff4455"
BORDER_COLOR = "#1b4d24"
BORDER_HIGHLIGHT = "#00ff66"

FONT_MONO = ("Consolas", 10)
FONT_BOLD = ("Consolas", 10, "bold")
FONT_TITLE = ("Consolas", 12, "bold")
FONT_SMALL = ("Consolas", 8)

class AstridUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Ас3д (Astrid) // Terminal OS")
        self.root.geometry("1020x660")
        self.root.minsize(860, 540)
        self.root.configure(bg=BG_DARK)

        self.presets = PresetsManager()
        self.core = AstridCore(self.presets, logger_callback=self.log_terminal)
        self.voice_output_enabled = True
        self.voice = VoiceEngine(on_user_speech=self._on_voice_user_speech, on_status=self._on_voice_status)

        self._build_ui()
        self._refresh_presets_list()
        self.root.after(300, self._startup_sequence)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # 1. Шапка (Header)
        header_frame = tk.Frame(self.root, bg=BG_PANEL, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_lbl = tk.Label(
            header_frame,
            text="[ АС3Д // ASTRID CORE v1.2 ]",
            font=FONT_TITLE,
            fg=TEXT_GREEN,
            bg=BG_PANEL
        )
        title_lbl.pack(side="left", padx=15, pady=8)

        self.status_lbl = tk.Label(
            header_frame,
            text="● ИНИЦИАЛИЗАЦИЯ...",
            font=FONT_BOLD,
            fg=ACCENT_CYAN,
            bg=BG_PANEL
        )
        self.status_lbl.pack(side="left", padx=15, pady=8)

        # Кнопки в шапке
        btn_settings = tk.Button(
            header_frame,
            text="[ ⚙ НАСТРОЙКИ ИИ И КЛЮЧЕЙ ]",
            font=FONT_BOLD,
            fg=TEXT_GREEN,
            bg=BG_DARK,
            activebackground=TEXT_GREEN,
            activeforeground=BG_DARK,
            bd=1,
            relief="solid",
            command=self._open_settings_dialog,
            cursor="hand2",
            padx=10,
            pady=4
        )
        btn_settings.pack(side="right", padx=10, pady=6)

        btn_donate = tk.Button(
            header_frame,
            text="[ ☕ ДОНАТ ]",
            font=FONT_BOLD,
            fg=ACCENT_YELLOW,
            bg=BG_DARK,
            activebackground=ACCENT_YELLOW,
            activeforeground=BG_DARK,
            bd=1,
            relief="solid",
            command=self._open_donate,
            cursor="hand2",
            padx=8,
            pady=4
        )
        btn_donate.pack(side="right", padx=(0, 5), pady=6)

        self.btn_tts_toggle = tk.Button(
            header_frame,
            text="[ 🔊 ОЗВУЧКА: ВКЛ ]",
            font=FONT_BOLD,
            fg=TEXT_GREEN,
            bg=BG_DARK,
            activebackground=TEXT_GREEN,
            activeforeground=BG_DARK,
            bd=1,
            relief="solid",
            command=self._toggle_tts,
            cursor="hand2",
            padx=8,
            pady=4
        )
        self.btn_tts_toggle.pack(side="right", padx=(0, 5), pady=6)

        # 2. Главная область
        main_content = tk.Frame(self.root, bg=BG_DARK)
        main_content.pack(fill="both", expand=True, padx=10, pady=5)

        # Слева: Терминал
        term_frame = tk.Frame(main_content, bg=BG_PANEL, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        term_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        term_title_frame = tk.Frame(term_frame, bg=BG_PANEL)
        term_title_frame.pack(fill="x", padx=10, pady=(6, 2))
        tk.Label(term_title_frame, text="-- КОНСОЛЬ ВЗАИМОДЕЙСТВИЯ --", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL).pack(side="left")

        btn_new_chat = tk.Button(
            term_title_frame,
            text="[+ Новый диалог]",
            font=FONT_SMALL,
            fg=ACCENT_CYAN,
            bg=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=TEXT_GREEN,
            bd=0,
            cursor="hand2",
            command=self._start_new_chat
        )
        btn_new_chat.pack(side="right", padx=(5, 0))

        btn_clear = tk.Button(
            term_title_frame,
            text="[Очистить экран]",
            font=FONT_SMALL,
            fg=TEXT_DIM,
            bg=BG_PANEL,
            activebackground=BG_PANEL,
            activeforeground=TEXT_GREEN,
            bd=0,
            cursor="hand2",
            command=self._clear_terminal
        )
        btn_clear.pack(side="right")

        scroll = tk.Scrollbar(term_frame)
        scroll.pack(side="right", fill="y", padx=(0, 2), pady=5)

        self.term_text = tk.Text(
            term_frame,
            bg=BG_PANEL,
            fg=TEXT_GREEN,
            insertbackground=TEXT_GREEN,
            font=FONT_MONO,
            wrap="word",
            yscrollcommand=scroll.set,
            bd=0,
            padx=10,
            pady=5
        )
        self.term_text.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.term_text.yview)

        # Стилизация текста
        self.term_text.tag_config("user", foreground=ACCENT_CYAN, font=FONT_BOLD)
        self.term_text.tag_config("astrid", foreground=TEXT_GREEN, font=FONT_BOLD)
        self.term_text.tag_config("system", foreground=TEXT_DIM)
        self.term_text.tag_config("action", foreground=ACCENT_YELLOW)
        self.term_text.tag_config("error", foreground=ACCENT_RED, font=FONT_BOLD)
        self.term_text.tag_config("success", foreground="#33ff88", font=FONT_BOLD)

        # Справа: Панель пресетов
        preset_frame = tk.Frame(main_content, bg=BG_PANEL, width=320, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        preset_frame.pack(side="right", fill="y", padx=(5, 0))
        preset_frame.pack_propagate(False)

        preset_header = tk.Frame(preset_frame, bg=BG_PANEL)
        preset_header.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(preset_header, text="[ РЕДАКТОР ПРЕСЕТОВ ]", font=FONT_BOLD, fg=TEXT_GREEN, bg=BG_PANEL).pack(side="left")

        # Список пресетов со скроллбаром
        p_scroll_frame = tk.Frame(preset_frame, bg=BG_PANEL)
        p_scroll_frame.pack(fill="both", expand=True, padx=6, pady=4)

        p_canvas = tk.Canvas(p_scroll_frame, bg=BG_PANEL, highlightthickness=0)
        p_scrollbar = tk.Scrollbar(p_scroll_frame, orient="vertical", command=p_canvas.yview)
        self.presets_inner_frame = tk.Frame(p_canvas, bg=BG_PANEL)

        self.presets_inner_frame.bind(
            "<Configure>",
            lambda e: p_canvas.configure(scrollregion=p_canvas.bbox("all"))
        )
        p_canvas.create_window((0, 0), window=self.presets_inner_frame, anchor="nw", width=290)
        p_canvas.configure(yscrollcommand=p_scrollbar.set)

        p_canvas.pack(side="left", fill="both", expand=True)
        p_scrollbar.pack(side="right", fill="y")

        # Кнопка добавления нового пресета
        btn_add_preset = tk.Button(
            preset_frame,
            text="+ ДОБАВИТЬ НОВЫЙ ПРЕСЕТ",
            font=FONT_BOLD,
            fg=BG_DARK,
            bg=TEXT_GREEN,
            activebackground=ACCENT_CYAN,
            activeforeground=BG_DARK,
            relief="flat",
            command=lambda: self._open_preset_editor(None),
            cursor="hand2",
            pady=8
        )
        btn_add_preset.pack(fill="x", padx=8, pady=8)

        # 3. Нижняя панель ввода
        input_frame = tk.Frame(self.root, bg=BG_PANEL, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
        input_frame.pack(fill="x", padx=10, pady=(5, 10))

        prompt_lbl = tk.Label(input_frame, text="> ", font=FONT_BOLD, fg=TEXT_GREEN, bg=BG_PANEL)
        prompt_lbl.pack(side="left", padx=(10, 0))

        self.input_entry = tk.Entry(
            input_frame,
            font=FONT_MONO,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=TEXT_GREEN,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightcolor=TEXT_GREEN,
            highlightbackground=BORDER_COLOR
        )
        self.input_entry.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self.input_entry.bind("<Return>", lambda e: self._on_send_message())
        self.input_entry.focus_set()

        btn_send = tk.Button(
            input_frame,
            text="ВВОД ↵",
            font=FONT_BOLD,
            fg=BG_DARK,
            bg=TEXT_GREEN,
            activebackground="#55ff99",
            activeforeground=BG_DARK,
            relief="flat",
            cursor="hand2",
            command=self._on_send_message,
            padx=14,
            pady=4
        )
        btn_send.pack(side="left", padx=(0, 5), pady=8)

        self.btn_live = tk.Button(
            input_frame,
            text="🎙 LIVE (СКАЖИ 'АСТРИД')",
            font=FONT_BOLD,
            fg=TEXT_GREEN,
            bg=BG_DARK,
            activebackground=TEXT_GREEN,
            activeforeground=BG_DARK,
            bd=1,
            relief="solid",
            cursor="hand2",
            command=self._toggle_live_mode,
            padx=10,
            pady=4
        )
        self.btn_live.pack(side="right", padx=(5, 10), pady=8)

        self.btn_mic = tk.Button(
            input_frame,
            text="🎤 СКАЗАТЬ",
            font=FONT_BOLD,
            fg=ACCENT_CYAN,
            bg=BG_DARK,
            activebackground=ACCENT_CYAN,
            activeforeground=BG_DARK,
            bd=1,
            relief="solid",
            cursor="hand2",
            command=self._listen_mic_once,
            padx=8,
            pady=4
        )
        self.btn_mic.pack(side="right", padx=(5, 0), pady=8)

    def log_terminal(self, text: str, tag: str = "system"):
        timestamp = time.strftime("%H:%M:%S")
        self.term_text.config(state="normal")
        self.term_text.insert("end", f"[{timestamp}] ", "system")

        if tag == "user":
            self.term_text.insert("end", f"ВЫ: {text}\n", "user")
        elif tag == "astrid":
            self.term_text.insert("end", f"АС3Д: {text}\n\n", "astrid")
        elif tag == "action":
            self.term_text.insert("end", f"⚡ {text}\n", "action")
        elif tag == "error":
            self.term_text.insert("end", f"✖ {text}\n", "error")
        elif tag == "success":
            self.term_text.insert("end", f"✔ {text}\n", "success")
        else:
            self.term_text.insert("end", f"{text}\n", "system")

        self.term_text.see("end")
        self.term_text.config(state="disabled")

    def _clear_terminal(self):
        self.term_text.config(state="normal")
        self.term_text.delete("1.0", "end")
        self.term_text.config(state="disabled")

    def _start_new_chat(self):
        if messagebox.askyesno("Новый диалог", "Начать новый диалог? Предыдущая история будет очищена."):
            self.core.chat.clear()
            self._clear_terminal()
            self.log_terminal("=== НАЧАТ НОВЫЙ ДИАЛОГ (ПАМЯТЬ ОЧИЩЕНА) ===", "system")
            self.log_terminal("Астрид готова к новому разговору!", "astrid")

    def _load_saved_history(self):
        saved = self.core.chat.get_messages()
        if saved:
            self.term_text.config(state="normal")
            self.term_text.insert("end", "--- СОХРАНЕННАЯ ИСТОРИЯ ДИАЛОГА ---\n", "system")
            for msg in saved:
                ts = msg.get("timestamp", "").split(" ")[-1] if " " in msg.get("timestamp", "") else msg.get("timestamp", "")
                tag = msg.get("tag", "system")
                text = msg.get("text", "")
                self.term_text.insert("end", f"[{ts}] ", "system")
                if tag == "user":
                    self.term_text.insert("end", f"ВЫ: {text}\n", "user")
                elif tag == "astrid":
                    self.term_text.insert("end", f"АС3Д: {text}\n\n", "astrid")
                else:
                    self.term_text.insert("end", f"{text}\n", "system")
            self.term_text.insert("end", "------------------------------------\n\n", "system")
            self.term_text.see("end")
            self.term_text.config(state="disabled")

    def _startup_sequence(self):
        self._load_saved_history()
        self.log_terminal("=== ИНИЦИАЛИЗАЦИЯ СИСТЕМЫ 'АС3Д' ===", "system")
        if self.core.is_ai_ready():
            p_name = self.core.config.get("provider", "ИИ").upper()
            m_name = self.core.config.get("model_name", "")
            self.status_lbl.config(text=f"● {p_name} [{m_name}] ONLINE", fg=TEXT_GREEN)
            self.log_terminal(f"ИИ активен: {p_name} ({m_name}). Память и пресеты подключены.", "success")
        else:
            self.status_lbl.config(text="● ЛОКАЛЬНЫЙ РЕЖИМ (БЕЗ КЛЮЧА)", fg=ACCENT_YELLOW)
            self.log_terminal("Внимание: API-ключ не указан. Запущен локальный режим.", "action")
            self.log_terminal("Пресеты, автозапуск сайтов/программ работают без интернета!", "action")

        self.log_terminal("Астрид на связи. Чем помочь?", "astrid")

    def _refresh_presets_list(self):
        for widget in self.presets_inner_frame.winfo_children():
            widget.destroy()

        all_p = self.presets.get_all()
        if not all_p:
            lbl = tk.Label(self.presets_inner_frame, text="Список пресетов пуст", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL)
            lbl.pack(pady=15)
            return

        for key, data in all_p.items():
            title = data.get("title", key)
            actions = data.get("actions", [])
            triggers = data.get("triggers", [])

            card = tk.Frame(self.presets_inner_frame, bg=BG_CARD, bd=1, relief="solid", highlightbackground=BORDER_COLOR, highlightthickness=1)
            card.pack(fill="x", pady=4, padx=2)

            top_row = tk.Frame(card, bg=BG_CARD)
            top_row.pack(fill="x", padx=6, pady=(4, 2))

            btn_run = tk.Button(
                top_row,
                text=f"▶ {title}",
                font=FONT_BOLD,
                fg=TEXT_GREEN,
                bg=BG_DARK,
                activebackground=TEXT_GREEN,
                activeforeground=BG_DARK,
                relief="flat",
                anchor="w",
                cursor="hand2",
                command=lambda k=key: self._run_preset(k)
            )
            btn_run.pack(side="left", fill="x", expand=True)

            btn_edit = tk.Button(
                top_row,
                text="✏",
                font=FONT_BOLD,
                fg=ACCENT_CYAN,
                bg=BG_DARK,
                relief="flat",
                cursor="hand2",
                command=lambda k=key: self._open_preset_editor(k),
                padx=5
            )
            btn_edit.pack(side="right", padx=(2, 0))

            btn_del = tk.Button(
                top_row,
                text="✖",
                font=FONT_BOLD,
                fg=ACCENT_RED,
                bg=BG_DARK,
                relief="flat",
                cursor="hand2",
                command=lambda k=key, t=title: self._delete_preset(k, t),
                padx=5
            )
            btn_del.pack(side="right", padx=(2, 0))

            # Инфо о действиях
            acts_desc = f"Шагов: {len(actions)}"
            if triggers:
                acts_desc += f" | Слова: {', '.join(triggers[:3])}"
            lbl_info = tk.Label(card, text=acts_desc, font=FONT_SMALL, fg=TEXT_DIM, bg=BG_CARD, anchor="w")
            lbl_info.pack(fill="x", padx=8, pady=(0, 4))

    def _run_preset(self, key: str):
        threading.Thread(target=lambda: self.presets.execute(key, logger=self.log_terminal), daemon=True).start()

    def _delete_preset(self, key: str, title: str):
        if messagebox.askyesno("Удаление", f"Удалить пресет '{title}'?"):
            self.presets.delete_preset(key)
            self._refresh_presets_list()
            self.log_terminal(f"Пресет '{title}' удален.", "system")

    def _on_send_message(self):
        msg = self.input_entry.get().strip()
        if not msg:
            return
        self.input_entry.delete(0, "end")
        self.log_terminal(msg, "user")

        self.status_lbl.config(text="● ДУМАЮ...", fg=ACCENT_YELLOW)

        def task():
            ans = self.core.process_message(msg)
            self.root.after(0, lambda: self._on_assistant_reply(ans))

        threading.Thread(target=task, daemon=True).start()

    def _on_assistant_reply(self, reply: str):
        if self.core.is_ai_ready():
            p_name = self.core.config.get("provider", "ИИ").upper()
            m_name = self.core.config.get("model_name", "")
            self.status_lbl.config(text=f"● {p_name} [{m_name}] ONLINE", fg=TEXT_GREEN)
        else:
            self.status_lbl.config(text="● ЛОКАЛЬНЫЙ РЕЖИМ", fg=ACCENT_YELLOW)
        self.log_terminal(reply, "astrid")

        # Озвучка голосом
        if self.voice_output_enabled:
            self.voice.speak(reply)

    def _toggle_tts(self):
        self.voice_output_enabled = not self.voice_output_enabled
        if self.voice_output_enabled:
            self.btn_tts_toggle.config(text="[ 🔊 ОЗВУЧКА: ВКЛ ]", fg=TEXT_GREEN)
            self.log_terminal("Голосовая озвучка ответов Астрид ВКЛЮЧЕНА", "success")
        else:
            self.voice.stop_speaking()
            self.btn_tts_toggle.config(text="[ 🔇 ОЗВУЧКА: ВЫКЛ ]", fg=TEXT_DIM)
            self.log_terminal("Голосовая озвучка ответов Астрид ВЫКЛЮЧЕНА (без звука)", "system")

    def _toggle_live_mode(self):
        is_active = self.voice.toggle_live()
        if is_active:
            self.btn_live.config(
                text="🎙 LIVE: АКТИВЕН (СКАЖИ 'АСТРИД')",
                bg=TEXT_GREEN,
                fg=BG_DARK
            )
            self.log_terminal("=== LIVE РЕЖИМ ВКЛЮЧЕН ===", "success")
            self.log_terminal("Просто скажите вслух: 'Астрид' или 'Астрид, включи ютуб'!", "action")
        else:
            self.btn_live.config(
                text="🎙 LIVE (СКАЖИ 'АСТРИД')",
                bg=BG_DARK,
                fg=TEXT_GREEN
            )
            self.log_terminal("Live режим выключен.", "system")

    def _listen_mic_once(self):
        self.voice.listen_once()

    def _on_voice_user_speech(self, text: str):
        self.root.after(0, lambda: self._process_voice_speech(text))

    def _process_voice_speech(self, text: str):
        self.log_terminal(text, "user")
        self.status_lbl.config(text="● ДУМАЮ...", fg=ACCENT_YELLOW)

        def task():
            ans = self.core.process_message(text)
            self.root.after(0, lambda: self._on_assistant_reply(ans))

        threading.Thread(target=task, daemon=True).start()

    def _on_voice_status(self, text: str, tag: str):
        color = TEXT_GREEN
        if tag == "accent":
            color = ACCENT_CYAN
        elif tag == "warning":
            color = ACCENT_YELLOW
        elif tag == "error":
            color = ACCENT_RED
        elif tag == "system":
            color = TEXT_DIM

        self.root.after(0, lambda: self.status_lbl.config(text=f"● {text}", fg=color))

    def _open_donate(self):
        import webbrowser
        donate_url = self.core.config.get("donate_url", "https://donatty.com/").strip() or "https://donatty.com/"
        self.log_terminal(f"Открытие страницы поддержки: {donate_url}", "action")
        webbrowser.open(donate_url)

    def _on_close(self):
        self.voice.stop_live()
        self.root.destroy()

    # =========================================================================
    # РЕДАКТОР ПРЕСЕТОВ
    # =========================================================================
    def _open_preset_editor(self, edit_key: str = None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактор пресета // Астрид" if edit_key else "Создание нового пресета // Астрид")
        dialog.geometry("620x560")
        dialog.minsize(560, 480)
        dialog.configure(bg=BG_PANEL)
        dialog.transient(self.root)
        dialog.grab_set()

        existing_data = self.presets.get_preset(edit_key) if edit_key else None
        current_actions = list(existing_data.get("actions", [])) if existing_data else []

        # Заголовок
        header_text = f"РЕДАКТИРОВАНИЕ ПРЕСЕТА: {edit_key}" if edit_key else "СОЗДАНИЕ НОВОГО ПРЕСЕТА"
        tk.Label(dialog, text=header_text, font=FONT_TITLE, fg=TEXT_GREEN, bg=BG_PANEL).pack(pady=(12, 6))

        form_frame = tk.Frame(dialog, bg=BG_PANEL)
        form_frame.pack(fill="x", padx=16, pady=4)

        # Кодовое имя
        tk.Label(form_frame, text="Кодовое имя (на англ., например 'youtube'):", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL).grid(row=0, column=0, sticky="w")
        e_key = tk.Entry(form_frame, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_GREEN)
        e_key.grid(row=1, column=0, sticky="ew", pady=(2, 6))
        if edit_key:
            e_key.insert(0, edit_key)

        # Отображаемое название
        tk.Label(form_frame, text="Название на кнопке (например 'YouTube + VPN'):", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL).grid(row=2, column=0, sticky="w")
        e_title = tk.Entry(form_frame, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_GREEN)
        e_title.grid(row=3, column=0, sticky="ew", pady=(2, 6))
        if existing_data:
            e_title.insert(0, existing_data.get("title", ""))

        # Триггеры (ключевые слова для голоса и чата)
        tk.Label(form_frame, text="Ключевые фразы через запятую (например 'ютуб, youtube, ютубчик'):", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL).grid(row=4, column=0, sticky="w")
        e_triggers = tk.Entry(form_frame, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_GREEN)
        e_triggers.grid(row=5, column=0, sticky="ew", pady=(2, 6))
        if existing_data:
            e_triggers.insert(0, ", ".join(existing_data.get("triggers", [])))

        form_frame.columnconfigure(0, weight=1)

        # Список шагов / действий
        act_box_frame = tk.Frame(dialog, bg=BG_PANEL)
        act_box_frame.pack(fill="both", expand=True, padx=16, pady=4)

        tk.Label(act_box_frame, text="Список действий (выполняются по очереди):", font=FONT_BOLD, fg=TEXT_GREEN, bg=BG_PANEL).pack(anchor="w")

        list_container = tk.Frame(act_box_frame, bg=BG_DARK, bd=1, relief="solid", highlightbackground=BORDER_COLOR)
        list_container.pack(fill="both", expand=True, pady=4)

        act_scroll = tk.Scrollbar(list_container)
        act_scroll.pack(side="right", fill="y")

        act_listbox = tk.Listbox(
            list_container,
            bg=BG_DARK,
            fg=TEXT_WHITE,
            selectbackground=TEXT_GREEN,
            selectforeground=BG_DARK,
            font=FONT_MONO,
            bd=0,
            yscrollcommand=act_scroll.set
        )
        act_listbox.pack(side="left", fill="both", expand=True)
        act_scroll.config(command=act_listbox.yview)

        def refresh_act_listbox():
            act_listbox.delete(0, "end")
            for i, a in enumerate(current_actions, start=1):
                t = a.get("type", "")
                if t == "app":
                    act_listbox.insert("end", f"[{i}] 💻 Запуск программы: {a.get('path', '')}")
                elif t == "url":
                    act_listbox.insert("end", f"[{i}] 🌐 Открыть сайт: {a.get('url', '')}")
                elif t == "wait":
                    act_listbox.insert("end", f"[{i}] ⏳ Пауза: {a.get('seconds', 1)} сек")
                elif t == "cmd":
                    act_listbox.insert("end", f"[{i}] ⚙ Команда CMD: {a.get('command', '')}")
                else:
                    act_listbox.insert("end", f"[{i}] {t}: {a}")

        refresh_act_listbox()

        # Кнопки добавления действий
        btns_row = tk.Frame(act_box_frame, bg=BG_PANEL)
        btns_row.pack(fill="x", pady=4)

        def add_app_action():
            path = filedialog.askopenfilename(
                title="Выберите исполняемый файл (.exe, .bat, ярлык)",
                filetypes=[("Программы", "*.exe;*.bat;*.cmd;*.lnk"), ("Все файлы", "*.*")]
            )
            if path:
                current_actions.append({"type": "app", "path": path})
                refresh_act_listbox()

        def add_url_action():
            url = simpledialog.askstring("Открыть сайт", "Введите адрес сайта (URL):\n(например, https://www.youtube.com)", parent=dialog)
            if url and url.strip():
                u = url.strip()
                if not u.startswith("http"):
                    u = "https://" + u
                current_actions.append({"type": "url", "url": u})
                refresh_act_listbox()

        def add_wait_action():
            sec = simpledialog.askfloat("Пауза", "Сколько секунд подождать? (например 1.5):", parent=dialog, minvalue=0.1, maxvalue=60.0)
            if sec:
                current_actions.append({"type": "wait", "seconds": sec})
                refresh_act_listbox()

        def remove_selected_action():
            sel = act_listbox.curselection()
            if sel:
                idx = sel[0]
                current_actions.pop(idx)
                refresh_act_listbox()

        btn_add_app = tk.Button(btns_row, text="+ 💻 Файл / .exe...", font=FONT_SMALL, fg=TEXT_GREEN, bg=BG_DARK, bd=1, relief="solid", command=add_app_action, cursor="hand2")
        btn_add_app.pack(side="left", padx=2)

        btn_add_url = tk.Button(btns_row, text="+ 🌐 Сайт (URL)...", font=FONT_SMALL, fg=ACCENT_CYAN, bg=BG_DARK, bd=1, relief="solid", command=add_url_action, cursor="hand2")
        btn_add_url.pack(side="left", padx=2)

        btn_add_wait = tk.Button(btns_row, text="+ ⏳ Пауза...", font=FONT_SMALL, fg=ACCENT_YELLOW, bg=BG_DARK, bd=1, relief="solid", command=add_wait_action, cursor="hand2")
        btn_add_wait.pack(side="left", padx=2)

        btn_rem = tk.Button(btns_row, text="✖ Удалить шаг", font=FONT_SMALL, fg=ACCENT_RED, bg=BG_DARK, bd=1, relief="solid", command=remove_selected_action, cursor="hand2")
        btn_rem.pack(side="right", padx=2)

        # Нижние кнопки
        bottom_row = tk.Frame(dialog, bg=BG_PANEL)
        bottom_row.pack(fill="x", padx=16, pady=(6, 14))

        def save_preset():
            key = e_key.get().strip().lower()
            title = e_title.get().strip() or key
            trigs = [t.strip() for t in e_triggers.get().split(",") if t.strip()]

            if not key:
                messagebox.showerror("Ошибка", "Укажите кодовое имя пресета!", parent=dialog)
                return

            if not current_actions:
                messagebox.showerror("Ошибка", "Добавьте хотя бы одно действие в список шагов!", parent=dialog)
                return

            self.presets.save_or_update_preset(
                key=key,
                title=title,
                description=f"Пресет: {title}",
                triggers=trigs,
                actions=current_actions,
                old_key=edit_key
            )
            self._refresh_presets_list()
            self.log_terminal(f"Пресет '{title}' успешно сохранен!", "success")
            dialog.destroy()

        btn_save = tk.Button(
            bottom_row,
            text="💾 СОХРАНИТЬ ПРЕСЕТ",
            font=FONT_BOLD,
            fg=BG_DARK,
            bg=TEXT_GREEN,
            activebackground=ACCENT_CYAN,
            activeforeground=BG_DARK,
            relief="flat",
            command=save_preset,
            cursor="hand2",
            padx=16,
            pady=6
        )
        btn_save.pack(side="left")

        btn_cancel = tk.Button(
            bottom_row,
            text="ОТМЕНА",
            font=FONT_BOLD,
            fg=TEXT_DIM,
            bg=BG_DARK,
            relief="solid",
            bd=1,
            command=dialog.destroy,
            cursor="hand2",
            padx=16,
            pady=6
        )
        btn_cancel.pack(side="right")

    # =========================================================================
    # НАСТРОЙКИ ИИ И ПРОВАЙДЕРОВ (GEMINI, OPENAI, GROQ, OPENROUTER, И Т.Д.)
    # =========================================================================
    def _open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки ИИ и Личности // Астрид")
        dialog.geometry("640x580")
        dialog.minsize(580, 500)
        dialog.configure(bg=BG_PANEL)
        dialog.transient(self.root)
        dialog.grab_set()

        cfg = self.core.config

        tk.Label(dialog, text="НАСТРОЙКИ НЕЙРОСЕТИ И ЛИЧНОСТИ", font=FONT_TITLE, fg=TEXT_GREEN, bg=BG_PANEL).pack(pady=(12, 6))

        scroll_frame = tk.Frame(dialog, bg=BG_PANEL)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=4)

        # Провайдер
        tk.Label(scroll_frame, text="Провайдер нейросети:", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        provider_var = tk.StringVar(value=cfg.get("provider", "gemini"))

        prov_row = tk.Frame(scroll_frame, bg=BG_PANEL)
        prov_row.pack(fill="x", pady=(2, 8))

        r_gemini = tk.Radiobutton(prov_row, text="Google Gemini (Бесплатный ключ)", variable=provider_var, value="gemini", font=FONT_BOLD, fg=TEXT_GREEN, bg=BG_PANEL, selectcolor=BG_DARK, activebackground=BG_PANEL)
        r_gemini.pack(side="left", padx=(0, 15))

        r_openai = tk.Radiobutton(prov_row, text="Любой OpenAI / OpenRouter / DeepSeek / Groq", variable=provider_var, value="openai_compatible", font=FONT_BOLD, fg=TEXT_GREEN, bg=BG_PANEL, selectcolor=BG_DARK, activebackground=BG_PANEL)
        r_openai.pack(side="left")

        # API Ключ
        tk.Label(scroll_frame, text="API-Ключ (хранится локально в config.json, в git НЕ попадёт):", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        e_key = tk.Entry(scroll_frame, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_GREEN, show="*")
        e_key.insert(0, cfg.get("api_key", ""))
        e_key.pack(fill="x", pady=(2, 8))

        # Модель
        tk.Label(scroll_frame, text="Имя модели (напр. 'gemini-2.5-flash', 'gpt-4o-mini', 'deepseek-chat'):", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        e_model = tk.Entry(scroll_frame, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_GREEN)
        e_model.insert(0, cfg.get("model_name", "gemini-2.5-flash"))
        e_model.pack(fill="x", pady=(2, 8))

        # Base URL (только для OpenAI-совместимых)
        tk.Label(scroll_frame, text="Базовый адрес API (Base URL, для OpenRouter / DeepSeek / Ollama):", font=FONT_SMALL, fg=TEXT_DIM, bg=BG_PANEL).pack(anchor="w")
        e_base_url = tk.Entry(scroll_frame, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_GREEN)
        e_base_url.insert(0, cfg.get("base_url", "https://api.openai.com/v1"))
        e_base_url.pack(fill="x", pady=(2, 8))

        # Системный промпт (Личность Астрид)
        tk.Label(scroll_frame, text="Промпт Личности ('Внушение' для нейросети):", font=FONT_BOLD, fg=TEXT_GREEN, bg=BG_PANEL).pack(anchor="w", pady=(4, 2))
        prompt_text = tk.Text(scroll_frame, height=6, font=FONT_MONO, bg=BG_INPUT, fg=TEXT_WHITE, insertbackground=TEXT_GREEN, wrap="word", bd=1, relief="solid")
        prompt_text.insert("1.0", cfg.get("system_prompt", ""))
        prompt_text.pack(fill="both", expand=True, pady=(2, 8))

        # Кнопка сохранения
        def save_settings():
            prov = provider_var.get()
            k = e_key.get().strip()
            m = e_model.get().strip() or ("gemini-2.5-flash" if prov == "gemini" else "gpt-4o-mini")
            u = e_base_url.get().strip()
            sp = prompt_text.get("1.0", "end").strip()

            self.core.update_settings(prov, k, m, u, sp)

            if self.core.is_ai_ready():
                self.status_lbl.config(text=f"● {prov.upper()} [{m}] ONLINE", fg=TEXT_GREEN)
                self.log_terminal(f"Настройки ИИ сохранены! Модель: {prov.upper()} ({m}). Личность обновлена.", "success")
                messagebox.showinfo("Успех", "Настройки сохранены, ИИ активирован!", parent=dialog)
            else:
                self.status_lbl.config(text="● ЛОКАЛЬНЫЙ РЕЖИМ", fg=ACCENT_YELLOW)
                self.log_terminal("Настройки сохранены. ИИ не подключен (ключ пуст или недоступен).", "action")

            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=BG_PANEL)
        btn_row.pack(fill="x", padx=20, pady=(4, 14))

        btn_save = tk.Button(btn_row, text="💾 СОХРАНИТЬ НАСТРОЙКИ", font=FONT_BOLD, fg=BG_DARK, bg=TEXT_GREEN, relief="flat", command=save_settings, cursor="hand2", padx=16, pady=6)
        btn_save.pack(side="left")

        btn_cancel = tk.Button(btn_row, text="ОТМЕНА", font=FONT_BOLD, fg=TEXT_DIM, bg=BG_DARK, relief="solid", bd=1, command=dialog.destroy, cursor="hand2", padx=16, pady=6)
        btn_cancel.pack(side="right")


def main():
    root = tk.Tk()
    app = AstridUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
