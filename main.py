import threading
import pyaudio
import speech_recognition as sr
import dearpygui.dearpygui as dpg
from pynput import mouse
import pyautogui
from translate import Translator

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

is_recording = False
frames = []
stream = None
recording_thread = None

recognizer = sr.Recognizer()

# Supported languages mapping (ISO 639-1 codes)
languages = {
    "Afrikaans": "af",
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese (Simplified)": "zh",
    "Chinese (Traditional)": "zh-TW",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Hindi": "hi",
    "Italian": "it",
    "Indonesian": "id",
    "Japanese": "ja",
    "Korean": "ko",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Swedish": "sv",
    "Turkish": "tr",
    "Vietnamese": "vi",
    # Add more languages as needed
}


def record_audio():
    # Records audio from the microphone until is_recording is False.
    global is_recording, frames, stream

    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )
    frames = []

    while is_recording:
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        except Exception as e:
            print(f"Error while recording audio: {e}")
            break

    stream.stop_stream()
    stream.close()
    p.terminate()


def process_audio(audio_data):
    try:
        input_language_name = dpg.get_value("input_language")
        input_language_code = languages.get(input_language_name, "en")
        output_language_name = dpg.get_value("output_language")
        output_language_code = languages.get(output_language_name, "en")

        # Recognize speech
        text = recognizer.recognize_google(audio_data, language=input_language_code)
        print(f"Recognized Text ({input_language_name}): {text}")

        # Update the GUI with recognized text
        dpg.set_value("input_box", text)

        # Translate the text asynchronously
        def translation_thread():
            try:
                translator = Translator(
                    to_lang=output_language_code, from_lang=input_language_code
                )
                translated_text = translator.translate(text)
                print(f"Translated Text ({output_language_name}): {translated_text}")

                # Update the GUI and type the text
                dpg.set_value("translated_box", translated_text)
                pyautogui.typewrite(translated_text)
            except Exception as e:
                print(f"Translation error: {e}")

        threading.Thread(target=translation_thread).start()

    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


def on_click(x, y, button, pressed):
    # Callback function for mouse events.
    global is_recording, recording_thread

    if button in [mouse.Button.x1, mouse.Button.x2, mouse.Button.middle]:
        if pressed:
            if not is_recording:
                is_recording = True
                recording_thread = threading.Thread(target=record_audio)
                recording_thread.start()
                print("Recording started...")
        else:
            if is_recording:
                is_recording = False
                recording_thread.join()
                print("Recording stopped.")

                audio_data_bytes = b"".join(frames)
                audio_data = sr.AudioData(audio_data_bytes, RATE, 2)

                # Process audio in a separate thread
                threading.Thread(target=process_audio, args=(audio_data,)).start()


def main():
    # Sets up the Dear PyGui application and runs the main event loop.
    dpg.create_context()
    dpg.create_viewport(
        title="Speech to Text App", min_width=600, min_height=300, width=600, height=300
    )

    with dpg.window(label="Speech to Text", tag="main_window"):
        with dpg.group(horizontal=False):
            dpg.add_text("Recognized Text:")
            dpg.add_input_text(default_value="", tag="input_box", width=-1)
            dpg.add_text("Translated Text:")
            dpg.add_input_text(default_value="", tag="translated_box", width=-1)
            dpg.add_combo(
                items=list(languages.keys()),
                default_value="English",
                label="Input Language",
                tag="input_language",
                width=-1,
            )
            dpg.add_combo(
                items=list(languages.keys()),
                default_value="Spanish",
                label="Output Language",
                tag="output_language",
                width=-1,
            )

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main_window", True)

    listener = mouse.Listener(on_click=on_click)
    listener.start()

    dpg.start_dearpygui()

    listener.stop()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
