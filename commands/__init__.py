import os
import sys
import importlib

def start():
    try:
        # Import the command modules
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from AluminumExtrusion import entry as aluminum_extrusion_cmd
        
        # Start the command
        aluminum_extrusion_cmd.start()
    except Exception as e:
        import adsk.core
        ui = adsk.core.Application.get().userInterface
        ui.messageBox(f'Failed to start commands: {str(e)}')

def stop():
    try:
        # Import the command modules
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from AluminumExtrusion import entry as aluminum_extrusion_cmd
        
        # Stop the command
        aluminum_extrusion_cmd.stop()
    except Exception as e:
        import adsk.core
        ui = adsk.core.Application.get().userInterface
        ui.messageBox(f'Failed to stop commands: {str(e)}')