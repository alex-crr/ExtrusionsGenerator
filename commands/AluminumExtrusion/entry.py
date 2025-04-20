import adsk.core
import adsk.fusion
import adsk.cam
import os
import sys
import traceback

# Use absolute imports instead of relative
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

# Global variables
app = adsk.core.Application.get()
ui = app.userInterface
handlers = []

# Helper function for debug logging to Fusion 360
def debug_log(message):
    if config.DEBUG:
        app.log(message)

# Command identity information
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_aluminum_extrusion'
CMD_NAME = 'Aluminum Extrusion'
CMD_DESC = 'Create aluminum extrusion profiles from DXF files'

# Command placement in the UI
WORKSPACE_ID = 'FusionSolidEnvironment'  # Solid workspace
PANEL_ID = 'SolidCreatePanel'            # Create panel
COMMAND_BESIDE_ID = 'PrimitivePipe'      # Will be placed after the Pipe command
IS_PROMOTED = True                       # Show in toolbar, not just in dropdown

# Path to DXF files (parent directory) - updated for new structure
dxf_parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dxf_profiles')

# Series options
SERIES_OPTIONS = ['2020', '3030', '4040']


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs

            # Get input values
            seriesInput = inputs.itemById('series')
            profileInput = inputs.itemById('profile')
            lengthInput = inputs.itemById('length')

            seriesName = seriesInput.selectedItem.name
            profileName = profileInput.selectedItem.name
            length = lengthInput.value

            # Path to selected series subfolder
            dxf_dir = os.path.join(dxf_parent_dir, seriesName)
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
            
            # Get the initial timeline marker - to know where we started
            timeline = design.timeline
            startingTimelineIndex = timeline.count - 1
            
            occ = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
            comp = occ.component
            
            # Updated naming convention: series_profile_type_length
            comp.name = f"{seriesName}_{profileName}_{int(length * 10)}"

            # FIXED: Don't create a sketch directly - just get the XY plane reference
            xyPlane = comp.xYConstructionPlane
            
            # Use the ImportManager for reliable DXF import - this will create one sketch
            importManager = app.importManager
            dxfOptions = importManager.createDXF2DImportOptions(dxfPath, xyPlane)
            importManager.importToTarget(dxfOptions, comp)
            
            # Find the imported sketch
            sketch = None
            for sk in comp.sketches:
                sketch = sk  # There should only be one sketch after import
                sketch.name = profileName  # Rename it
                break
                
            if not sketch:
                ui.messageBox('Failed to import sketch from DXF file')
                return
            
            # Wait for computation to complete
            adsk.doEvents()
            sketch.isComputeDeferred = False
            adsk.doEvents()
            
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
            
            # Assign Aluminum material silently
            try:
                # Get the Fusion Material Library
                materialLib = app.materialLibraries.itemByName('Fusion Material Library')
                if materialLib:
                    # Try Aluminum first, then Gold as fallback
                    material = materialLib.materials.itemByName('Aluminum')
                    if not material:
                        material = materialLib.materials.itemByName('Gold')
                    
                    # Apply material if found
                    if material:
                        comp.material = material
            except:
                # Silently continue if material assignment fails
                pass
            
            # IMPROVED: Timeline compression
            try:
                # Get the final timeline marker
                endingTimelineIndex = timeline.count - 1
                
                # Only create a group if we have at least two operations
                if endingTimelineIndex > startingTimelineIndex:
                    newGroup = timeline.timelineGroups.add(startingTimelineIndex + 1, endingTimelineIndex)
                    newGroup.name = f"Extrusion {profileName}"
                    newGroup.isCollapsed = True
            except:
                # Silently fail if grouping doesn't work
                pass

        except Exception as e:
            if ui:
                ui.messageBox(f'Failed: {str(e)}\n\n{traceback.format_exc()}')


