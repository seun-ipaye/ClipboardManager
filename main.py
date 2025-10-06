import sys
import time
import threading
import platform
from collections import deque

# Install these with:
#   python -m pip install pyperclip pynput
import pyperclip
from pynput import keyboard

# -----------------------------
# Config
# -----------------------------
MAX_ITEMS = 3                 # number of clipboard slots to keep
POLL_INTERVAL_SEC = 0.20      # how often we check clipboard
IGNORE_BLANK = True           # ignore blank/whitespace-only copies

# Hotkeys (auto-picked per OS)
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
        self.current_index = -1  # -1 means no active selection yet

    def add_item(self, text: str):
        # skip if empty/whitespace (optional)
        if IGNORE_BLANK and (text is None or text.strip() == ""):
            return
        # avoid duplicate if same as last stored
        if self.history and text == self.history[-1]:
            return
        self.history.append(text)
        # when a new item arrives, point to the newest
        self.current_index = len(self.history) - 1

    def cycle(self):
        if not self.history:
            return None
        self.current_index = (self.current_index + 1) % len(self.history)
        return self.history[self.current_index]

    def get_current(self):
        if self.history and 0 <= self.current_index < len(self.history):
            return self.history[self.current_index]
        return None

    def clear(self):
        self.history.clear()
        self.current_index = -1

history = ClipboardHistory(max_items=MAX_ITEMS)

# This shared dict prevents the watcher from re-adding items we set ourselves.
state = {
    "last_clipboard": None,
    "paused": False,  # could be used if you later add a pause/resume hotkey
}

# -----------------------------
# Helpers
# -----------------------------
def print_stack():
    """
    Pretty-print the stack to console each time you cycle or change.
    The active item is marked with '👉'.
    """
    items = list(history.history)
    if not items:
        print("📋 [empty]")
        return

    print("\n📋 Clipboard stack (oldest → newest):")
    for i, item in enumerate(items):
        prefix = "👉 " if i == history.current_index else "   "
        # clip long lines for console hygiene
        preview = item.replace("\n", " ")
        if len(preview) > 120:
            preview = preview[:117] + "..."
        print(f"{prefix}[{i}] {preview}")
    print()  # extra newline

# -----------------------------
# Clipboard watcher thread
# -----------------------------
def clipboard_watcher(stop_event: threading.Event):
    """
    Poll the system clipboard and add new items to history.
    """
    # Initialize last clipboard content
    try:
        state["last_clipboard"] = pyperclip.paste()
    except Exception:
        state["last_clipboard"] = None

    while not stop_event.is_set():
        try:
            current = pyperclip.paste()
        except Exception:
            # If the OS clipboard isn't accessible right now, just retry shortly
            time.sleep(POLL_INTERVAL_SEC)
            continue

        # Only register as a new copy if it's different from the last known content
        if current != state["last_clipboard"]:
            # Update memory of what we saw
            state["last_clipboard"] = current
            # Add to history (with duplicate/blank guard inside)
            history.add_item(current)
            # Optional: print stack when something new is copied
            # print_stack()

        time.sleep(POLL_INTERVAL_SEC)

# -----------------------------
# Hotkey callbacks
# -----------------------------
def on_cycle():
    """
    Switch the system clipboard to the next item in our history.
    """
    new_text = history.cycle()
    if new_text is None:
        print("🔁 No items to cycle.")
        return
    # 1) Put chosen text into system clipboard
    pyperclip.copy(new_text)
    # 2) Tell watcher not to treat this as a 'new' copy
    state["last_clipboard"] = new_text
    # 3) Show where we landed
    print_stack()

def on_clear():
    """
    Clear the clipboard history (does not clear the system clipboard).
    """
    history.clear()
    print("🧹 History cleared.")

# -----------------------------
# Main
# -----------------------------
def main():
    print("🚀 Multi-Slot Clipboard Manager")
    print(f"   Slots: {MAX_ITEMS}")
    print(f"   Cycle hotkey: {HOTKEY_CYCLE}")
    print(f"   Clear hotkey: {HOTKEY_CLEAR}")
    if IS_MAC:
        print("   macOS note: grant Accessibility permission to your terminal/Python for hotkeys to work.")
    print("   Usage: copy text as usual, use the cycle hotkey to switch the active clipboard, then paste.")

    # Start watcher thread
    stop_event = threading.Event()
    t = threading.Thread(target=clipboard_watcher, args=(stop_event,), daemon=True)
    t.start()

    # Register global hotkeys
    # pynput uses strings like "<ctrl>+<alt>+h", "<cmd>+<shift>+v"
    with keyboard.GlobalHotKeys({
        HOTKEY_CYCLE: on_cycle,
        HOTKEY_CLEAR: on_clear,
    }) as h:
        try:
            h.join()  # blocks until interrupted (Ctrl+C in terminal)
        except KeyboardInterrupt:
            pass
        finally:
            stop_event.set()
            t.join(timeout=1.0)
            print("\n👋 Exiting.")

if __name__ == "__main__":
    main()
