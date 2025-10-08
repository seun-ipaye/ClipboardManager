import tkinter as tk
from tkinter import ttk

class ClipboardGUI:
    def __init__(self, history):
        self.history = history
        self.root = tk.Tk()
        self.root.title("📋 Clipboard Manager")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.root.configure(bg="#1E1E1E")
        style = ttk.Style()
        style.configure("TLabel", background="#1E1E1E", foreground="#D9D9D9", font=("Segoe UI", 11))

        self.title_label = ttk.Label(self.root, text="Clipboard History", font=("Segoe UI", 13, "bold"), foreground="#00FF88")
        self.title_label.pack(pady=8)

        self.item_labels = []
        for _ in range(self.history.max_items):
            lbl = ttk.Label(self.root, text="", anchor="w", wraplength=360)
            lbl.pack(fill="x", padx=20, pady=4)
            self.item_labels.append(lbl)

        self.clear_button = ttk.Button(self.root, text="Clear History", command=self.clear_history)
        self.clear_button.pack(pady=6)

        self.refresh_display()
        self.root.after(500, self.auto_refresh)

    def refresh_display(self):
        """Update the text of the labels based on history."""
        items = list(self.history.history)
        for i, lbl in enumerate(self.item_labels):
            if i < len(items):
                text = items[i].replace("\n", " ")
                if len(text) > 60:
                    text = text[:57] + "..."
                if i == self.history.current_index:
                    lbl.config(text=f"👉 {text}", foreground="#00FF88")
                else:
                    lbl.config(text=f"   {text}", foreground="#D9D9D9")
            else:
                lbl.config(text="", foreground="#666666")

    def auto_refresh(self):
        """Keep the GUI updated as the program runs."""
        self.refresh_display()
        self.root.after(500, self.auto_refresh)

    def clear_history(self):
        self.history.clear()
        self.refresh_display()

    def run(self):
        self.root.mainloop()
