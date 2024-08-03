import tkinter as tk
import threading
import speech_recognition as sr
import pyautogui
import sys
from flask import Flask, request

# Initialize the Flask app
app = Flask(__name__)

# Global flag to manage server running state
server_running = True

@app.route('/')
def index():
    return "Flask server is running."

@app.route('/shutdown', methods=['POST'])
def shutdown():
    request.environ.get('werkzeug.server.shutdown')()
    return 'Server shutting down...'

# Initialize global variables
recognizer = sr.Recognizer()
microphone = sr.Microphone()
listening = False
recognized_text = ""
recognized_text_lock = threading.Lock()  # Lock for thread-safe access

def callback(recognizer, audio):
    global recognized_text
    try:
        text = recognizer.recognize_google(audio)
        print(f"Recognized: {text}")
        pyautogui.write(" " + text, interval=0.01)  # Add a space before the text

        with recognized_text_lock:  # Ensure thread-safe access
            recognized_text += " " + text
    except sr.UnknownValueError:
        print("Could not understand the audio.")
    except sr.RequestError:
        print("Could not request results; check your network connection.")

def listen_continuously():
    global listening
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        while listening:
            try:
                print("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                threading.Thread(target=callback, args=(recognizer, audio)).start()
            except sr.WaitTimeoutError:
                print("Listening timed out, restarting...")
            except Exception as e:
                print(f"An error occurred: {e}")

def start_listening():
    global listening
    listening = True
    threading.Thread(target=listen_continuously).start()

def stop_listening():
    global listening
    listening = False

def on_start():
    start_listening()
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

def on_stop():
    stop_listening()
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

def on_close():
    global server_running
    stop_listening()
    server_running = False
    # Send shutdown request to Flask server
    try:
        requests.post("http://127.0.0.1:5000/shutdown")
    except:
        pass
    root.destroy()

def run_flask():
    app.run(debug=False, use_reloader=False)

# Set up the Tkinter window
root = tk.Tk()
root.title("Voice Typing Control")

# Set the window icon (replace 'icon.ico' with your icon file)
icon_path = 'C:\\Users\\binwi\\Desktop\\Folders\\PyVoice\\B-001.ico'  # Replace with the correct path to your icon
root.iconbitmap(icon_path)

# Create and place title label
title_label = tk.Label(root, text="Voice Typing Control", font=("Helvetica", 16))
title_label.pack(pady=10)

# Create and place description label
description_label = tk.Label(root, text="Use this tool to convert speech to text in real-time.", wraplength=300)
description_label.pack(pady=10)

# Create and place Start and Stop buttons
start_button = tk.Button(root, text="Start", command=on_start, width=10)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop", command=on_stop, width=10)
stop_button.pack(pady=10)
stop_button.config(state=tk.DISABLED)

# Bind the close event
root.protocol("WM_DELETE_WINDOW", on_close)

# Start the Flask server in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.start()

# Start the Tkinter main loop
root.mainloop()

# Wait for the Flask server to stop before exiting
flask_thread.join()
