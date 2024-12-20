
import os
import sys
import re

import tkinter.filedialog
import tkinter.messagebox
import tkinter.scrolledtext
import tkinter as tk

from .TkGui import *

class Profile():
    MAX_LENGTH = 40 # From listening to the Torch's controller - might be changeable, *might not*
    DEFAULT_PATH = "profiles/default.prfl"
    LAST_FILE_PATH = "lastprofile.txt"

    def __init__(self, filename=None, callback=None):
        self.text = None         # Text of profile
        self.errors = []         # Array of tuples with error lines.
        self.pairs = []          # Parsed profile as Array of tuples
        self.duration = None     # Full length of profile
        self.filename = None
        
        if filename is None:
            if os.path.exists(self.LAST_FILE_PATH):
                with open(self.LAST_FILE_PATH) as f:
                    filename = f.readline().strip()
                    print("Reading file " + filename)
            if filename is None or len(filename) == 0:
                filename = self.DEFAULT_PATH
                self.filename = filename
                self.save_last()
                print("No previous file found, loading default")
        if filename:
            if os.path.exists(filename):
                self.filename = filename
                with open(filename) as file:
                    self.update(file.read())
        else:
            print("NO WHY HERE? BAD!")
            self.update(DEFAULT_PROFILE)
        
        # Note: below must be set after first update.
        self.has_changes = False # Has changes needing saving to disk.
        self.callback = callback # Callback to signal updated profile.
    
    def name(self):
        name = os.path.basename(self.filename) if self.filename is not None else "default"
        if self.has_changes:
            name += "*"
        return name

    def has_errors(self):
        return len(self.errors) > 0

    def update(self, text, first_error_only=False):
        if self.text == text:
            return # No changes to text

        self.has_changes = True
        self.errors = Profile.Validate(text, first_error_only)
        self.text = text
        self.pairs = Profile.Parse(text)
        self.duration = sum([pair[1] for pair in self.pairs])

        # Todo: only use callback when there are no errors?
        if hasattr(self, "callback") and callable(self.callback):
            self.callback()
            
        if __debug__ and self.has_errors():
            print("Failed to parse '{}' profile. Errors on the following lines.".format(self.filename), file=sys.stderr)
            for error, line in self.errors:
                print("  line {} Error: {}".format(line, error), file=sys.stderr)

    PROFILE_FILETYPES = (('oven profiles', '*.prfl *.csv'),('All files', '*.*'))

    def open(self):
        print("Open")
        directory, basename = os.path.split(self.filename)
        file = tk.filedialog.askopenfile(
            title="Open Oven Profile",
            initialdir=directory,
            initialfile=basename,
            filetypes=Profile.PROFILE_FILETYPES
        )
        
        if file:
            self.filename = file.name
            self.update(file.read())
            self.has_changes = False # Clear dirty flag after load.
            file.close()
            self.save_last()
        return file

    def save_last(self):
        with open(self.LAST_FILE_PATH, "w") as f:
            f.write(self.filename)

    def save_as(self):
        directory, basename = os.path.split(self.filename)
        file = tk.filedialog.asksaveasfile(
            title="Select Oven Profile",
            initialdir=directory,
            initialfile=basename,
            filetypes=Profile.PROFILE_FILETYPES
        )
        self.save(file.name)
        file.close()
        return file

    def save(self, filename=None):
        filename = filename or self.filename
        if os.path.exists(filename):
            with open(filename, "w") as file:
                file.write(self.text)
            with open(self.LAST_FILE_PATH, "w") as f:
                f.write(self.filename)

    RE_COMMENT   = re.compile(r"^\s*(?:#.*)?$")
    RE_HEADER    = re.compile(r"^\s*TEMP\s*,\s*TIME\s*(?:#.*)?$", re.IGNORECASE)
    RE_TEMP_TIME = re.compile(r"^\s*\d+\s*,\s*\d+\s*(?:#.*)?$")
    def Validate(text, first_error_only=False):
        "Validate the text of a profile. Returns an array of (Error, Line Number) tuples."
        errors = []
        for i, line in enumerate(text.split('\n')):
            if Profile.RE_COMMENT.match(line):
                continue
            elif Profile.RE_HEADER.match(line):
                continue
            elif Profile.RE_TEMP_TIME.match(line):
                continue
            else:
                errors.append( ("Line has unexpected format.", i+1))
                if first_error_only:
                    return errors
        return errors

    RE_PAIRS     = re.compile(r"^\s*(\d+)\s*,\s*(\d+)\s*(?:#.*)?$", re.MULTILINE)
    def Parse(text):
        "Parse profile into array of (Temp, Time) tuples."
        return [(int(match.group(1)), int(match.group(2))) for match in Profile.RE_PAIRS.finditer(text)]

