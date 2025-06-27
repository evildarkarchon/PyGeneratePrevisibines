#!/usr/bin/env python3
"""PyGeneratePrevisibines - Python port of PJM's GeneratePrevisibines batch file.

This is a convenience wrapper that imports and runs the main function
from previs_builder.py. This allows the tool to be run as:
    python PyGeneratePrevisibines.py [args]

Or when installed:
    PyGeneratePrevisibines [args]

Original batch file parameters are supported:
    PyGeneratePrevisibines.py [-clean|-filtered|-xbox] [-bsarch] [plugin.esp]
"""

from previs_builder import main

if __name__ == "__main__":
    main()
