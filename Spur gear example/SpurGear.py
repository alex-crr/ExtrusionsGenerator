# Author-Autodesk
# Description-Base Template for creating a Fusion Addin.

from . import commands
from .lib import fusionAddInUtils as futil
import adsk.core


def run(context):
    try:
        # Display a message when the add-in is manually run.
        if not context['IsApplicationStartup']:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('The Spur Gear sample add-in has been loaded and has added a new "Spur Gear" command to the CREATE panel in the SOLID tab of the DESIGN workspace.', 'Command Samples')

        # Run the start function in each command.
        commands.start()

    except:
        futil.handle_error('run')


def stop(context):
    try:
        # Remove all of the event handlers.
        futil.clear_handlers()

        # Run the stop function in each command.
        commands.stop()

    except:
        futil.handle_error('stop')