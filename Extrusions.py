import adsk.core
import traceback
import os
import sys

def run(context):
    try:
        # Get the UI
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Add the current directory to sys.path to enable imports
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Now import the commands module (after path is set)
        import commands
        
        # Start the commands
        commands.start()
        
        # More helpful message about where to find the command
        if not context['IsApplicationStartup']:
            ui.messageBox('Aluminum Extrusion add-in loaded in the CREATE panel of the SOLID workspace', 'Aluminum Extrusion')
            
    except Exception as e:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox(f'Failed to start: {str(e)}\n\n{traceback.format_exc()}')

def stop(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Add the current directory to sys.path to enable imports
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # First try to clean up using our command module
        try:
            # Fix the import scope issue by ensuring we import before referencing
            import commands as commands_module
            commands_module.stop()
        except Exception as e:
            ui.messageBox(f'Module cleanup failed: {str(e)}')
        
        # Fallback cleanup - directly remove the command definition
        try:
            # Import config to get proper command ID 
            import config
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