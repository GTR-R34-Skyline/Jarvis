import speech_recognition as sr
from gtts import gTTS  # Google Text To speech 
import playsound
import os
import webbrowser   #to open external links
import wikipedia    # to link information
import music_library 
import sys          # to system related tasks
import difflib      #difference and similarity

def speak(text):                         
    print("Friday said:", text)     # whatever she speaks it will start with "friday said"
    tts = gTTS(text=text, lang="en", slow=False)
    filename = "her_voice.mp3"
    tts.save(filename)       # Make her_voice.mp3
    playsound.playsound(filename)  # play and run it
    os.remove(filename)      # after done , delete the file
    
recognizer = sr.Recognizer()

def listen():
    with sr.Microphone() as source:   # collects the input
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)  # enhance input
        recognizer.energy_threshold = 300  # to remove unwanted noise from input
        recognizer.dynamic_energy_threshold = False 

        audio = recognizer.listen(source)     # records my voice

        try:
            command = recognizer.recognize_google(audio, language="en-in")    # intakes my input and then recognize it
            print("Shivaji said:", command)
            return command.lower()
        except:
            speak("Sorry, I could not understand.")
            return ""

def myCommand(c):
    if "model" in c.lower() or "moodle" in c.lower():
        webbrowser.open("https://cet.iitp.ac.in")           # open moodle

    elif "open instagram" in c.lower() or "instagram khol" in c.lower():
        webbrowser.open("https://instagram.com")              # open insta

    elif "open youtube" in c.lower() or "youtube khol" in c.lower():
        webbrowser.open("https://youtube.com")                 # open yt

    elif "open github" in c.lower() or "coders ka adda" in c.lower():
        webbrowser.open("https://github.com")                    # open git

    elif "open linkedin" in c.lower() or "demotivate kar" in c.lower():
        webbrowser.open("https://linkedin.com")                   # starts demotivating

    elif "meri playlist chala" in c.lower():
        webbrowser.open("https://youtu.be/AbkEmIgJMcU?si=V6ETJmVWDU2zOEtq") 

    elif "google" in c.lower() or "search" in c.lower():
        speak("Kya Search Karu")    
        topic = listen()                                             # wait for your topic 
        webbrowser.open(f"https://www.google.com/search?q={topic}")
        speak(f"Here is what I found for {topic}")

    elif "tum best ho" in c.lower():
        speak("Thank You , Ye mere boss ki vajah se hai")            # 😁😁

    elif "good bye" in c.lower():
        speak("Good Bye Guys , Have a nice day")                  # just for video

    elif c.lower().startswith("play"):
        song = c.lower().replace("play", "", 1).strip()           # if i say "play tu hi mera" it removes play and search remaining part in music_library

        if song in music_library.music:
            link = music_library.music[song]
            webbrowser.open(link)                          # if it found , opens the link in browser
        else :
            speak("Ye song play list mai nahi h")

    elif "information" in c.lower() or "tell me about" in c.lower() or "who is" in c.lower():
        speak("Kya Jan na hai apko?")
        topic = listen()
        try:
            info = wikipedia.summary(topic, sentences=2)       # search topic on wikipedia and summarize it upto 2 sentences 
            speak(info)
        except:
            speak("Sorry, I couldn't find anything on that.")
    
if __name__ == "__main__":
    speak("Activating Friday...")                     # Engine is heating up

    while True:
        try:
            with sr.Microphone() as source:           # listens to my voice
                print("Listening for wake word...")   # Wait for "Friday"
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)    # how much time it will listen and recognize the input
            word = recognizer.recognize_google(audio)  # Will Match the word
 
            if word.lower() == "friday":
                speak("Yes Boss")                       # Speak Yes boss , if true
                
                while True:
                    command = listen()                  # listen the command and give it to def function
                    if command != "":
                        myCommand(command)
                        if "exit" in command or "quit" in command:
                            speak("Good bye boss , Friday Going offline.")    # to shut down friday say "exit"
                            sys.exit(0) 

        except Exception as e:                           # display error as "e" not show red error
            print("Error:", e)                          
