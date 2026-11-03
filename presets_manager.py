import json
import os
import subprocess
import time
import webbrowser
from typing import Callable, Optional, Dict, Any, List
import input_automation as ia

PRESETS_FILE = os.path.join(os.path.dirname(__file__), "presets.json")

class PresetsManager:
    def __init__(self, filepath: str = PRESETS_FILE):
        self.filepath = filepath
        self.presets: Dict[str, Any] = {}
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.presets = data.get("presets", {})
            except Exception as e:
                print(f"Ошибка загрузки пресетов: {e}")
                self.presets = {}
        else:
            self.presets = self._get_default_presets()
            self.save()

    def _get_default_presets(self) -> Dict[str, Any]:
        return {
            "youtube": {
                "title": "YouTube",
                "description": "Запуск VPN/программы и открытие YouTube",
                "triggers": ["ютуб", "youtube", "ютубчик"],
                "actions": [
                  {
                    "type": "app",
                    "path": "happ.exe"
                  },
                  {
                    "type": "wait",
                    "seconds": 1
                  },
                  {
                    "type": "url",
                    "url": "https://www.youtube.com"
                  }
                ]
            },
            "telegram": {
                "title": "Telegram",
                "description": "Открыть Telegram Web",
                "triggers": ["телеграм", "тг", "telegram"],
                "actions": [
                  {
                    "type": "url",
                    "url": "https://web.telegram.org"
                  }
                ]
            }
        }

    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({"presets": self.presets}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения пресетов: {e}")

    def get_all(self) -> Dict[str, Any]:
        return self.presets

    def get_preset(self, key: str) -> Optional[Dict[str, Any]]:
        return self.presets.get(key.lower().strip())

    def save_or_update_preset(self, key: str, title: str, description: str, triggers: List[str], actions: List[Dict[str, Any]], old_key: Optional[str] = None):
        clean_key = key.lower().strip()
        if old_key and old_key.lower().strip() != clean_key:
            if old_key.lower().strip() in self.presets:
                del self.presets[old_key.lower().strip()]

        self.presets[clean_key] = {
            "title": title.strip() or clean_key,
            "description": description.strip(),
            "triggers": [t.strip().lower() for t in triggers if t.strip()],
            "actions": actions
        }
        self.save()

    def delete_preset(self, key: str) -> bool:
        k = key.lower().strip()
        if k in self.presets:
            del self.presets[k]
            self.save()
            return True
        return False

    def find_by_text(self, text: str) -> Optional[str]:
        t = text.lower()
        # Сначала проверяем точные ключи
        for key, data in self.presets.items():
            if key in t:
                return key
            # Проверяем триггеры
            triggers = data.get("triggers", [])
            for trig in triggers:
                if trig and trig in t:
                    return key
        return None

    def execute(self, key: str, logger: Optional[Callable[[str, str], None]] = None) -> bool:
        k = key.lower().strip()
        if k not in self.presets:
            if logger:
                logger(f"Пресет '{key}' не найден в базе данных.", "error")
            return False

        preset = self.presets[k]
        title = preset.get("title", k)
        if logger:
            logger(f"Инициализация пресета: [{title}]...", "info")

        actions = preset.get("actions", [])
        if not actions:
            if logger:
                logger(f"Пресет [{title}] не содержит действий.", "error")
            return False

        for idx, act in enumerate(actions, start=1):
            act_type = act.get("type", "")
            try:
                if act_type == "url":
                    target_url = act.get("url", "").strip()
                    if not target_url.startswith("http://") and not target_url.startswith("https://"):
                        target_url = "https://" + target_url
                    if logger:
                        logger(f"[{idx}/{len(actions)}] Открытие сайта: {target_url}", "action")
                    webbrowser.open(target_url)

                elif act_type == "app":
                    app_path = act.get("path", "").strip()
                    if logger:
                        logger(f"[{idx}/{len(actions)}] Запуск программы: {app_path}", "action")
                    # Запуск через os.startfile или subprocess
                    if os.path.exists(app_path):
                        os.startfile(app_path)
                    else:
                        # Попробуем запустить по имени (если в PATH)
                        subprocess.Popen(app_path, shell=True)

                elif act_type == "cmd":
                    command = act.get("command", "").strip()
                    if logger:
                        logger(f"[{idx}/{len(actions)}] Команда: {command}", "action")
                    subprocess.Popen(command, shell=True)

                elif act_type == "wait":
                    sec = float(act.get("seconds", 1))
                    if logger:
                        logger(f"[{idx}/{len(actions)}] Ожидание {sec} сек...", "system")
                    time.sleep(sec)

                elif act_type == "focus":
                    title = act.get("title", "")
                    if logger:
                        logger(f"[{idx}/{len(actions)}] Фокус на окно: '{title}'", "action")
                    ok = ia.focus_window(title)
                    if not ok and logger:
                        logger(f"Окно с названием '{title}' не найдено", "system")

                elif act_type == "key":
                    key_code = act.get("key", "enter")
                    if logger:
                        logger(f"[{idx}/{len(actions)}] Нажатие клавиши: [{key_code.upper()}]", "action")
                    ia.press_key(key_code)

                elif act_type == "click":
                    x = act.get("x")
                    y = act.get("y")
                    btn = act.get("button", "left")
                    dbl = act.get("double", False)
                    coord_str = f"({x}, {y})" if x is not None and y is not None else "текущая позиция"
                    if logger:
                        logger(f"[{idx}/{len(actions)}] Клик мыши [{btn}]: {coord_str}", "action")
                    ia.mouse_click(x, y, button=btn, double=dbl)

                elif act_type == "type":
                    txt = act.get("text", "")
                    if logger:
                        logger(f"[{idx}/{len(actions)}] Ввод текста...", "action")
                    ia.type_text(txt)

                elif act_type == "notify":
                    msg = act.get("message", "")
                    if logger:
                        logger(f"[{idx}/{len(actions)}] {msg}", "system")

            except Exception as e:
                if logger:
                    logger(f"Ошибка в действии #{idx} ({act_type}): {e}", "error")
                return False

        if logger:
            logger(f"Пресет [{title}] успешно выполнен!", "success")
        return True
