import json
import os
import time
from typing import List, Dict, Any

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "chat_history.json")

class ChatManager:
    def __init__(self, filepath: str = HISTORY_FILE):
        self.filepath = filepath
        self.messages: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.messages = data.get("messages", [])
            except Exception as e:
                print(f"Ошибка загрузки истории чата: {e}")
                self.messages = []
        else:
            self.messages = []
        return self.messages

    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump({"messages": self.messages}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории чата: {e}")

    def add_message(self, sender: str, text: str, tag: str):
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sender": sender,
            "text": text,
            "tag": tag
        }
        self.messages.append(entry)
        # Сохраняем последние 200 сообщений, чтобы файл не разрастался бесконечно
        if len(self.messages) > 200:
            self.messages = self.messages[-200:]
        self.save()

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def clear(self):
        self.messages = []
        self.save()

    def get_context_for_ai(self, max_turns: int = 8) -> List[Dict[str, str]]:
        """
        Возвращает историю для ИИ в формате [{"role": "user"|"model"|"assistant", "content": "..."}]
        """
        dialog = []
        # Фильтруем только реплики пользователя и Астрид (без системных логов)
        for m in self.messages:
            tag = m.get("tag", "")
            if tag == "user":
                dialog.append({"role": "user", "text": m.get("text", "")})
            elif tag == "astrid":
                dialog.append({"role": "model", "text": m.get("text", "")})

        # Берем последние N сообщений
        return dialog[-max_turns:]
