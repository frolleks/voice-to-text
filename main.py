import threading
import pyaudio
import speech_recognition as sr
import dearpygui.dearpygui as dpg
from pynput import mouse
import pyautogui


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


is_recording = False
frames = []
stream = None
recording_thread = None

recognizer = sr.Recognizer()


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


def on_click(x, y, button, pressed):
    # Callback function for mouse events.
    global is_recording, recording_thread

    if button == mouse.Button.x1 or button == mouse.Button.x2:
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

                audio_data = b"".join(frames)

                audio = sr.AudioData(audio_data, RATE, 2)
                try:

                    text = recognizer.recognize_google(audio)
                    print(f"Recognized Text: {text}")

                    pyautogui.typewrite(text)

                    dpg.set_value("input_box", text)
                except sr.UnknownValueError:
                    print("Could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results; {e}")


def main():
    # Sets up the Dear PyGui application and runs the main event loop.
    dpg.create_context()
    dpg.create_viewport(
        title="Speech to Text App", min_width=300, min_height=100, width=600, height=200
    )

    with dpg.window(label="Speech to Text", tag="main_window"):
        with dpg.group(horizontal=False):
            dpg.add_text("Recognized Text:")
            dpg.add_input_text(default_value="", tag="input_box", width=-1)

    def on_viewport_resize(sender, app_data):
        width, height = app_data[0], app_data[1]
        print(f"Viewport resized: width={width}, height={height}")

    dpg.set_viewport_resize_callback(on_viewport_resize)

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
