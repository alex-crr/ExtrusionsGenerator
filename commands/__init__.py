import os
import sys
import importlib

# Import only the modules that actually exist
# The error showed you were trying to import modules like commandDialog that don't exist
from .Extrusion import entry as extrusion_command

# List of all commands in the add-in - only include what exists
commands = [
    extrusion_command
]

def start():
    try:
        # Start the command
        extrusion_command.start()
    except Exception as e:
        import adsk.core
        ui = adsk.core.Application.get().userInterface
        ui.messageBox(f'Failed to start commands: {str(e)}')

def stop():
    try:
        # Stop the command
        extrusion_command.stop()
    except Exception as e:
        import adsk.core
        ui = adsk.core.Application.get().userInterface
        ui.messageBox(f'Failed to stop commands: {str(e)}')