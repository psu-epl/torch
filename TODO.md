# Todo

## Rewrite GUI in TK

Modernize the gui.

- [x] Implement start/stop, elapsed time, and temperature display
- [x] Implement matplotlib based display for profile and temperature readings
- [x] Command line arguments for simulation and polling rate
- [x] Profile editing, save, load
- [ ] Select Com port.
- [ ] Simulate notification/setting.
- [ ] Add about page, utilized libraries.
- [ ] Add license page.
- [x] Display Time instead of popup when finished.
- [x] Display minutes instead of seconds on plot.
- [x] Display elapsed seconds as time. mm:ss
- [x] Prevent save/load/edit while oven is started
- [ ] Check for 40 pair max profile size.

## Extras

- [ ] Configuration file
- [ ] Remember Window position.
- [ ] Better profile storage?
- [ ] Provide additional profile features
    - [ ] Explicit cooldown. Check for reasonable value range. End when oven reaches goal temp instead of waiting the entire time.
    - [ ] Slow Ramp instruction to temperature.
- [ ] Token based parsing of profile format