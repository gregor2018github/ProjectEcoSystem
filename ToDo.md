### Todo

- [ ] Add more variables to the settings menu
  - [ ] Max ages
  - [ ] Food consumption levels for different activities
  - [ ] Starting values for gras
- [ ] Improve the visuals of the settings screen  
- [ ] Add a start screen where you can change settings and launch the simulation
- [ ] Add better mating system that requires two animals to interact, currently new animals spawn randomly
  - [ ] Animals need new mating state
  - [ ] Keep track of generational statistics
- [ ] Add heritage of traits from parents to children
  - [ ] give every induvidual unique properties instead of hardcoded values from settings
  - [ ] add mixing algorithm (distribution of finite amount of points between different traits)
- [ ] Improve performance by only considering other animals with low distances instead of every animal
 
### Done ✓

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