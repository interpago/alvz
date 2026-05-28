#!/usr/bin/env python3
"""Alvz Language - Entry point wrapper.

Delega la ejecucion al paquete modular alvz/
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alvz import main

if __name__ == "__main__":
    main()
