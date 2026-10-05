import adsk.core
import traceback

from . import commands, config

def run(context):
    try:
        # Get the UI
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Start the commands
        commands.start()

            
    except Exception as e:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox(f'Failed to start: {str(e)}\n\n{traceback.format_exc()}')

def stop(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # First try to clean up using our command module
        try:
            commands.stop()
        except Exception as e:
            ui.messageBox(f'Module cleanup failed: {str(e)}')
        
        # Fallback cleanup - directly remove the command definition
        try:
            cmdId = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_extrusion'
            
            # Clean up the UI manually as a fallback
            workspace = ui.workspaces.itemById('FusionSolidEnvironment')
            if workspace:
                panel = workspace.toolbarPanels.itemById('SolidCreatePanel')
                if panel:
                    control = panel.controls.itemById(cmdId)
                    if control:
                        control.deleteMe()
            
            # Remove command definition
            cmdDef = ui.commandDefinitions.itemById(cmdId)
            if cmdDef:
                cmdDef.deleteMe()
        except Exception as e:
            ui.messageBox(f'Direct cleanup failed: {str(e)}')
            
    except Exception as e:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox(f'Failed to clean up the add-in: {str(e)}\n\n{traceback.format_exc()}')