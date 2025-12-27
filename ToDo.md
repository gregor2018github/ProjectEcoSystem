### Todo





- [ ] Add more information to the table in the statistics window
  - [ ] Total current population (predators and preys)
  - [ ] Average age of animals (separately for predators and preys)
  - [ ] Average energy levels (separately for predators and preys)
  - [ ] Animals hunted down in the last 100 rounds
  - [ ] Animals died of starvation in the last 100 rounds
  - [ ] Animals died of old age in the last 100 rounds
  - [ ] Total animals born in the last 100 rounds
- [ ] Reduce the refresh rate of the table to 1 in 70 to save performance

- [ ] Update Git page with new screenshots and littel video of the simulation running

- [ ] Add heritage of traits from parents to children
  - [ ] give every induvidual unique properties instead of hardcoded values from settings
  - [ ] add mixing algorithm (distribution of finite amount of points between different traits to avoid overpowered animals)

- [ ] Multithreading for better performance
  - [ ] separate predator and prey updates into different threads
  - [ ] subthreads per animal group (negative effects of unfair advantages for animals late in the queue should be minimal)
 
### Done ✓

- [x] Population graph y-axis can switch between relative and absolute mode by button
- [x] Add better mating system that requires two animals to interact, currently new animals spawn randomly
  - [x] Animals need new mating state
  - [x] Keep track of generational statistics
- [x] Limit the Frame Rate for the simulation view only with the settings from the start screen
- [x] In statistics screen limit the Frame Rate to 60 when paused, otherwise unlimited
- [x] Add click sounds to the button and dropdowns in the start screen
- [x] Cannot make screenshots anymore, the simulation minimizes when not in focus, must be changed back
- [x] Add a start screen where you can change settings and launch the simulation
- [x] more options to statistics window
  - [x] dropdown to select max number of points shown in graphs
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