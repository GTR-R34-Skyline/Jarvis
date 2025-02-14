import tkinter as tk
import threading
import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import webbrowser
import pywhatkit
import pyautogui
import os
import time
import subprocess
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

class VoiceAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant")
        self.root.geometry("400x300")

        # GUI Elements
        self.label = tk.Label(root, text="Voice Assistant", font=("Arial", 24))
        self.label.pack(pady=20)
        self.status_label = tk.Label(root, text="Status: Ready", font=("Arial", 12))
        self.status_label.pack(pady=5)
        self.start_button = tk.Button(root, text="Start Listening", command=self.start_listening_thread)
        self.start_button.pack(pady=10)
        self.quit_button = tk.Button(root, text="Quit", command=self.quit_assistant)
        self.quit_button.pack(pady=10)

        # Initialize speech engine
        self.engine = pyttsx3.init('sapi5')
        self.recognizer = sr.Recognizer()
        # Spotify path for Windows Store version
        self.spotify_path = r"C:\Users\shash\AppData\Local\Microsoft\WindowsApps\Spotify.exe"
        self.is_spotify_running = False

    def update_status(self, message):
        self.status_label.config(text=f"Status: {message}")
        self.root.update()

    def speak(self, audio):
        self.update_status("Speaking...")
        self.engine.say(audio)
        self.engine.runAndWait()
        self.update_status("Ready")

    def open_spotify(self):
        try:
            # Check if Spotify is already running
            output = subprocess.check_output('tasklist', shell=True).decode()
            if 'Spotify.exe' in output:
                self.is_spotify_running = True
                self.speak("Spotify is already running")
                return True
            # Launch Spotify using the Windows Store path
            subprocess.Popen([self.spotify_path])
            time.sleep(3)  # Wait for Spotify to launch
            self.is_spotify_running = True
            self.speak("Opening Spotify")
            return True
        except Exception as e:
            print(f"Error opening Spotify: {e}")
            # Fallback method using shell command
            try:
                subprocess.run('start spotify:', shell=True)
                time.sleep(3)
                self.is_spotify_running = True
                self.speak("Opening Spotify")
                return True
            except Exception as e:
                self.speak("I couldn't open Spotify. Please check if it's installed correctly")
                print(f"Fallback error: {e}")
                return False

    def control_spotify(self, command):
        try:
            if not self.is_spotify_running and not self.open_spotify():
                return
            # Focus Spotify window
            subprocess.run(['powershell', '-command', '(New-Object -ComObject WScript.Shell).AppActivate("Spotify")'])
            time.sleep(0.5)
            if 'play' in command:
                if 'play' in command and len(command.split()) > 1:
                    # Search and play specific song
                    pyautogui.hotkey('ctrl', 'l')
                    time.sleep(0.5)
                    search_term = command.replace("play", "").replace("on spotify", "").replace("spotify", "").strip()
                    pyautogui.write(search_term)
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    self.speak(f"Playing {search_term} on Spotify")
                else:
                    # Play/Resume current song
                    pyautogui.press('space')
                    self.speak("Playing music on Spotify")
            elif 'pause' in command:
                pyautogui.press('space')
                self.speak("Pausing music")
            elif 'next' in command:
                pyautogui.hotkey('ctrl', 'right')
                self.speak("Playing next track")
            elif 'previous' in command:
                pyautogui.hotkey('ctrl', 'left')
                self.speak("Playing previous track")
        except Exception as e:
            self.speak("I encountered an error while controlling Spotify")
            print(f"Error controlling Spotify: {e}")

    def process_command(self, query):
        try:
            if 'wikipedia' in query:
                self.speak("Searching Wikipedia...")
                query = query.replace("wikipedia", "")
                results = wikipedia.summary(query, sentences=2)
                self.speak(results)
            elif 'open spotify' in query:
                self.open_spotify()
            elif 'spotify' in query:
                if 'play' in query or any(cmd in query for cmd in ['pause', 'next', 'previous']):
                    self.control_spotify(query)
            elif 'open google' in query:
                webbrowser.open('http://google.com')
            elif 'youtube' in query:
                query = query.replace("youtube", "")
                pywhatkit.playonyt(query)
                self.speak(f"Playing {query} on YouTube")
            elif 'cricket' in query:
                webbrowser.open('https://www.espncricinfo.com/')
            elif 'exit' in query:
                self.speak("Exiting program.")
                self.quit_assistant()
        except Exception as e:
            print(f"Error processing command: {e}")
            self.speak("I encountered an error processing that command")

    def start_listening(self):
        self.update_status("Listening...")
        while True:
            query = self.take_command()
            if query:
                self.process_command(query)

    def start_listening_thread(self):
        threading.Thread(target=self.start_listening).start()

    def take_command(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("Listening...")
            audio = self.recognizer.listen(source)
        try:
            print("Recognizing...")
            query = self.recognizer.recognize_google(audio)
            print(f"User said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            self.speak("Sorry, I did not understand that.")
            return None
        except sr.RequestError:
            print("Could not request results from Google Speech Recognition service.")
            self.speak("Could not request results from the speech recognition service.")
            return None

    def quit_assistant(self):
        self.speak("Goodbye!")
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistantApp(root)
    root.mainloop()
