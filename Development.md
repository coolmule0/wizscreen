# Development Information

## Current OS

`pyinstaller --onefile wizscreen.py` will create an executable in a `dist` directory

## Windows Exe on Linux

It is hard to generate executables on a different OS, however this is possible on at least Linux to create a windows exe:

``` bash
docker run -v "$(pwd):/src/" cdrx/pyinstaller-windows:python3
```

# Github

This section covers information pertaining to Github.

## Creating executables 

A Github action workflow is in place to run Docker and Wine to generate a windows and linux executable/artifact of this program. It ensures a simple way for users to have access to te end result without needing to go through any code.

The generated executables are available in the `actions` tab in the Github repository browser window. After selecting the most recent build, it is positioned towards the bottom of the page. 