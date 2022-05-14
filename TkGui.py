
import tkinter.filedialog
import tkinter.messagebox
import tkinter.font
import tkinter.scrolledtext
import tkinter as tk

class TkShowFile(tk.simpledialog.Dialog):
    def __init__(self, parent, title, text):
        self.text = text
        super().__init__(parent, title)

    def body(self, frame):
        text_license = tk.scrolledtext.ScrolledText(frame)
        text_license.insert('1.0', self.text)
        text_license.config(state=tk.DISABLED)
        text_license.pack(fill=tk.X, expand=True)
    
        return frame
    
    def buttonbox(self):
        pass