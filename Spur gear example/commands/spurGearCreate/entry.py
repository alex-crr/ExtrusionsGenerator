import adsk.core
import os
from ...lib import fusionAddInUtils as futil
from ... import config
from . import logic

app = adsk.core.Application.get()
ui = app.userInterface

spur_gear_logic: logic.SpurGearLogic = None

# Specify the command identity information.
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_spurGearCreate'
CMD_NAME = 'Spur Gear'
CMD_Description = ('Sample command that demonstrates adding a button for a custom command ' 
                   'to the user interface and creating a command with a dialog to interact '
                   'with the user. It also demonstrates using the API to create sketches '
                   'and features to build a spur gear model based on the user input.')

# Specify that the command will be promoted to the panel.
IS_PROMOTED = False

# Defines the location of the command to be in the DESIGN workspace and 
# in the CREATE panel below the Pipe command. See the user manual topic
# on "User Interface Customization" for details on how to get these ID's.
# https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/UserInterface_UM.htm
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'PrimitivePipe'

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when the add-in is loaded. The button to execute the command
# is created and the event handler to handle when the command is run is connected.
def start():
    # General logging for debug.
    futil.log(f'{CMD_NAME} started')

    # ******** Create the Command Definition ********
    # Delete the existing command, in case it wasn't correctly deleted during a failed execution.
    cmdDef = ui.commandDefinitions.itemById(CMD_ID)
    if cmdDef:
        cmdDef.deleteMe()

    # Define the folder that contains the icon files. In this case it is a subfolder named "resources".
    icon_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'SpurGear')

    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, icon_folder)

    # Add the additional information for an extended tooltip.
    imageFilename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'toolClip.png')
    cmd_def.toolClipFilename = imageFilename

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # General logging for debug.
    futil.log(f'{CMD_NAME} stopped')

    # Gets the toolbar panel containing the button.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Delete the button command control.
    cntrl = panel.controls.itemById(CMD_ID)
    if cntrl:
        cntrl.deleteMe()

    # Delete the command definition.
    cmdDef = ui.commandDefinitions.itemById(CMD_ID)
    if cmdDef:
        cmdDef.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # TODO Define the dialog for your command by adding different inputs to the command.
    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    futil.log(f'{CMD_NAME} Command Created Event')

    # Setup the event handlers needed for this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_inputs, local_handlers=local_handlers)

    des: adsk.fusion.Design = app.activeProduct
    if des is None:
        return

    # Create an instance of the Spur Gear command class.
    global spur_gear_logic
    spur_gear_logic = logic.SpurGearLogic(des)

    cmd = args.command
    cmd.isExecutedWhenPreEmpted = False

    # Define the dialog by creating the command inputs.
    spur_gear_logic.CreateCommandInputs(cmd.commandInputs)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    spur_gear_logic.HandleExecute(args)


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {args.input.id}')

    spur_gear_logic.HandleInputsChanged(args)


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_inputs(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Validate Inputs Event fired.')

    spur_gear_logic.HandleValidateInputs(args)


# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []