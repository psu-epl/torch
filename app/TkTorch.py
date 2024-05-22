
import argparse
import time
from struct import error as StructError

import tkinter as tk

from .TkProfileEdit import *
from .TkProfilePlot import *
from .TkGui import *

from oven import TorchOven

from PIL import Image, ImageTk

class Torch(tk.Tk):
    ICON_PATH = "Torch.png"

    def __init__(self):
        super().__init__()

        # Parse Command line options
        parser = argparse.ArgumentParser(description="Provide a GUI for control of RN200+ Reflow Oven")
        parser.add_argument('-s', '--sim', help='simulate serial connection to reflow oven', action='store_true')
        parser.add_argument('--rate', help='set polling rate for temperature updates in milliseconds', type=int, default=1000)
        self.args = parser.parse_args()
    
        self.oven = None
        self.simulate_oven = tk.BooleanVar(self, self.args.sim)
        self.profile = Profile(callback=self.update_profile)

        self.measured_temps = []    # Record Measured Temperature Values
        self.measured_elapsed = []  # Record Times of measurement
        self.last_temp = '...'      # Holds last temperature or info/error message
        self.elapsed_seconds = 0    # Holds count of elapsed seconds

        self.geometry("+100+100")
        self.title("Torch - Reflow Oven RN200+ Serial Controller")
        im = Image.open(self.ICON_PATH)
        photo = ImageTk.PhotoImage(im)
        self.wm_iconphoto(True, photo)
        # self.iconphoto()

        self.init_menu()
        self.profile_plot = TkProfilePlot(self, self.profile)
        self.init_bar()

        self.update_profile()
        self.update_measurements()
        self.update_bar()
        self.layout()
        
        if self.profile.has_errors():
            self.profile_edit()
        
        self.protocol('WM_DELETE_WINDOW', self.confirm_exit)
    
    def confirm_exit(self):
        if self.profile.has_changes:
            res = tk.messagebox.askyesnocancel(title="Save Profile", message="Would you like to save changes to profile?")
            if res == None:
                return
            if res == tk.YES:
                self.profile.save_as()
        self.quit()

    def init_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        self.menubar = menubar

        menu_file = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=menu_file, underline=0)
        menu_file.add_checkbutton(label="Simulate Oven", variable=self.simulate_oven)
        menu_file.add_separator()
        menu_file.add_command(label="Edit Profile", underline=0, accelerator="F2", command=self.profile_edit)
        menu_file.add_command(label="Open Profile", underline=0, accelerator="Ctrl-o", command=self.profile_open)
        menu_file.add_command(label="Save Profile as", underline=0, accelerator="Ctrl-s", command=self.profile_save_as)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", underline=1, command=self.destroy)
        
        menu_help = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Help", menu=menu_help, underline=0)
        menu_help.add_command(label="License", underline=0, command=self.show_license)
        menu_help.add_command(label="About", underline=0, command=self.show_about)

        menubar.add_separator()
        menubar.add_command(label="Profile:", command=self.profile_edit)
        self.menuindex_profile = menubar.index("Profile:")
        
        self.bind("<F2>", self.profile_edit)
        self.bind("<Control-o>", self.profile_open)
        self.bind("<Control-s>", self.profile_save_as)

    def init_plot(self):
        
        figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(figure, self)
        axes = figure.add_subplot()
        self.target, = axes.step([], [], "g", where="post", label="Target")
        self.measured, = axes.plot([], [], "r", label="Measured")

        axes.set_title("Oven Temperature")
        axes.set_ylabel("Temperature (°C)")
        axes.set_xlabel("Elapsed Time (m)")
        axes.grid(visible=True)
        axes.legend(handles=[self.target, self.measured])
        axes.margins(0)

        self.axes = axes
    
    def init_bar(self):
        # Create larger font object.
        font_bar = TkCustomFont('TkFixedFont', weight="bold", size=lambda s: s+6)

        # Create Lower Toolbar
        self.bar = tk.Frame(self)

        self.label_temp = tk.Label(self.bar, font=font_bar, text="", width=12)
        self.label_time = tk.Label(self.bar, font=font_bar, text="", width=12)
        self.button_start = tk.Button(self.bar, font=font_bar, width=6, text="Start", fg="green", command=self.action_start)
    
    def layout(self):
        self.profile_plot.pack(fill=tk.BOTH, expand=True)
        self.bar.pack(fill=tk.X)

        self.label_temp.pack(side=tk.LEFT)
        self.label_time.pack(side=tk.LEFT)
        self.button_start.pack(side=tk.RIGHT, ipadx=10)
        self.button_start.focus_set()

    
    def update_profile(self):
        # Update profile name on menubar
        self.menubar.entryconfig(self.menuindex_profile, label="Profile: " + self.profile.name())

        self.profile_plot.update_profile()
    
    def update_measurements(self):
        self.profile_plot.update_measurements(self.measured_temps, self.measured_elapsed)

    def show_status(self, status):
        self.label_temp.config(text="Temp: {:3s}".format(status))
        self.label_time.config(text="")

    def update_bar(self):
        started = self.oven is not None and self.oven.started

        if started:
            self.button_start.config(text="Stop", fg="red", command=self.action_stop)
        else:
            self.button_start.config(text="Start", fg="green", command=self.action_start) 

        if isinstance(self.last_temp, str):
            self.label_temp.config(text="Temp: {:3s}".format(self.last_temp))
        else:
            self.label_temp.config(text="Temp: {:3d} °C".format(self.last_temp))

        self.label_time.config(text="Elapsed: {:02}:{:02}".format(self.elapsed_seconds//60, self.elapsed_seconds%60))

    def timer_start(self):
        self.timer = self.after(self.args.rate, self.action_read)

    def action_start(self):
        assert(self.oven is None)
        
        try:
            if self.simulate_oven.get():
                self.oven = TorchOven.VirtualTorchOven()
            elif port := PickComport(self):
                if __debug__:
                    print("Trying COM port:", port)
                self.oven = TorchOven.TorchOven(port)
            else:
                return
        except Exception as e:
            if __debug__:
                print(*sys.exc_info())
            tk.messagebox.showerror(title='Error connecting to Oven', message=e)
            return
            
        try:
            self.show_status("Oven Init...")
            self.oven.init_sequence()
            self.show_status("Sending Profile...")
            self.oven.send_profile(self.profile.pairs)
            self.show_status("Oven Start...")
            self.oven.start()
        except StructError:
            if __debug__:
                print(*sys.exc_info())
            self.oven = None # Clear oven variable to allow restart.
            tk.messagebox.showerror(title='Error communicating with oven', message="Read unexpected bytes from COM port. Perhaps try a different port or check if the oven is on.")
            self.update_bar()
            return
        except Exception as e:
            if __debug__:
                print(*sys.exc_info())
            self.oven.stop() # Try to stop the oven just to be safe.
            self.oven = None # Clear oven variable to allow restart.

            tk.messagebox.showerror(title='Error communicating with oven', message=e)
            self.update_bar()
            return


        self.time_started = time.time()
        self.measured_temps = []
        self.measured_elapsed = []
        self.last_temp = "..."
        self.elapsed_seconds = 0
        self.read_failures = 0

        self.update_bar()
        self.timer_start()

    def action_stop(self):
        assert(self.oven is not None and self.oven.started)

        self.oven.stop()
        self.oven.close()
        self.oven = None

        self.after_cancel(self.timer)
        self.timer = None

        self.update_bar()

    def action_read(self):
        assert(self.oven is not None and self.oven.started)

        elapsed = time.time() - self.time_started
        self.timer_start()

        temp = 0
        try:
            temp = self.oven.read_temp()
        except Exception:
            if __debug__:
                print(*sys.exc_info())
            self.read_failures += 1
            temp = "ERR"
        else:
            self.read_failures = 0 # Reset failures
            self.elapsed_seconds = int(elapsed)
            self.last_temp = temp
            self.measured_elapsed.append(elapsed)
            self.measured_temps.append(temp)        
        finally:
            self.elapsed_seconds = int(elapsed)
            self.last_temp = temp
        
        if elapsed >= self.profile.duration:
            self.action_stop()
            tk.messagebox.showinfo(title='Reflow Cycle Complete', message="Reflow cycle has concluded.")
            return
               
        self.update_bar()
        self.update_measurements()

    def profile_edit(self, event=None):
        if self.oven:
            return
        dialog = DialogProfileEdit(self, self.profile)
        dialog.title("Torch - Edit Profile")
        dialog.iconbitmap(self.ICON_PATH)
    
    def profile_open(self, event=None):
        if self.oven:
            return
        self.profile.open()
        
    def profile_save_as(self, event=None):
        if self.oven:
            return
        self.profile.save_as()
    
    def show_license(self):
        with open('LICENSE') as file:
            license = TkShowText(self, title="Torch - License", text=file.read())
            license.iconbitmap(self.ICON_PATH)
    
    def show_about(self):
        with open('ABOUT') as file:
            about = TkShowText(self, title="Torch - About", text=file.read())
            about.iconbitmap(self.ICON_PATH)

def main():
    app = Torch()
    app.mainloop()

if __name__ == '__main__':
    main()