import os
import asyncio
import threading
import time
import tempfile
import re
from typing import Callable, Optional
import speech_recognition as sr
import edge_tts
import pygame
from sound_effects import play_chime

# Голос по умолчанию для Астрид (живой женский голос Светлана)
DEFAULT_VOICE = "ru-RU-SvetlanaNeural"

class VoiceEngine:
    def __init__(self, on_user_speech: Callable[[str], None], on_status: Callable[[str, str], None]):
        self.on_user_speech = on_user_speech
        self.on_status = on_status

        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.8  # Пауза в секундах, после которой фраза считается законченной

        self.is_live = False
        self.is_speaking = False
        self.live_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Инициализация звука
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as e:
            print(f"Ошибка инициализации pygame.mixer: {e}")

        # Список триггеров имени (wake words)
        self.wake_words = ["астрид", "ас3д", "астрит", "астрик", "ася"]

    def start_live(self):
        """Запуск фонового Live-режима (как Алиса / Алекса)"""
        if self.is_live:
            return
        self.is_live = True
        self._stop_event.clear()
        self.live_thread = threading.Thread(target=self._live_loop, daemon=True)
        self.live_thread.start()
        self.on_status("LIVE: ОЖИДАЮ СЛОВО 'АСТРИД'...", "accent")

    def stop_live(self):
        """Остановка фонового Live-режима"""
        self.is_live = False
        self._stop_event.set()
        self.stop_speaking()
        self.on_status("LIVE ВЫКЛЮЧЕН", "system")

    def toggle_live(self) -> bool:
        if self.is_live:
            self.stop_live()
            return False
        else:
            self.start_live()
            return True

    def listen_once(self):
        """Однократная запись фразы (по клику на кнопку микрофона)"""
        threading.Thread(target=self._listen_once_thread, daemon=True).start()

    def _listen_once_thread(self):
        self.on_status("СЛУШАЮ МИКРОФОН...", "accent")
        play_chime()
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.4)
                audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=10)

            self.on_status("РАСПОЗНАЮ РЕЧЬ...", "warning")
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            if text and text.strip():
                self.on_user_speech(text.strip())
            else:
                self.on_status("ГОТОВА", "system")
        except sr.WaitTimeoutError:
            self.on_status("ВРЕМЯ ВЫШЛО (ТИШИНА)", "system")
        except sr.UnknownValueError:
            self.on_status("НЕ УДАЛОСЬ РАСПОЗНАТЬ", "system")
        except Exception as e:
            self.on_status(f"ОШИБКА МИКРОФОНА: {e}", "error")

    def _live_loop(self):
        """Бесконечный цикл ожидания wake word и диалога"""
        mic = sr.Microphone()

        # Калибровка шума
        try:
            with mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.8)
        except Exception as e:
            self.on_status(f"Ошибка микрофона: {e}", "error")
            self.is_live = False
            return

        while not self._stop_event.is_set():
            if self.is_speaking:
                time.sleep(0.2)
                continue

            self.on_status("LIVE: СЛУШАЮ ('АСТРИД')...", "accent")

            try:
                with mic as source:
                    # Слушаем короткую фразу
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)

                if self._stop_event.is_set():
                    break

                # Распознаем
                text = self.recognizer.recognize_google(audio, language="ru-RU").lower().strip()

                # Проверяем наличие слова "Астрид"
                found_wake = False
                command_after_wake = ""

                for w in self.wake_words:
                    if w in text:
                        found_wake = True
                        # Вырезаем имя и смотрим, есть ли команда сразу в этой же фразе
                        # Например: "Астрид включи ютуб" -> "включи ютуб"
                        parts = re.split(rf"\b{w}\b", text, maxsplit=1)
                        if len(parts) > 1 and parts[1].strip():
                            command_after_wake = parts[1].strip()
                        break

                if found_wake:
                    # 1. Проиграть короткий звук активации
                    play_chime()

                    if command_after_wake:
                        # Команда была сказана сразу вместе с именем
                        self.on_status("ОБРАБАТЫВАЮ КОМАНДУ...", "warning")
                        self.on_user_speech(command_after_wake)
                    else:
                        # Сказали только "Астрид" — ждем саму команду
                        self.on_status("АСТРИД НА СВЯЗИ! СЛУШАЮ ВАС...", "success")
                        with mic as cmd_source:
                            cmd_audio = self.recognizer.listen(cmd_source, timeout=6, phrase_time_limit=12)

                        self.on_status("РАСПОЗНАЮ КОМАНДУ...", "warning")
                        cmd_text = self.recognizer.recognize_google(cmd_audio, language="ru-RU")
                        if cmd_text and cmd_text.strip():
                            self.on_user_speech(cmd_text.strip())

            except sr.WaitTimeoutError:
                # Таймаут тишины — просто продолжаем слушать
                continue
            except sr.UnknownValueError:
                # Шум или непонятный звук — продолжаем слушать
                continue
            except Exception as e:
                # Ошибка распознавания или сети
                time.sleep(0.5)
                continue

    def speak(self, text: str, on_done: Optional[Callable[[], None]] = None):
        """Озвучивает текст голосом Светланы в отдельном потоке"""
        if not text or not text.strip():
            if on_done:
                on_done()
            return

        threading.Thread(target=self._speak_thread, args=(text, on_done), daemon=True).start()

    def _speak_thread(self, text: str, on_done: Optional[Callable[[], None]] = None):
        self.is_speaking = True
        self.on_status("АСТРИД ГОВОРИТ...", "success")

        # Очищаем текст от технической разметки и ссылок для красивой речи
        clean_text = re.sub(r"\[\[.*?\]\]", "", text)
        clean_text = re.sub(r"https?://\S+", "ссылка", clean_text)
        clean_text = re.sub(r"[*_#`]", "", clean_text).strip()

        if not clean_text:
            self.is_speaking = False
            if on_done:
                on_done()
            return

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name

            # Генерация аудиофайла через edge-tts
            async def _generate():
                communicate = edge_tts.Communicate(clean_text, DEFAULT_VOICE)
                await communicate.save(temp_path)

            asyncio.run(_generate())

            # Воспроизведение через pygame
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy() and not self._stop_event.is_set():
                time.sleep(0.08)

        except Exception as e:
            print(f"Ошибка синтеза речи: {e}")
        finally:
            self.is_speaking = False
            if temp_path and os.path.exists(temp_path):
                try:
                    pygame.mixer.music.unload()
                    os.remove(temp_path)
                except Exception:
                    pass

            if self.is_live:
                self.on_status("LIVE: ОЖИДАЮ 'АСТРИД'...", "accent")
            else:
                self.on_status("ГОТОВА", "system")

            if on_done:
                on_done()

    def stop_speaking(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_speaking = False
