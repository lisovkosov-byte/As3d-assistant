import json
import os
import re
import webbrowser
import requests
from typing import Callable, Optional
from presets_manager import PresetsManager
from chat_manager import ChatManager

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
CONFIG_EXAMPLE_FILE = os.path.join(os.path.dirname(__file__), "config.example.json")

class AstridCore:
    def __init__(self, presets_manager: PresetsManager, logger_callback: Optional[Callable[[str, str], None]] = None):
        self.presets = presets_manager
        self.chat = ChatManager()
        self.logger = logger_callback or (lambda text, tag: print(f"[{tag}] {text}"))
        self.config = self.load_config()
        self.gemini_client = None
        self.init_ai()

    def load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки config.json: {e}")

        if os.path.exists(CONFIG_EXAMPLE_FILE):
            try:
                with open(CONFIG_EXAMPLE_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.config = cfg
                    self.save_config()
                    return cfg
            except Exception:
                pass

        return {
            "assistant_name": "Ас3д (Астрид)",
            "provider": "gemini",
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model_name": "gemini-2.5-flash",
            "system_prompt": "Ты — Ас3д (Астрид), дружелюбная, сообразительная и живая девушка-ассистент в стиле хакерского терминала. Отвечай кратко, с легким характером и по делу."
        }

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения config.json: {e}")

    def update_settings(self, provider: str, api_key: str, model_name: str, base_url: str, system_prompt: str) -> bool:
        self.config["provider"] = provider.strip()
        self.config["api_key"] = api_key.strip()
        self.config["model_name"] = model_name.strip()
        self.config["base_url"] = base_url.strip()
        self.config["system_prompt"] = system_prompt.strip()
        self.save_config()
        return self.init_ai()

    def init_ai(self) -> bool:
        key = self.config.get("api_key", "").strip()
        provider = self.config.get("provider", "gemini").lower().strip()

        if not key:
            self.gemini_client = None
            return False

        if provider == "gemini":
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=key)
                return True
            except Exception as e:
                self.logger(f"Ошибка инициализации Gemini: {e}", "error")
                self.gemini_client = None
                return False
        else:
            return True

    def is_ai_ready(self) -> bool:
        key = self.config.get("api_key", "").strip()
        if not key:
            return False
        provider = self.config.get("provider", "gemini").lower().strip()
        if provider == "gemini":
            return self.gemini_client is not None
        return True

    def process_message(self, user_text: str) -> str:
        text_clean = user_text.strip().lower()

        # Сохраняем сообщение пользователя в историю
        self.chat.add_message("User", user_text, tag="user")

        # 1. Проверяем пресеты и их триггеры
        matched_preset = self.presets.find_by_text(text_clean)
        if matched_preset:
            self.logger(f"Обнаружен пресет по триггеру: '{matched_preset}'", "system")
            success = self.presets.execute(matched_preset, logger=self.logger)
            p_data = self.presets.get_preset(matched_preset)
            title = p_data.get("title", matched_preset) if p_data else matched_preset
            reply = f"Пресет '{title}' успешно запущен!" if success else f"Возникла ошибка при выполнении пресета '{title}'."
            self.chat.add_message("Астрид", reply, tag="astrid")
            return reply

        # 2. Если нейросеть настроена — спрашиваем её с учетом памяти диалога
        if self.is_ai_ready():
            reply = self._query_ai(user_text)
        else:
            # 3. Локальный режим
            reply = self._local_fallback_response(user_text)

        self.chat.add_message("Астрид", reply, tag="astrid")
        return reply

    def _build_full_system_prompt(self) -> str:
        base_prompt = self.config.get("system_prompt", "Ты — Ас3д (Астрид), голосовой ассистент.")
        all_presets = self.presets.get_all()

        presets_info = []
        for k, v in all_presets.items():
            title = v.get("title", k)
            desc = v.get("description", "")
            trigs = ", ".join(v.get("triggers", []))
            presets_info.append(f"- Код: '{k}', Название: '{title}', Описание: '{desc}', Ключевые слова: [{trigs}]")

        presets_str = "\n".join(presets_info) if presets_info else "Нет доступных пресетов."

        full_prompt = (
            f"{base_prompt}\n\n"
            f"=== СПИСОК ДОСТУПНЫХ В СИСТЕМЕ ПРЕСЕТОВ ===\n"
            f"{presets_str}\n\n"
            f"=== ПРАВИЛА ВЫПОЛНЕНИЯ КОМАНД ===\n"
            f"1. Если пользователь явно или по смыслу просит запустить программу, сайт или пресет (например: 'включи ютуб', 'открой телегу', 'запусти рабочее место'), "
            f"ОБЯЗАТЕЛЬНО начни свой ответ с метки: [[RUN_PRESET: код_пресета]].\n"
            f"2. После метки напиши короткий, живой ответ пользователю.\n"
            f"3. Если пользователь просто общается или задает вопросы — отвечай в образе Астрид без всяких меток.\n"
            f"4. Помни контекст предыдущего разговора."
        )
        return full_prompt

    def _query_ai(self, user_text: str) -> str:
        provider = self.config.get("provider", "gemini").lower().strip()
        system_prompt = self._build_full_system_prompt()
        history = self.chat.get_context_for_ai(max_turns=6)

        try:
            if provider == "gemini":
                model_name = self.config.get("model_name", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

                # Формируем контекст с историей для Gemini
                context_lines = []
                for h in history[:-1]:  # без текущего последнего сообщения
                    role_name = "Пользователь" if h["role"] == "user" else "Астрид"
                    context_lines.append(f"{role_name}: {h['text']}")

                history_context = "\n".join(context_lines)
                if history_context:
                    prompt = f"{system_prompt}\n\n--- Предыдущий контекст разговора ---\n{history_context}\n\nПользователь: {user_text}\nАстрид:"
                else:
                    prompt = f"{system_prompt}\n\nПользователь: {user_text}\nАстрид:"

                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                ans = response.text or ""
            else:
                # OpenAI-совместимый API
                base_url = self.config.get("base_url", "https://api.openai.com/v1").rstrip("/")
                api_key = self.config.get("api_key", "").strip()
                model_name = self.config.get("model_name", "gpt-4o-mini").strip() or "gpt-4o-mini"

                messages = [{"role": "system", "content": system_prompt}]
                for h in history[:-1]:
                    role = "user" if h["role"] == "user" else "assistant"
                    messages.append({"role": role, "content": h["text"]})
                messages.append({"role": "user", "content": user_text})

                endpoint = f"{base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": 0.7
                }
                res = requests.post(endpoint, headers=headers, json=payload, timeout=20)
                if res.status_code != 200:
                    raise Exception(f"HTTP {res.status_code}: {res.text}")
                data = res.json()
                ans = data["choices"][0]["message"]["content"]

            match = re.search(r"\[\[RUN_PRESET:\s*([a-zA-Z0-9_-]+)\]\]", ans)
            if match:
                preset_key = match.group(1).lower().strip()
                self.logger(f"ИИ активировал пресет: '{preset_key}'", "system")
                self.presets.execute(preset_key, logger=self.logger)
                ans = re.sub(r"\[\[RUN_PRESET:\s*[a-zA-Z0-9_-]+\]\]", "", ans).strip()

            return ans

        except Exception as e:
            self.logger(f"Ошибка обращения к ИИ ({provider}): {e}", "error")
            return f"Ошибка соединения с ИИ: {e}"

    def _local_fallback_response(self, text: str) -> str:
        t = text.lower().strip()

        if any(w in t for w in ["привет", "хай", "здравствуй", "салют"]):
            return "Привет! Я Астрид. В локальном режиме умею мгновенно запускать твои пресеты. Чтобы поболтать с ИИ — укажи ключ в настройках [⚙ Настройки ИИ]."

        if any(w in t for w in ["кто ты", "что ты", "твое имя", "твоё имя"]):
            return "Я Ас3д (Астрид) — твой персональный голосовой кибер-помощник."

        if "открой" in t:
            match = re.search(r"открой\s+(https?://\S+|\S+\.\S+)", t)
            if match:
                url = match.group(1)
                if not url.startswith("http"):
                    url = "https://" + url
                self.logger(f"Открытие ссылки: {url}", "action")
                webbrowser.open(url)
                return f"Открываю: {url}"

            query = t.replace("открой", "").strip()
            if query:
                url = f"https://www.google.com/search?q={query}"
                self.logger(f"Поиск в Google: {query}", "action")
                webbrowser.open(url)
                return f"Ищу в интернете: {query}"

        return "Команда не распознана локально. Добавь пресет для этого действия или введи API-ключ в настройках, чтобы активировать интеллект!"
