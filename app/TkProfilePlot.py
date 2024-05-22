

import tkinter as tk
from itertools import accumulate

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)

class TkProfilePlot(tk.Frame):
    def __init__(self, container, profile):
        super().__init__(container)

        self.profile = profile

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
        
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_profile(self):
        
        profile_temps = [x[0] for x in self.profile.pairs]
        profile_temps.append(profile_temps[-1])
        profile_durations = [x[1] for x in self.profile.pairs]
        profile_elapsed = list(accumulate(profile_durations, initial=0))

        self.target.set_ydata(profile_temps)
        self.target.set_xdata(profile_elapsed)
        ticks_duration = list(range(0, profile_elapsed[-1], 60))
        ticks_labels = list(range(0, (profile_elapsed[-1]//60)+1))
        self.axes.set_xticks(ticks_duration, labels=ticks_labels)
        self.axes.set_ylim([0, max(260, max(profile_temps))])
        self.axes.set_xlim([0, self.profile.duration])

        self.canvas.draw()
        self.canvas.flush_events()
    
    def update_measurements(self, temps, elapsed):
        self.measured.set_ydata(temps)
        self.measured.set_xdata(elapsed)
        self.canvas.draw()
        self.canvas.flush_events()

