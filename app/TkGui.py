
import tkinter.filedialog
import tkinter.messagebox
import tkinter.font
import tkinter.scrolledtext
import tkinter as tk

from serial.tools.list_ports import comports

def TkCustomFont(font_name='TkTextFont', **kwargs):
    "Build customized font object based on existing default. Any callable arguments are used to modify the current value."
    font = tk.font.nametofont('TkTextFont').copy()
    for option, value in kwargs.items():
        if callable(value):
            kwargs[option] = value(font.cget(option))
    font.configure(**kwargs)
    return font

class TkShowText(tk.simpledialog.Dialog, title="" text=""):
    """Dialog used to show read-only contents of a file."""
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

class PickChoice(tk.simpledialog.Dialog):
    """Dialog used to pick from a list of choices.
    
    After selection result member has 1-based index of choice."""
    def __init__(self, parent, title, message, choices):
        self.message = message
        self.choices = choices
        self.choice = tk.IntVar()
        super().__init__(parent, title)

    def body(self, frame):
        tk.Label(frame, text=self.message).pack(fill=tk.X)
        for i, choice in enumerate(self.choices):
            text = choice if isinstance(choice, str) else choice[0]
            tk.Radiobutton(frame, text=text, value=i+1, variable=self.choice, justify=tk.LEFT).pack(fill=tk.X)
            #tk.Button(frame, text="Pick").grid(row=i, column=0)
            #tk.Label(frame, text=text).grid(row=i, column=1)
        return frame
    
    def buttonbox(self):
        tk.Button(self, text='Cancel', width=5, command=self.cancel_pressed)\
            .pack(side=tk.RIGHT, padx=2, pady=4)
        tk.Button(self, text='OK', width=5, command=self.ok_pressed)\
            .pack(side=tk.RIGHT, padx=2, pady=4)
        self.bind("<Return>", lambda event: self.ok_pressed())
        self.bind("<Escape>", lambda event: self.cancel_pressed())
    
    def ok_pressed(self):
        self.result = self.choice.get()
        if self.result == 0:
            self.result = None
        self.destroy()

    def cancel_pressed(self):
        self.destroy()

def PickComport(parent):
    ports = comports()
    if not ports:
        tk.messagebox.showinfo(title='Comport Selection', message="No comports detected.")
        return None
    elif len(ports) == 1:
        return ports[0][0]
    
    choice = PickChoice(parent, title="Select COM port", message="Select comport for connection to oven.", choices=ports)
    if choice:    
        return ports[choice.result-1][0]
    else:
        return None
