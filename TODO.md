# Todo

## Rewrite GUI in TK

Modernize the gui.

- [x] Implement start/stop, elapsed time, and temperature display
- [x] Implement matplotlib based display for profile and temperature readings
- [x] Command line arguments for simulation and polling rate
- [ ] Profile editing, save, load
- [ ] Select Com port.
- [ ] Simulate notification.
- [ ] Add about page, utilized libraries.
- [ ] Add license page.
- [ ] Display Time instead of popup when finished.
- [ ] Display minutes instead of seconds.
- [ ] Display elapsed seconds as time. mm:ss
- [ ] Prevent save/load/edit while oven is started
- [ ] Add menu hotkeys
    - `F2` to edit profile

## Extras

- [ ] Different units
- [ ] Configuration
- [ ] Remember Window position.
- [ ] Better profile storage?
- [ ] Provide additional profile features
    - [ ] Explicit cooldown. Check for reasonable value range. End when oven reaches goal temp instead of waiting the entire time.
    - [ ] Slow Ramp instruction to temperature.