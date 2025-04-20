import adsk.core
import traceback
import os
import sys

def run(context):
    try:
        # Debug message to verify the add-in is loading
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Debug: Add-in loading started')
        
        # Add the current directory to sys.path to enable imports
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Now import the commands module (after path is set)
        import commands
        
        # Start the commands
        commands.start()
            
    except Exception as e:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox(f'Failed to start: {str(e)}\n\n{traceback.format_exc()}')


def stop(context):
    try:
        # Only import if not already imported
        if 'commands' not in sys.modules:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            import commands
            
        # Stop all commands
        commands.stop()
            
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox('Failed to clean up the add-in')