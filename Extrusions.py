import adsk.core, adsk.fusion, adsk.cam, traceback
import os

# Global variables
app = adsk.core.Application.get()
ui = app.userInterface
handlers = []

# Path to DXF files
dxf_dir = os.path.join(os.path.dirname(__file__), 'dxf_profiles')

# Define the command identity information
CMD_ID = 'ExtrusionGenerator'
CMD_NAME = 'Aluminum Extrusion'
CMD_DESC = 'Create aluminum extrusion profiles from DXF files'

# Define the placement in the UI
WORKSPACE_ID = 'FusionSolidEnvironment'  # Solid workspace
PANEL_ID = 'SolidCreatePanel'            # Create panel
COMMAND_BESIDE_ID = 'PrimitivePipe'      # Will be placed after the Pipe command
IS_PROMOTED = True                       # Show in toolbar, not just in dropdown


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs

            profileInput = inputs.itemById('profile')
            lengthInput = inputs.itemById('length')

            profileName = profileInput.selectedItem.name
            length = lengthInput.value

            dxfPath = os.path.join(dxf_dir, f'{profileName}.dxf')

            if not os.path.exists(dxfPath):
                ui.messageBox(f'DXF not found: {dxfPath}')
                return

            # Create a new component
            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox('No active Fusion design')
                return
                
            rootComp = design.rootComponent
            occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            
            # Updated naming convention: profile_type_length
            comp.name = f"{profileName}_{int(length * 10)}"

            # Create a sketch on the XY plane
            sketches = comp.sketches
            xyPlane = comp.xYConstructionPlane
            sketch = sketches.add(xyPlane)
            sketch.name = profileName
            
            # Use the ImportManager for more reliable DXF import
            importManager = app.importManager
            dxfOptions = importManager.createDXF2DImportOptions(dxfPath, xyPlane)
            importManager.importToTarget(dxfOptions, comp)
            
            # Find the imported sketch (usually the last one created)
            for sk in comp.sketches:
                if sk.name != profileName:  # Find the newly imported sketch
                    sketch = sk
                    sketch.name = profileName  # Rename it
                    break
            
            # Wait for computation to complete
            adsk.doEvents()
            sketch.isComputeDeferred = False
            adsk.doEvents()  # Give Fusion time to process
            
            # Check for profiles
            if sketch.profiles.count == 0:
                # Try to fix gaps
                tolerance = adsk.core.ValueInput.createByReal(0.01)
                sketch.fixAll(tolerance)
                adsk.doEvents()  # Give Fusion time to process
                
                # If still no profiles, exit with error
                if sketch.profiles.count == 0:
                    ui.messageBox('No profiles could be created from the DXF.\n\n' + 
                                  'Try cleaning up the DXF file in your CAD application.')
                    return
            
            # Use the first profile for extrusion
            prof = sketch.profiles.item(0)
            
            # Create the extrusion
            extrudes = comp.features.extrudeFeatures
            distance = adsk.core.ValueInput.createByReal(length)
            extrude = extrudes.addSimple(prof, distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            # Success message removed - extrusion created silently

        except Exception as e:
            if ui:
                ui.messageBox(f'Failed: {str(e)}\n\n{traceback.format_exc()}')


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = adsk.core.Command.cast(args.command)
            inputs = cmd.commandInputs

            # Create DXF directory if it doesn't exist
            if not os.path.exists(dxf_dir):
                os.makedirs(dxf_dir)
                ui.messageBox(f'Created DXF profiles directory at: {dxf_dir}\nPlease add your DXF profiles there.')
                return

            # Get list of DXF files
            dxf_files = [f for f in os.listdir(dxf_dir) if f.endswith('.dxf')]
            
            if not dxf_files:
                ui.messageBox(f'No DXF files found in {dxf_dir}. Please add your profile DXF files to this directory.')
                return

            # Create profile dropdown
            dropdown = inputs.addDropDownCommandInput('profile', 'Profile', adsk.core.DropDownStyles.TextListDropDownStyle)
            dropdownItems = dropdown.listItems
            
            for filename in dxf_files:
                name = os.path.splitext(filename)[0]
                dropdownItems.add(name, False)
                
            if dropdownItems.count > 0:
                dropdownItems.item(0).isSelected = True

            # Add length input
            inputs.addValueInput('length', 'Length (mm)', 'mm', adsk.core.ValueInput.createByReal(100))

            # Add event handlers
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

        except Exception as e:
            if ui:
                ui.messageBox(f'Failed: {str(e)}\n\n{traceback.format_exc()}')


def run(context):
    try:
        # Display a shortened message when the add-in is manually run
        if not context['IsApplicationStartup']:
            ui.messageBox('Aluminum Extrusion add-in loaded in CREATE panel.', 'Aluminum Extrusion')
            
        # Clean up any previously created command definition
        cmdDef = ui.commandDefinitions.itemById(CMD_ID)
        if cmdDef:
            cmdDef.deleteMe()
            
        # Create the command definition
        cmdDef = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_DESC)
        
        # Connect to command created event
        onCommandCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        # Add the command to the Create panel in the Solid workspace
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        if workspace:
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            if panel:
                # Add a button control to the panel
                control = panel.controls.itemById(CMD_ID)
                if not control:
                    control = panel.controls.addCommand(cmdDef, COMMAND_BESIDE_ID, False)
                    control.isPromoted = IS_PROMOTED
        
    except Exception as e:
        if ui:
            ui.messageBox(f'Failed to start: {str(e)}')


def stop(context):
    try:
        # Clean up the UI when the add-in is stopped
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        if workspace:
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            if panel:
                control = panel.controls.itemById(CMD_ID)
                if control:
                    control.deleteMe()
                    
        cmdDef = ui.commandDefinitions.itemById(CMD_ID)
        if cmdDef:
            cmdDef.deleteMe()
            
    except:
        if ui:
            ui.messageBox('Failed to clean up the add-in')