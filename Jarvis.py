"""
Friday - Siri-like Voice Assistant with GUI
A production-grade voice assistant with macOS Siri-inspired floating UI
"""

import speech_recognition as sr
from gtts import gTTS
import playsound
import os
import webbrowser
import wikipedia
import subprocess
import sys
import logging
import threading
import time
import re
import urllib.request
from datetime import datetime
from typing import Optional, Dict, List
from abc import ABC, abstractmethod
import json
from pathlib import Path
from urllib.parse import quote
import pyttsx3
# GUI Imports
import tkinter as tk
from tkinter import font as tkFont
import tkinter.ttk as ttk
from PIL import Image, ImageDraw, ImageFilter
import io

# ==================== CONFIGURATION ====================

class Config:
    """Centralized configuration management"""
    WAKE_WORD = "jarvis"
    VOICE_SPEED = False
    LANGUAGE = "en"
    TIMEOUT_SECONDS = 5
    PHRASE_TIME_LIMIT = 5
    ENERGY_THRESHOLD = 300
    AMBIENT_NOISE_DURATION = 0.5
    LOG_FILE = "jarvis_assistant.log"
    CACHE_DIR = "jarvis_cache"
    
    # GUI Configuration
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 500
    CORNER_RADIUS = 30
    
    # Feature toggles
    ENABLE_MUSIC = True
    ENABLE_SEARCH = True
    ENABLE_WIKIPEDIA = True
    ENABLE_LOGGING = True

# ==================== LOGGING SETUP ====================

def setup_logger():
    """Configure comprehensive logging"""
    if not Config.ENABLE_LOGGING:
        return logging.getLogger(__name__)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    fh = logging.FileHandler(Config.LOG_FILE)
    fh.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logger()

# ==================== MUSIC LIBRARY ====================

class MusicLibrary:
    """Manage music playlist with persistence and auto-learning"""
    def __init__(self, filename: str = "music_library.json"):
        self.filename = filename
        self.music = self._load_music()
    
    def _load_music(self) -> Dict[str, str]:
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load music library: {e}")
        
        # Initial default songs
        return {
            "starboy": "https://youtu.be/34Na4j8AVgA",
            "blinding lights": "https://youtu.be/fHI8X4OXluQ",
            "billie jean": "https://youtu.be/Zi_XLOBDo_Y",
        }
    
    def search_song(self, query: str) -> Optional[str]:
        query = query.lower().strip()
        if query in self.music:
            return self.music[query]
        for song, url in self.music.items():
            if query in song:
                return url
        return None

    def save_new_song(self, song_name: str, url: str):
        """Adds a new song to the library and persists to disk"""
        self.music[song_name.lower().strip()] = url
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.music, f, indent=4)
            logger.info(f"Saved '{song_name}' to local library.")
        except Exception as e:
            logger.error(f"Failed to save to music library: {e}")

# ==================== AUDIO MANAGEMENT ====================

class JARVISVoice:
    """Paul Bettany JARVIS-style voice synthesis"""
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'male' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                logger.info(f"Using voice: {voice.name}")
                break

    def speak(self, text: str):
        if not text: return
        try:
            logger.info(f"Speaking (JARVIS): {text}")
            formatted_text = self._format_for_jarvis(text)
            self.engine.say(formatted_text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Speech error: {e}")

    def _format_for_jarvis(self, text: str) -> str:
        replacements = {'color': 'colour', 'center': 'centre', 'realize': 'realise'}
        for am, br in replacements.items():
            text = text.replace(am, br)
        return text

class AudioManager:
    def __init__(self, use_jarvis=True):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = Config.ENERGY_THRESHOLD
        self.use_jarvis = use_jarvis
        self.voice_engine = JARVISVoice() if use_jarvis else None

    def speak(self, text: str):
        if self.use_jarvis:
            self.voice_engine.speak(text)
        else:
            logger.info(f"Speaking (Google TTS): {text}")
            tts = gTTS(text=text, lang=Config.LANGUAGE)
            filename = os.path.join(Config.CACHE_DIR, "temp_voice.mp3")
            tts.save(filename)
            playsound.playsound(filename)
            os.remove(filename)

    def listen(self, timeout: int = Config.TIMEOUT_SECONDS) -> str:
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=Config.PHRASE_TIME_LIMIT)
            command = self.recognizer.recognize_google(audio, language=Config.LANGUAGE)
            logger.info(f"Recognized: {command}")
            return command.lower().strip()
        except Exception as e:
            logger.debug(f"Recognition issue: {e}")
            return ""

# ==================== COMMAND HANDLERS ====================

class CommandHandler(ABC):
    def __init__(self, audio_manager: AudioManager):
        self.audio_manager = audio_manager
    @abstractmethod
    def can_handle(self, command: str) -> bool: pass
    @abstractmethod
    def handle(self, command: str): pass

class WebSearchHandler(CommandHandler):
    WEBSITES = {"moodle": "https://cet.iitp.ac.in", "youtube": "https://youtube.com", "github": "https://github.com"}
    def can_handle(self, command: str) -> bool: return any(s in command for s in self.WEBSITES) or "search" in command
    def handle(self, command: str):
        for site, url in self.WEBSITES.items():
            if site in command:
                webbrowser.open(url)
                self.audio_manager.speak(f"Opening {site}")
                return
        self.audio_manager.speak("Searching Google.")
        webbrowser.open(f"https://www.google.com/search?q={quote(command)}")

