import time
import threading
import platform
from collections import deque
import pyperclip
from pynput import keyboard
from gui import ClipboardGUI

# -----------------------------
# Config
# -----------------------------
MAX_ITEMS = 3
POLL_INTERVAL_SEC = 0.20
IGNORE_BLANK = True

IS_MAC = platform.system() == "Darwin"
HOTKEY_CYCLE = "<cmd>+<shift>+v" if IS_MAC else "<ctrl>+<shift>+v"
HOTKEY_CLEAR = "<cmd>+<alt>+c" if IS_MAC else "<ctrl>+<alt>+c"

# -----------------------------
# State
# -----------------------------
class ClipboardHistory:
    def __init__(self, max_items=3):
        self.max_items = max_items
        self.history = deque(maxlen=max_items)
        self.current_index = -1

    def add_item(self, text: str):
        if IGNORE_BLANK and (text is None or text.strip() == ""):
            return
        if self.history and text == self.history[-1]:
            return
        self.history.append(text)
        self.current_index = len(self.history) - 1

    def cycle(self):
        if not self.history:
            return None
        self.current_index = (self.current_index + 1) % len(self.history)
        return self.history[self.current_index]

    def clear(self):
        self.history.clear()
        self.current_index = -1


history = ClipboardHistory(max_items=MAX_ITEMS)
state = {"last_clipboard": None}

# -----------------------------
# Clipboard watcher
# -----------------------------
def clipboard_watcher(stop_event):
    try:
        state["last_clipboard"] = pyperclip.paste()
    except Exception:
        state["last_clipboard"] = None

    while not stop_event.is_set():
        try:
            current = pyperclip.paste()
        except Exception:
            time.sleep(POLL_INTERVAL_SEC)
            continue

        if current != state["last_clipboard"]:
            state["last_clipboard"] = current
            history.add_item(current)
        time.sleep(POLL_INTERVAL_SEC)

# -----------------------------
# Hotkey callbacks
# -----------------------------
def on_cycle():
    new_text = history.cycle()
    if new_text:
        pyperclip.copy(new_text)
        state["last_clipboard"] = new_text
        gui.refresh_display()

def on_clear():
    history.clear()
    gui.refresh_display()

# -----------------------------
# Main
# -----------------------------
def main():
    print("🚀 Multi-Slot Clipboard Manager")
    print(f"   Slots: {MAX_ITEMS}")
    print(f"   Cycle hotkey: {HOTKEY_CYCLE}")
    print(f"   Clear hotkey: {HOTKEY_CLEAR}")
    if IS_MAC:
        print("   macOS note: grant Accessibility permission to Python for hotkeys to work.")

    # Start watcher and hotkey listener in threads
    stop_event = threading.Event()
    threading.Thread(target=clipboard_watcher, args=(stop_event,), daemon=True).start()

    # Global hotkeys thread
    def hotkey_listener():
        with keyboard.GlobalHotKeys({
            HOTKEY_CYCLE: on_cycle,
            HOTKEY_CLEAR: on_clear,
        }) as h:
            h.join()

    threading.Thread(target=hotkey_listener, daemon=True).start()

    # --- Run GUI on MAIN THREAD ---
    global gui
    gui = ClipboardGUI(history)
    try:
        gui.run()  # this call blocks and safely owns the Tk event loop
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        print("\n👋 Exiting.")

if __name__ == "__main__":
    main()
