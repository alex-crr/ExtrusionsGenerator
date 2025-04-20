# This file makes the directory a Python package

from . import commands
import traceback

def run(context):
    try:
        # Display a shortened message when the add-in is manually run
        if not context['IsApplicationStartup']:
            from . import config
            if config.DEBUG:
                print("Aluminum Extrusion add-in started")
        
        # Start all commands
        commands.start()
            
    except:
        import adsk.core
        ui = adsk.core.Application.get().userInterface
        if ui:
            ui.messageBox(f'Failed to start Aluminum Extrusion add-in:\n{traceback.format_exc()}')


def stop(context):
    try:
        # Stop all commands
        commands.stop()
            
    except:
        import adsk.core
        ui = adsk.core.Application.get().userInterface
        if ui:
            ui.messageBox('Failed to clean up Aluminum Extrusion add-in')