# Handler for when inputs change
class SeriesSelectionChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        try:
            # Get the input that triggered this event
            changedInput = args.input
            
            # Only respond if the series dropdown was changed
            if changedInput.id == 'series':
                # Get the command inputs
                inputs = args.inputs
                
                # Get both dropdowns
                seriesInput = inputs.itemById('series')
                profileInput = inputs.itemById('profile')
                
                # Clear profile dropdown
                profileInput.listItems.clear()
                
                # Get selected series
                selectedSeries = seriesInput.selectedItem.name
                seriesDir = os.path.join(dxf_parent_dir, selectedSeries)
                
                # Check if series directory exists
                if not os.path.exists(seriesDir):
                    os.makedirs(seriesDir)
                    ui.messageBox(f'Created series directory at: {seriesDir}\nPlease add your DXF profiles for {selectedSeries} series there.')
                    return
                
                # Populate profile dropdown with DXF files from the selected series
                dxf_files = [f for f in os.listdir(seriesDir) if f.endswith('.dxf')]
                
                if dxf_files:
                    for filename in dxf_files:
                        name = os.path.splitext(filename)[0]
                        profileInput.listItems.add(name, False)
                    
                    # Select first item
                    if profileInput.listItems.count > 0:
                        profileInput.listItems.item(0).isSelected = True
                else:
                    ui.messageBox(f'No DXF files found in {seriesDir}. Please add your profile DXF files for {selectedSeries} series there.')
                
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

            # Create main dxf_profiles directory if it doesn't exist
            if not os.path.exists(dxf_parent_dir):
                os.makedirs(dxf_parent_dir)
                
                # Create series subfolders
                for series in SERIES_OPTIONS:
                    os.makedirs(os.path.join(dxf_parent_dir, series), exist_ok=True)
                
                ui.messageBox(f'Created DXF profiles directories at: {dxf_parent_dir}\nPlease add your DXF profiles to the appropriate series folders.')
                return

            # Create series dropdown
            seriesDropdown = inputs.addDropDownCommandInput('series', 'Series', adsk.core.DropDownStyles.TextListDropDownStyle)
            seriesItems = seriesDropdown.listItems
            
            # Add series options
            for series in SERIES_OPTIONS:
                seriesItems.add(series, False)
            
            # Select first series by default
            if seriesItems.count > 0:
                seriesItems.item(0).isSelected = True
            
            # Create profile dropdown (will be populated based on selected series)
            profileDropdown = inputs.addDropDownCommandInput('profile', 'Profile', adsk.core.DropDownStyles.TextListDropDownStyle)
            
            # Add length input
            inputs.addValueInput('length', 'Length (mm)', 'mm', adsk.core.ValueInput.createByReal(100))
            
            # Populate profile dropdown initially
            selectedSeries = seriesItems.item(0).name
            seriesDir = os.path.join(dxf_parent_dir, selectedSeries)
            
            # Create series directory if it doesn't exist
            if not os.path.exists(seriesDir):
                os.makedirs(seriesDir)
                ui.messageBox(f'Created series directory at: {seriesDir}\nPlease add your DXF profiles for {selectedSeries} series there.')
            else:
                # Add profiles from selected series
                dxf_files = [f for f in os.listdir(seriesDir) if f.endswith('.dxf')]
                
                if dxf_files:
                    for filename in dxf_files:
                        name = os.path.splitext(filename)[0]
                        profileDropdown.listItems.add(name, False)
                    
                    if profileDropdown.listItems.count > 0:
                        profileDropdown.listItems.item(0).isSelected = True
                else:
                    ui.messageBox(f'No DXF files found in {seriesDir}. Please add your profile DXF files for {selectedSeries} series there.')

            # Add event handlers for command execution
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            
            # Add event handler for input changes - connect to the command
            onInputChanged = SeriesSelectionChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)

        except Exception as e:
            if ui:
                ui.messageBox(f'Failed: {str(e)}\n\n{traceback.format_exc()}')


def start():
    try:
        # Get the command definition or create it if it doesn't exist
        cmdDef = ui.commandDefinitions.itemById(CMD_ID)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_DESC)
        
        # Ensure resource folder exists and is valid
        resourceFolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
        if not os.path.exists(resourceFolder):
            os.makedirs(resourceFolder, exist_ok=True)
            print(f"Created missing resource folder: {resourceFolder}")
        
        # Make sure we have at least empty icon files
        icon_sizes = ["16x16", "32x32", "64x64"]
        for size in icon_sizes:
            icon_path = os.path.join(resourceFolder, f"{size}.png")
            if not os.path.exists(icon_path):
                # Create a minimal valid PNG file (single pixel transparent) as a placeholder
                try:
                    # Try to create an empty icon - but if we can't, it's not critical
                    with open(icon_path, 'wb') as f:
                        # Minimal valid PNG file (1x1 transparent pixel)
                        f.write(bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da6364000002000001e2908d580000000049454e44ae426082'))
                except:
                    pass
        
        # Set icon path (even if empty)
        cmdDef.resourceFolder = resourceFolder
        
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
                    if control:  # Ensure control was created successfully
                        control.isPromoted = IS_PROMOTED
                    else:
                        ui.messageBox(f"Failed to add control to panel: {PANEL_ID}")
            else:
                ui.messageBox(f"Panel not found: {PANEL_ID}")
        else:
            ui.messageBox(f"Workspace not found: {WORKSPACE_ID}")
        
        if config.DEBUG:
            print(f'Aluminum Extrusion command created in CREATE panel.')
            
    except Exception as e:
        if ui:
            ui.messageBox(f'Failed to start: {str(e)}\n\n{traceback.format_exc()}')


def stop():
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
            
        # Clear the handlers
        handlers.clear()
            
    except Exception as e:
        if ui:
            ui.messageBox(f'Failed to clean up: {str(e)}')