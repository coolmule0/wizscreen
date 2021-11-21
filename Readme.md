# WizScreen

Set your Wiz Bulb to match the colors on screen. Finds the dominant on-screen color and requests the bulb change accordingly. Fastest response time on the order of 0.2s from testing.

## How to use

### Executables

Executables are distributed within this repository for windows and unix-like systems. This is the easiest option to get started quickly.

They can be found in the most recent build by visiting the `Actions` tab, selecting the top most build with a green tick next to the name, and selecting from the `Artifacts` section.

Simply run the executable to start the program. `Ctrl+C` to quit. Run from the command line to specify extra command arguments

### From Source

Download the code. Ensure you have a modern python installed, and `pipenv`. Then in this downloaded folder run `pipenv install` to obtain the correct environment. Finally `pipenv run main.py` to execute the script.

### Command Arguments

Specify additional command arguments to change default values, or change certain behaviour.

| Argument  | Sequential Argument Example                  | Description               |
|----|----|----|
|-h, --help | -            |show this help message and exit|
|-d, --debug | -           |Prints more verbose messages. Sets to INFO level |
|-s, --search| -          |Search for available bulbs, print IP addresses, and exit |
|-ip IP | 192.168.1.66              |known IP of bulb to use 
|--broadcast_space BROADCAST_SPACE | 192.168.1.225 |              Search over this space of IP for possible bulbs. Use when IP of desired bulb unknown 
|-b [0-255], --brightness [0-255]| 70 | minimum desired brightness of bulb|
|-r RATE, --rate RATE| 20 | refresh rate of color change (hz)|
|-m MONITOR --monitor MONITOR | 1 | Monitor number to use |
|-q [1-10], --quality [1-10]| 5 |Quality of dominant color calculation. 1: highest, 10: lowest 
|--screen_percent [1-100]| 60 |Amount of screen to consider, in percentage. Chances are that things around the edge of the screen do not need consideration |
|-d, --display| - | Show a window of expected color captured from screen, and sent to bulb |
