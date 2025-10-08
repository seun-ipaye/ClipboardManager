from collections import deque

class ClipboardHistory:
    def __init__(self, max_items=3):
        self.max_items = max_items
        self.history = deque(maxlen=max_items)
        self.current_index = -1 

    def add_item(self, text: str):
        if not text or (self.history and text == self.history[-1]):
            return
        self.history.append(text)
        self.current_index = len(self.history) - 1

    def cycle(self):
        if not self.history:
            return None
        self.current_index = (self.current_index + 1) % len(self.history)
        return self.history[self.current_index]

    def get_current(self):
        if self.history and self.current_index >= 0:
            return self.history[self.current_index]
        return None
