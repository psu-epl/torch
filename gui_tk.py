
import argparse
import time
import re
from itertools import accumulate

import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

import TorchOven

from ProfileEdit import Profile, DialogProfileEdit, TkCustomFont

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Parse Command line options
        parser = argparse.ArgumentParser(description="Provide a GUI for control of RN200+ Reflow Oven")
        parser.add_argument('-s', '--sim', help='simulate serial connection to reflow oven', action='store_true')
        parser.add_argument('--rate', help='set polling rate for temperature updates in milliseconds', type=int, default=1000)
        self.args = parser.parse_args()
    
        self.oven = None
        self.profile = Profile("profiles/default.txt", self.update_profile)

        self.measured_temps = []    # Record Measured Temperature Values
        self.measured_elapsed = []  # Record Times of measurement
        self.last_temp = '...'      # Holds last temperature or info/error message
        self.elapsed_seconds = 0    # Holds count of elapsed seconds

        self.geometry("+100+100")
        self.title("Torch - Reflow Oven RN200+ Serial Controller")

        self.init_menu()
        self.init_plot()
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
                
        self.withdraw()

    def init_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        self.menubar = menubar

        menu_file = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=menu_file, underline=0)
        self.bind("<F2>", self.profile_edit)
        self.bind("<Control-o>", self.profile_open)
        self.bind("<Control-s>", self.profile_save_as)
        menu_file.add_command(label="Edit Profile", underline=0, accelerator="F2", command=self.profile_edit)
        menu_file.add_command(label="Open Profile", underline=0, accelerator="Ctrl-o", command=self.profile_open)
        menu_file.add_command(label="Save Profile as", underline=0, accelerator="Ctrl-s", command=self.profile_save_as)
        menu_file.add_separator()
        menu_file.add_command(label="Exit", underline=1, command=self.destroy)
        menubar.add_command(label="Profile: ", command=self.profile_edit)

    def init_plot(self):
        
        figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(figure, self)
        axes = figure.add_subplot()
        self.target, = axes.step([], [], "g", where="post", label="Target")
        self.measured, = axes.plot([], [], "r", label="Measured")

        axes.set_title("Oven Temperature")
        axes.set_ylabel("Temperature (°C)")
        axes.set_xlabel("Elapsed Time (s)")
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
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.bar.pack(fill=tk.X)

        self.label_temp.pack(side=tk.LEFT)
        self.label_time.pack(side=tk.LEFT)
        self.button_start.pack(side=tk.RIGHT, ipadx=10)
        self.button_start.focus_set()

    
    def update_profile(self):
        # Update profile name on menubar
        self.menubar.entryconfig(2, label="Profile: "+self.profile.name())
        
        profile_temps = [x[0] for x in self.profile.pairs]
        profile_temps.append(profile_temps[-1])
        profile_durations = [x[1] for x in self.profile.pairs]
        profile_elapsed = list(accumulate(profile_durations, initial=0))
        self.profile_duration = profile_elapsed[-1]

        ticks_duration = list(range(0, profile_elapsed[-1], 60))

        self.target.set_ydata(profile_temps)
        self.target.set_xdata(profile_elapsed)

        self.axes.set_xticks(ticks_duration)
        self.axes.set_ylim([0, max(260, max(profile_temps))])
        self.axes.set_xlim([0, self.profile_duration])

        self.canvas.draw()
        self.canvas.flush_events()
    
    def update_measurements(self):
        self.measured.set_ydata(self.measured_temps)
        self.measured.set_xdata(self.measured_elapsed)
        self.canvas.draw()
        self.canvas.flush_events()

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

        self.label_time.config(text="Elapsed: {} s".format(self.elapsed_seconds))

    def timer_start(self):
        self.timer = self.after(self.args.rate, self.action_read)

    def action_start(self):
        assert(self.oven is None)
        
        self.oven = TorchOven.VirtualTorchOven()
        
        self.oven.init_sequence()
        self.oven.send_profile(self.profile.pairs)
        self.oven.start()

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
        except Exception as error:
            self.read_failures += 1
            temp = "ERR"
            print(e)
        else:
            self.read_failures = 0 # Reset failures
            self.measured_elapsed.append(elapsed)
            self.measured_temps.append(temp)
            self.update_measurements()
        finally:
            self.elapsed_seconds = int(elapsed)
            self.last_temp = temp
        
        if elapsed >= self.profile_duration:
            self.action_stop()
            tk.messagebox.showinfo(title='Reflow Cycle Complete', message="Reflow cycle has concluded.")
            return
               
        self.update_bar()

    def profile_edit(self, event=None):
        if self.oven:
            return
        dialog = DialogProfileEdit(self, self.profile)
        dialog.title("Torch - Edit Profile")
    
    def profile_open(self, event=None):
        if self.oven:
            return
        self.profile.open()
        
    def profile_save_as(self, event=None):
        if self.oven:
            return
        self.profile.save_as()

if __name__ == '__main__':
    app = App()
    app.mainloop()