class MusicHandler(CommandHandler):
    def __init__(self, audio_manager, library):
        super().__init__(audio_manager)
        self.library = library

    def can_handle(self, command: str) -> bool: return "play" in command

    def handle(self, command: str):
        song = command.replace("play", "").strip()
        if not song:
            self.audio_manager.speak("What should I play, sir?")
            song = self.audio_manager.listen()
        
        if not song: return

        # Try library first
        url = self.library.search_song(song)
        if url:
            webbrowser.open(url)
            self.audio_manager.speak(f"Playing {song} from your collection.")
        else:
            self.audio_manager.speak(f"Searching YouTube for {song}.")
            self.play_and_save_youtube_result(song)

    def play_and_save_youtube_result(self, song: str):
        try:
            search_url = f"https://www.youtube.com/results?search_query={quote(song)}"
            response = urllib.request.urlopen(search_url)
            html = response.read().decode()
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            
            if video_ids:
                video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
                webbrowser.open(video_url)
                # Learning logic
                self.library.save_new_song(song, video_url)
            else:
                webbrowser.open(search_url)
        except Exception as e:
            logger.error(f"YouTube logic error: {e}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={quote(song)}")

class UtilityHandler(CommandHandler):
    def can_handle(self, command: str) -> bool: return any(k in command for k in ["exit", "quit", "goodbye"])
    def handle(self, command: str):
        self.audio_manager.speak("Goodbye, sir. Systems powering down.")
        logger.info("Shutdown sequence complete")
        os._exit(0)

# ==================== GUI COMPONENTS ====================

class SiriLikeGUI:
    def __init__(self, root, audio_manager, handlers):
        self.root = root
        self.audio_manager = audio_manager
        self.handlers = handlers
        self.is_listening = False
        self.setup_window()
        self.create_widgets()
        self.position_window()
        self.start_background_listening()

    def setup_window(self):
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.root.attributes('-alpha', 0.95, '-topmost', True)
        self.root.configure(bg='#000000')
        self.root.resizable(False, False)
        self.root.title("JARVIS Assistant")

    def position_window(self):
        sw = self.root.winfo_screenwidth()
        x = sw - Config.WINDOW_WIDTH - 20
        self.root.geometry(f"+{x}+60")

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root, bg='#1a1a1a')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(self.main_frame, text="JARVIS", font=("Helvetica", 16, "bold"), fg='#ffffff', bg='#1a1a1a').pack(pady=(0, 20))
        self.status_label = tk.Label(self.main_frame, text="Listening for wake word...", font=("Helvetica", 12), fg='#a8a8a8', bg='#1a1a1a')
        self.status_label.pack(pady=(0, 20))
        
        self.waveform_canvas = tk.Canvas(self.main_frame, width=360, height=100, bg='#1a1a1a', highlightthickness=0)
        self.waveform_canvas.pack(pady=(0, 20))
        
        self.text_display = tk.Text(self.main_frame, height=6, width=40, bg='#2a2a2a', fg='#ffffff', font=("Menlo", 10), wrap=tk.WORD, borderwidth=0)
        self.text_display.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        btn_frame = tk.Frame(self.main_frame, bg='#1a1a1a')
        btn_frame.pack(fill=tk.X)
        self.wake_btn = tk.Button(btn_frame, text="🎤", command=self.wake_and_listen, bg='#0a84ff', fg='#ffffff', font=("Helvetica", 18), relief=tk.FLAT, width=3)
        self.wake_btn.pack(side=tk.LEFT)
        tk.Button(btn_frame, text="✕", command=self.root.quit, bg='#5e5e5e', fg='#ffffff', font=("Helvetica", 12), relief=tk.FLAT, width=3).pack(side=tk.RIGHT)

    def animate_waveform(self):
        if not self.is_listening:
            self.waveform_canvas.delete("all")
            return
        self.waveform_canvas.delete("all")
        import random
        for i in range(12):
            x = 10 + i * 30
            h = random.randint(10, 80)
            self.waveform_canvas.create_rectangle(x, 50-h//2, x+20, 50+h//2, fill="#0a84ff", outline="#0a84ff")
        self.root.after(100, self.animate_waveform)

    def wake_and_listen(self):
        self.is_listening = True
        self.wake_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Say your command...")
        self.animate_waveform()
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        self.root.after(0, lambda: self.text_display.insert(tk.END, "🎤 Listening...\n"))
        command = self.audio_manager.listen()
        self.is_listening = False
        self.root.after(0, lambda: self.wake_btn.config(state=tk.NORMAL))
        if command:
            self.root.after(0, lambda: self.text_display.insert(tk.END, f"You: {command}\n"))
            for h in self.handlers:
                if h.can_handle(command):
                    h.handle(command)
                    break
        self.root.after(0, lambda: self.status_label.config(text="Listening for wake word..."))

    def start_background_listening(self):
        threading.Thread(target=self._bg_listener, daemon=True).start()

    def _bg_listener(self):
        while True:
            try:
                word = self.audio_manager.listen(timeout=5)
                if Config.WAKE_WORD in word:
                    self.audio_manager.speak("Yes, sir?")
                    self.root.after(0, self.wake_and_listen)
            except: pass
            time.sleep(0.1)

if __name__ == "__main__":
    os.makedirs(Config.CACHE_DIR, exist_ok=True)
    root = tk.Tk()
    am = AudioManager(use_jarvis=True)
    lib = MusicLibrary()
    handlers = [MusicHandler(am, lib), WebSearchHandler(am), UtilityHandler(am)]
    app = SiriLikeGUI(root, am, handlers)
    am.speak("Systems initialized. JARVIS online.")
    root.mainloop()
