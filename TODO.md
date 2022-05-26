# Todo

## Rewrite GUI in TK

Modernize the gui.

- [x] Implement start/stop, elapsed time, and temperature display
- [x] Implement matplotlib based display for profile and temperature readings
- [x] Command line arguments for simulation and polling rate
- [x] Profile editing, save, load
- [x] Select Com port.
- [x] Add about page, utilized libraries.
- [x] Add license page.
- [x] Display Time instead of popup when finished.
- [x] Display minutes instead of seconds on plot.
- [x] Display elapsed seconds as time. mm:ss
- [x] Prevent save/load/edit while oven is started
- [ ] Check for 40 pair max profile size.
- [ ] Package python environment and library dependencies
- [ ] Add documentation for profile format
- [ ] Check Oven Serial Communication.
- [ ] Thread oven communications
- [ ] Resolve
    - [ ] Unpack requires buffer of 4 bytes

## Bugs
- [ ] Save as is incorrect.
- [ ] Profile length of 1 does not set labels properly. Possibly also too short of a profile.

## Extras

- [ ] Use importlib_resources
    - Inlcude ABOUT, LICENSE in binary distribution
    - Include Profiles
    - <https://importlib-resources.readthedocs.io/en/latest/using.html>
- [ ] Use Dialog class for profile edit
- [ ] Simulate notification/setting.
- [ ] Configuration File
    - [ ] Load profile at start
    - [ ] Remember window position
- [ ] Remember Window position.
- [ ] Better profile storage?
- [ ] Provide additional profile features
    - [ ] Explicit cooldown. Check for reasonable value range. End when oven reaches goal temp instead of waiting the entire time.
    - [ ] Slow Ramp instruction to temperature.
- [ ] Token based parsing of profile format
- [ ] Plot in separate file?