class ProfileEdit(tk.Frame):
    LIGHTRED = "#FF7F7F"

    def __init__(self, container, profile):
        super().__init__(container)

        self.profile = profile

        container.bind("<Escape>", self.cancel)
        container.bind("<Control-o>", self.open)
        container.bind("<Control-Shift-s>", self.save_as)
        container.bind("<Control-s>", self.update)

        self.text_profile = tk.scrolledtext.ScrolledText(self, undo=True)
        self.text_profile.pack(fill=tk.BOTH, expand=True)
        self.text_profile.focus_set()
        frame_toolbar = tk.Frame(self)
        frame_toolbar.pack(side=tk.BOTTOM, fill=tk.X, padx=4, pady=4)

        self.label_status = tk.Label(frame_toolbar, anchor=tk.W)
        self.label_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        font_bold = TkCustomFont(weight="bold")

        tk.Button(frame_toolbar, text="Validate", command=self.validate).pack(side=tk.LEFT)
        tk.Button(frame_toolbar, text="Update", font=font_bold, command=self.update).pack(side=tk.LEFT)
        tk.Button(frame_toolbar, text="Cancel", command=self.cancel).pack(side=tk.LEFT)
        tk.Button(frame_toolbar, text="Open", command=self.open).pack(side=tk.LEFT, padx=(10,0)) # Sepparate Button groups with padding
        tk.Button(frame_toolbar, text="Save as", command=self.save_as).pack(side=tk.LEFT)

        self.text_profile.insert('1.0', self.profile.text)
        self.highlight_errors(self.profile.errors)
        if self.profile.has_errors():
            self.status_error("Errors in profile.")
        else:
            self.status_info("Valid.")
    
    def clear_errors(self):
        self.text_profile.tag_delete("error")
    def highlight_error(self, line, status):
        self.text_profile.tag_add("error", "{}.0".format(line), "{}.end".format(line))
        self.text_profile.tag_config("error", background=self.LIGHTRED)
        #self.popup = tk.Label(self.text_profile, text="Error Here", bd=1)
        #self.text_profile.window_create("3.10", window=self.popup)
        #self.label_status.config(text="Error: line {}, {}".format(line_n, error), fg="red")
    def highlight_errors(self, errors):
        self.clear_errors()
        for error, line_n in errors:
                self.highlight_error(line_n, error)

    def text(self):
        return self.text_profile.get('1.0', tk.END)

    def status_info(self, status):
        self.label_status.config(text=status, fg="green")
    
    def status_error(self, status):
        self.label_status.config(text=status, fg="red")

    def validate(self, text=None):
        text = text or self.text()
        errors = Profile.Validate(text)
        self.highlight_errors(errors)

        if len(errors) == 0:
            self.status_info("Valid")
        else:
            self.status_error("Errors in profile.")
    
    def update(self):
        self.profile.update(self.text())

        if self.profile.has_errors():
            self.highlight_errors(self.profile.errors)
            self.status_error("Errors in profile.")
        else:
            self.status_info("Updated.")
            self.cancel()
            
    def open(self, event=None):
        if self.profile.open():
            self.clear_errors()
            self.text_profile.delete("1.0","end")
            self.text_profile.insert("1.0", self.profile.text)     
            self.validate(text)
        else:
            self.status_error("Canceled.")

    def save(self, event=None):
        self.profile.update(self.text())
        self.profile.save()

    def save_as(self, event=None):
        self.profile.update(self.text())
        if self.profile.save_as():
            # Todo: Update filename.
           self.status_info("Saved as '{}'.".format(self.profile.filename))
        else:
           self.status_error("Canceled.")

    def cancel(self, event=None):
        self.master.grab_release()
        self.master.withdraw()
        pass

class DialogProfileEdit(tk.Toplevel):
    def __init__(self, parent, profile):
        super().__init__(parent)

        ProfileEdit(self, profile).pack(fill=tk.BOTH, expand=True)

        self.wait_visibility()
        self.grab_set()
        self.transient()



        
if __name__ == '__main__':
    app = tk.Tk()
    app.title("Torch - Edit Profile")
    app.geometry("+60+60")
    profile = Profile("profiles/default.txt")
    ProfileEdit(app, profile).pack(fill=tk.BOTH, expand=True)
    
    app.mainloop()
