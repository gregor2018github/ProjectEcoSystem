### Todo


- [ ] more options to statistics window
  - [ ] dropdown to select refresh rate of two graphs
  - [ ] dropdown to select max number of points shown in graphs
- [ ] Add a start screen where you can change settings and launch the simulation
- [ ] Add better mating system that requires two animals to interact, currently new animals spawn randomly
  - [ ] Animals need new mating state
  - [ ] Keep track of generational statistics
- [ ] Add heritage of traits from parents to children
  - [ ] give every induvidual unique properties instead of hardcoded values from settings
  - [ ] add mixing algorithm (distribution of finite amount of points between different traits)

 
### Done ✓

- [x] Add FPS counter
- [x] Repair FPS limits, currently settings value is non functional
- [x] Improve performance of phase diagram by limiting number of points drawn
- [x] Improve performance of population graph by limiting number of points drawn
- [x] Add phase diagram to statistics window
- [x] Add basic information table to statistics window
- [x] Improve performance by using a spatial hash grid for animal movements
- [x] Improve the visuals of the settings screen
  - [x] center the settings window on the screen
  - [x] center the buttons within the settings window
  - [x] empty lines between different sections for better readability
  - [x] Cursor blink effect
  - [x] arrow buttons can change the cursor position (left/right)
  - [x] arrow buttons can change the value of the setting (up/down)
  - [x] add side bar indication of scroll position
- [x] Add more variables to the settings menu
  - [x] Max ages
  - [x] Food consumption levels for different activities
  - [x] Starting values for grass
- [x] Add current energy consumption to the hover statistics
- [x] Add "Starving" with True or False to the hover statistics
- [x] Add hover statistics for animal instances
- [x] Add age system
  - [x] Count and store age per animal instance
  - [x] Animals can die of old age
  - [x] Keep track of detailed death stats (hunger, age, hunted down)
- [x] Add click effects for buttons
- [x] Add hover effects for buttons 
- [x] Add event_handler.py and refactor existing code accordingly
- [x] Add pause button
- [x] Refactor into several scripts for readability