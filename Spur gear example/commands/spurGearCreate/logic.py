import adsk.core
import adsk.fusion
import math
import os
import json
import time

app = adsk.core.Application.get()
ui = app.userInterface
skipValidate = False


class SpurGearLogic():
    def __init__(self, des: adsk.fusion.Design):
        # Read the cached values, if they exist.
        settings = None
        settingAttribute = des.attributes.itemByName('SpurGear', 'settings')
        if settingAttribute is not None:
            jsonSettings = settingAttribute.value
            settings = json.loads(jsonSettings)              

        defaultUnits = des.unitsManager.defaultLengthUnits
            
        # Determine whether to use inches or millimeters as the intial default.
        if defaultUnits == 'in' or defaultUnits == 'ft':
            self.units = 'in'
        else:
            self.units = 'mm'
        
        # Define the default for each value and then check to see if there
        # were cached settings and override the default if a setting exists.
        if self.units == 'in':
            self.standard = 'English'
        else:
            self.standard = 'Metric'
        if settings:
            self.standard = settings['Standard']
            
        if self.standard == 'English':
            self.units = 'in'
        else:
            self.units = 'mm'
        
        self.pressureAngle = '20 deg'
        if settings:
            self.pressureAngle = settings['PressureAngle']
        
        self.pressureAngleCustom = 20 * (math.pi/180.0)
        if settings:
            self.pressureAngleCustom = float(settings['PressureAngleCustom'])            

        self.diaPitch = '2'
        if settings:
            self.diaPitch = settings['DiaPitch']
        
        self.metricModule = 25.4 / float(self.diaPitch)

        self.backlash = '0'
        if settings:
            self.backlash = settings['Backlash']

        self.numTeeth = '24'            
        if settings:
            self.numTeeth = settings['NumTeeth']

        self.rootFilletRad = '0.2'
        if settings:
            self.rootFilletRad = settings['RootFilletRad']

        self.thickness = '1.0'
        if settings:
            self.thickness = settings['Thickness']
        
        self.holeDiam = '1.0'
        if settings:
            self.holeDiam = settings['HoleDiam']


    def CreateCommandInputs(self, inputs: adsk.core.CommandInputs):
        global skipValidate
        skipValidate = True

        # Create the command inputs to define the contents of the command dialog.
        imagePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'GearEnglish.png')
        self.englishImageInput = inputs.addImageCommandInput('gearImageEnglish', '', imagePath)
        self.englishImageInput.isFullWidth = True

        imagePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'GearMetric.png')
        self.metricImageInput = inputs.addImageCommandInput('gearImageMetric', '', imagePath)
        self.metricImageInput.isFullWidth = True

        self.standardDropDownInput = inputs.addDropDownCommandInput('standard', 'Standard', adsk.core.DropDownStyles.TextListDropDownStyle)
        if self.standard == "English":
            self.standardDropDownInput.listItems.add('English', True)
            self.standardDropDownInput.listItems.add('Metric', False)
            self.metricImageInput.isVisible = False
        else:
            self.standardDropDownInput.listItems.add('English', False)
            self.standardDropDownInput.listItems.add('Metric', True)
            self.englishImageInput.isVisible = False            
        
        self.pressureAngleListInput = inputs.addDropDownCommandInput('pressureAngle', 'Pressure Angle', adsk.core.DropDownStyles.TextListDropDownStyle)
        if self.pressureAngle == '14.5 deg':
            self.pressureAngleListInput.listItems.add('14.5 deg', True)
        else:
            self.pressureAngleListInput.listItems.add('14.5 deg', False)

        if self.pressureAngle == '20 deg':
            self.pressureAngleListInput.listItems.add('20 deg', True)
        else:
            self.pressureAngleListInput.listItems.add('20 deg', False)

        if self.pressureAngle == '25 deg':
            self.pressureAngleListInput.listItems.add('25 deg', True)
        else:
            self.pressureAngleListInput.listItems.add('25 deg', False)

        if self.pressureAngle == 'Custom':
            self.pressureAngleListInput.listItems.add('Custom', True)
        else:
            self.pressureAngleListInput.listItems.add('Custom', False)

        self.pressureAngleCustomValueInput = inputs.addValueInput('pressureAngleCustom', 'Custom Angle', 'deg', adsk.core.ValueInput.createByReal(self.pressureAngleCustom))
        if self.pressureAngle != 'Custom':
            self.pressureAngleCustomValueInput.isVisible = False
                    
        self.diaPitchValueInput = inputs.addValueInput('diaPitch', 'Diametral Pitch', '', adsk.core.ValueInput.createByString(self.diaPitch))   

        self.moduleValueInput = inputs.addValueInput('module', 'Module', '', adsk.core.ValueInput.createByReal(self.metricModule))   
        
        if self.standard == 'English':
            self.moduleValueInput.isVisible = False
        elif self.standard == 'Metric':
            self.diaPitchValueInput.isVisible = False
            
        self.numTeethStringInput = inputs.addStringValueInput('numTeeth', 'Number of Teeth', self.numTeeth)        

        self.backlashValueInput = inputs.addValueInput('backlash', 'Backlash', self.units, adsk.core.ValueInput.createByReal(float(self.backlash)))

        self.rootFilletRadValueInput = inputs.addValueInput('rootFilletRad', 'Root Fillet Radius', self.units, adsk.core.ValueInput.createByReal(float(self.rootFilletRad)))

        self.thicknessValueInput = inputs.addValueInput('thickness', 'Gear Thickness', self.units, adsk.core.ValueInput.createByReal(float(self.thickness)))

        self.holeDiamValueInput = inputs.addValueInput('holeDiam', 'Hole Diameter', self.units, adsk.core.ValueInput.createByReal(float(self.holeDiam)))

        self.pitchDiamTextInput = inputs.addTextBoxCommandInput('pitchDiam', 'Pitch Diameter', '', 1, True)
        
        self.errorMessageTextInput = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
        self.errorMessageTextInput.isFullWidth = True

        skipValidate = False


    def HandleInputsChanged(self, args: adsk.core.InputChangedEventArgs):
        changedInput = args.input
        
        if not skipValidate:
            if changedInput.id == 'standard':
                if self.standardDropDownInput.selectedItem.name == 'English':
                    self.metricImageInput.isVisible = False
                    self.englishImageInput.isVisible = True
                    
                    self.diaPitchValueInput.isVisible = True
                    self.moduleValueInput.isVisible = False

                    self.diaPitchValueInput.value = 25.4 / self.moduleValueInput.value
                    
                    self.units = 'in'
                elif self.standardDropDownInput.selectedItem.name == 'Metric':
                    self.metricImageInput.isVisible = True
                    self.englishImageInput.isVisible = False
                    
                    self.diaPitchValueInput.isVisible = False
                    self.moduleValueInput.isVisible = True
                
                    self.moduleValueInput.value = 25.4 / self.diaPitchValueInput.value
                    
                    self.units = 'mm'

                # Set each one to it's current value to work around an issue where
                # otherwise if the user has edited the value, the value won't update 
                # in the dialog because apparently it remembers the units when the 
                # value was edited.  Setting the value using the API resets this.
                self.backlashValueInput.value = self.backlashValueInput.value
                self.backlashValueInput.unitType = self.units
                self.rootFilletRadValueInput.value = self.rootFilletRadValueInput.value
                self.rootFilletRadValueInput.unitType = self.units
                self.thicknessValueInput.value = self.thicknessValueInput.value
                self.thicknessValueInput.unitType = self.units
                self.holeDiamValueInput.value = self.holeDiamValueInput.value
                self.holeDiamValueInput.unitType = self.units
                
            # Update the pitch diameter value.
            diaPitch = None
            if self.standardDropDownInput.selectedItem.name == 'English':
                if self.diaPitchValueInput.isValidExpression:
                    diaPitch = self.diaPitchValueInput.value
            elif self.standardDropDownInput.selectedItem.name == 'Metric':
                if self.moduleValueInput.isValidExpression:
                    diaPitch = 25.4 / self.moduleValueInput.value
            if not diaPitch == None:
                if self.numTeethStringInput.value.isdigit(): 
                    numTeeth = int(self.numTeethStringInput.value)
                    pitchDia = numTeeth/diaPitch

                    # The pitch dia has been calculated in inches, but this expects cm as the input units.
                    des = adsk.fusion.Design.cast(app.activeProduct)
                    pitchDiaText = des.unitsManager.formatInternalValue(pitchDia * 2.54, self.units, True)
                    self.pitchDiamTextInput.text = pitchDiaText
                else:
                    self.pitchDiamTextInput.text = ''                    
            else:
                self.pitchDiamTextInput.text = ''

            if changedInput.id == 'pressureAngle':
                if self.pressureAngleListInput.selectedItem.name == 'Custom':
                    self.pressureAngleCustomValueInput.isVisible = True
                else:
                    self.pressureAngleCustomValueInput.isVisible = False                    


    def HandleValidateInputs(self, args: adsk.core.ValidateInputsEventArgs):
        if not skipValidate:
            self.errorMessageTextInput.text = ''

            # Verify that at lesat 4 teeth are specified.
            if not self.numTeethStringInput.value.isdigit():
                self.errorMessageTextInput.text = 'The number of teeth must be a whole number.'
                args.areInputsValid = False
                return
            else:    
                numTeeth = int(self.numTeethStringInput.value)
            
            if numTeeth < 4:
                self.errorMessageTextInput.text = 'The number of teeth must be 4 or more.'
                args.areInputsValid = False
                return
                
            # Calculate some of the gear sizes to use in validation.
            if self.standardDropDownInput.selectedItem.name == 'English':
                if self.diaPitchValueInput.isValidExpression:
                    diaPitch = self.diaPitchValueInput.value
                else:
                    args.areInputsValid = False
                    return
            elif self.standardDropDownInput.selectedItem.name == 'Metric':
                if self.moduleValueInput.isValidExpression:
                    diaPitch = 25.4 / self.moduleValueInput.value
                else:
                    args.areInputsValid = False
                    return

            diametralPitch = diaPitch / 2.54
            pitchDia = numTeeth / diametralPitch
            
            if (diametralPitch < (20 *(math.pi/180))-0.000001):
                dedendum = 1.157 / diametralPitch
            else:
                circularPitch = math.pi / diametralPitch
                if circularPitch >= 20:
                    dedendum = 1.25 / diametralPitch
                else:
                    dedendum = (1.2 / diametralPitch) + (.002 * 2.54)                

            rootDia = pitchDia - (2 * dedendum)        
                    
            if self.pressureAngleListInput.selectedItem.name == 'Custom':
                pressureAngle = self.pressureAngleCustomValueInput.value
            else:
                if self.pressureAngleListInput.selectedItem.name == '14.5 deg':
                    pressureAngle = 14.5 * (math.pi/180)
                elif self.pressureAngleListInput.selectedItem.name == '20 deg':
                    pressureAngle = 20.0 * (math.pi/180)
                elif self.pressureAngleListInput.selectedItem.name == '25 deg':
                    pressureAngle = 25.0 * (math.pi/180)
            baseCircleDia = pitchDia * math.cos(pressureAngle)
            baseCircleCircumference = 2 * math.pi * (baseCircleDia / 2) 

            if self.holeDiamValueInput.isValidExpression:
                holeDiam = self.holeDiamValueInput.value
            else:
                args.areInputsValid = False
                return
                            
            des = adsk.fusion.Design.cast(app.activeProduct)
            if holeDiam >= (rootDia - 0.01):
                self.errorMessageTextInput.text = 'The center hole diameter is too large.  It must be less than ' + des.unitsManager.formatInternalValue(rootDia - 0.01, self.units, True)
                args.areInputsValid = False
                return

            toothThickness = baseCircleCircumference / (numTeeth * 2)
            if self.rootFilletRadValueInput.value > toothThickness * .4:
                self.errorMessageTextInput.text = 'The root fillet radius is too large.  It must be less than ' + des.unitsManager.formatInternalValue(toothThickness * .4, self.units, True)
                args.areInputsValid = False
                return


    def HandleExecute(self, args: adsk.core.CommandEventArgs):
        if self.standardDropDownInput.selectedItem.name == 'English':
            diaPitch = self.diaPitchValueInput.value            
        elif self.standardDropDownInput.selectedItem.name == 'Metric':
            diaPitch = 25.4 / self.moduleValueInput.value
        
        # Save the current values as attributes.
        settings = {'Standard': self.standardDropDownInput.selectedItem.name,
                    'PressureAngle': self.pressureAngleListInput.selectedItem.name,
                    'PressureAngleCustom': str(self.pressureAngleCustomValueInput.value),
                    'DiaPitch': str(diaPitch),
                    'NumTeeth': str(self.numTeethStringInput.value),
                    'RootFilletRad': str(self.rootFilletRadValueInput.value),
                    'Thickness': str(self.thicknessValueInput.value),
                    'HoleDiam': str(self.holeDiamValueInput.value),
                    'Backlash': str(self.backlashValueInput.value)}

        jsonSettings = json.dumps(settings)

        des = adsk.fusion.Design.cast(app.activeProduct)
        attribs = des.attributes
        attribs.add('SpurGear', 'settings', jsonSettings)

        # Get the current values.
        if self.pressureAngleListInput.selectedItem.name == 'Custom':
            pressureAngle = self.pressureAngleCustomValueInput.value
        else:
            if self.pressureAngleListInput.selectedItem.name == '14.5 deg':
                pressureAngle = 14.5 * (math.pi/180)
            elif self.pressureAngleListInput.selectedItem.name == '20 deg':
                pressureAngle = 20.0 * (math.pi/180)
            elif self.pressureAngleListInput.selectedItem.name == '25 deg':
                pressureAngle = 25.0 * (math.pi/180)

        numTeeth = int(self.numTeethStringInput.value)
        rootFilletRad = self.rootFilletRadValueInput.value
        thickness = self.thicknessValueInput.value
        holeDiam = self.holeDiamValueInput.value
        backlash = self.backlashValueInput.value

        # Create the gear.
        start = time.time()
        gearComp = drawGear(des, diaPitch, numTeeth, thickness, rootFilletRad, pressureAngle, backlash, holeDiam)
        end = time.time()
        app.log(f'Time to create spur gear: {end - start} seconds.')            

        # If the gear was created, add a description to the component.
        if gearComp:
            if self.standardDropDownInput.selectedItem.name == 'English':
                desc = 'Spur Gear; Diametrial Pitch: ' + str(diaPitch) + '; '            
            elif self.standardDropDownInput.selectedItem.name == 'Metric':
                desc = 'Spur Gear; Module: ' +  str(25.4 / diaPitch) + '; '
            
            desc += 'Num Teeth: ' + str(numTeeth) + '; '
            desc += 'Pressure Angle: ' + str(pressureAngle * (180/math.pi)) + '; '
            
            desc += 'Backlash: ' + des.unitsManager.formatInternalValue(backlash, self.units, True)
            gearComp.description = desc        


# # Verfies that a value command input has a valid expression and returns the 
# # value if it does.  Otherwise it returns False.  This works around a 
# # problem where when you get the value from a ValueCommandInput it causes the
# # current expression to be evaluated and updates the display.  Some new functionality
# # is being added in the future to the ValueCommandInput object that will make 
# # this easier and should make this function obsolete.
# def getCommandInputValue(commandInput, unitType):
#     valCommandInput = adsk.core.ValueCommandInput.cast(commandInput)
#     if not valCommandInput:
#         return (False, 0)

#     # Verify that the expression is valid.
#     des = adsk.fusion.Design.cast(app.activeProduct)
#     unitsMgr = des.unitsManager
    
#     if unitsMgr.isValidExpression(valCommandInput.expression, unitType):
#         value = unitsMgr.evaluateExpression(valCommandInput.expression, unitType)
#         return (True, value)
#     else:
#         return (False, 0)


# Calculate points along an involute curve.
def involutePoint(baseCircleRadius, distFromCenterToInvolutePoint):
    # Calculate the other side of the right-angle triangle defined by the base circle and the current distance radius.
    # This is also the length of the involute chord as it comes off of the base circle.
    triangleSide = math.sqrt(math.pow(distFromCenterToInvolutePoint,2) - math.pow(baseCircleRadius,2)) 
    
    # Calculate the angle of the involute.
    alpha = triangleSide / baseCircleRadius

    # Calculate the angle where the current involute point is.
    theta = alpha - math.acos(baseCircleRadius / distFromCenterToInvolutePoint)

    # Calculate the coordinates of the involute point.    
    x = distFromCenterToInvolutePoint * math.cos(theta)
    y = distFromCenterToInvolutePoint * math.sin(theta)

    # Create a point to return.        
    return adsk.core.Point3D.create(x, y, 0)


# Builds a spur gear.
def drawGear(design, diametralPitch, numTeeth, thickness, rootFilletRad, pressureAngle, backlash, holeDiam):
    try:
        # The diametral pitch is specified in inches but everthing
        # here expects all distances to be in centimeters, so convert
        # for the gear creation.
        diametralPitch = diametralPitch / 2.54
    
        # Compute the various values for a gear.
        pitchDia = numTeeth / diametralPitch
        
        #addendum = 1.0 / diametralPitch
        if (diametralPitch < (20 *(math.pi/180))-0.000001):
            dedendum = 1.157 / diametralPitch
        else:
            circularPitch = math.pi / diametralPitch
            if circularPitch >= 20:
                dedendum = 1.25 / diametralPitch
            else:
                dedendum = (1.2 / diametralPitch) + (.002 * 2.54)                

        rootDia = pitchDia - (2 * dedendum)
        
        baseCircleDia = pitchDia * math.cos(pressureAngle)
        outsideDia = (numTeeth + 2) / diametralPitch
        
        # Create a new component by creating an occurrence.
        occs = design.rootComponent.occurrences
        mat = adsk.core.Matrix3D.create()
        newOcc = occs.addNewComponent(mat)        
        newComp = adsk.fusion.Component.cast(newOcc.component)
        
        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        baseSketch = sketches.add(xyPlane)

        # Draw a circle for the base.
        baseSketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0,0,0), rootDia/2.0)
        
        # Draw a circle for the center hole, if the value is greater than 0.
        prof = adsk.fusion.Profile.cast(None)
        if holeDiam - (app.pointTolerance * 2) > 0:
            baseSketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0,0,0), holeDiam/2.0)

            # Find the profile that uses both circles.
            for prof in baseSketch.profiles:
                if prof.profileLoops.count == 2:
                    break
        else:
            # Use the single profile.
            prof = baseSketch.profiles.item(0)
        
        #### Extrude the circle to create the base of the gear.

        # Create an extrusion input to be able to define the input needed for an extrusion
        # while specifying the profile and that a new component is to be created
        extrudes = newComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        # Define that the extent is a distance extent of 5 cm.
        distance = adsk.core.ValueInput.createByReal(thickness)
        extInput.setDistanceExtent(False, distance)

        # Create the extrusion.
        baseExtrude = extrudes.add(extInput)
        
        # Create a second sketch for the tooth.
        toothSketch = sketches.add(xyPlane)

        # Calculate points along the involute curve.
        involutePointCount = 15 
        involuteIntersectionRadius = baseCircleDia / 2.0
        involutePoints = []
        involuteSize = (outsideDia - baseCircleDia) / 2.0
        for i in range(0, involutePointCount):
            involuteIntersectionRadius = (baseCircleDia / 2.0) + ((involuteSize / (involutePointCount - 1)) * i)
            newPoint = involutePoint(baseCircleDia / 2.0, involuteIntersectionRadius)
            involutePoints.append(newPoint)
            
        # Get the point along the tooth that's at the pitch diameter and then
        # calculate the angle to that point.
        pitchInvolutePoint = involutePoint(baseCircleDia / 2.0, pitchDia / 2.0)
        pitchPointAngle = math.atan(pitchInvolutePoint.y / pitchInvolutePoint.x)

        # Determine the angle defined by the tooth thickness as measured at
        # the pitch diameter circle.
        toothThicknessAngle = (2 * math.pi) / (2 * numTeeth)
        
        # Determine the angle needed for the specified backlash.
        backlashAngle = (backlash / (pitchDia / 2.0)) * .25
        
        # Determine the angle to rotate the curve.
        rotateAngle = -((toothThicknessAngle/2) + pitchPointAngle - backlashAngle)
        
        # Rotate the involute so the middle of the tooth lies on the x axis.
        cosAngle = math.cos(rotateAngle)
        sinAngle = math.sin(rotateAngle)
        for i in range(0, involutePointCount):
            newX = involutePoints[i].x * cosAngle - involutePoints[i].y * sinAngle
            newY = involutePoints[i].x * sinAngle + involutePoints[i].y * cosAngle
            involutePoints[i] = adsk.core.Point3D.create(newX, newY, 0)

        # Create a new set of points with a negated y.  This effectively mirrors the original
        # points about the X axis.
        involute2Points = []
        for i in range(0, involutePointCount):
            involute2Points.append(adsk.core.Point3D.create(involutePoints[i].x, -involutePoints[i].y, 0))

        # Calculate the angle of each involute point relative to the X axis.
        curve1Angle = []
        curve2Angle = []
        for i in range(0, involutePointCount):
            curve1Angle.append(math.atan(involutePoints[i].y / involutePoints[i].x))
            curve2Angle.append(math.atan(involute2Points[i].y / involute2Points[i].x))      

        toothSketch.isComputeDeferred = True
		
        # Create and load an object collection with the points.
        pointSet = adsk.core.ObjectCollection.create()
        for i in range(0, involutePointCount):
            pointSet.add(involutePoints[i])

        # Create the first spline.
        spline1 = toothSketch.sketchCurves.sketchFittedSplines.add(pointSet)

        # Add the involute points for the second spline to an ObjectCollection.
        pointSet = adsk.core.ObjectCollection.create()
        for i in range(0, involutePointCount):
            pointSet.add(involute2Points[i])

        # Create the second spline.
        spline2 = toothSketch.sketchCurves.sketchFittedSplines.add(pointSet)

        # Draw the arc for the top of the tooth.
        midPoint = adsk.core.Point3D.create((outsideDia / 2), 0, 0)
        toothSketch.sketchCurves.sketchArcs.addByThreePoints(spline1.endSketchPoint, midPoint, spline2.endSketchPoint)     

        # Check to see if involute goes down to the root or not.  If not, then
        # create lines to connect the involute to the root.
        if( baseCircleDia < rootDia ):
            toothSketch.sketchCurves.sketchLines.addByTwoPoints(spline2.startSketchPoint, spline1.startSketchPoint)
        else:
            rootPoint1 = adsk.core.Point3D.create((rootDia / 2 - 0.001) * math.cos(curve1Angle[0] ), (rootDia / 2) * math.sin(curve1Angle[0]), 0)
            line1 = toothSketch.sketchCurves.sketchLines.addByTwoPoints(rootPoint1, spline1.startSketchPoint)

            rootPoint2 = adsk.core.Point3D.create((rootDia / 2 - 0.001) * math.cos(curve2Angle[0]), (rootDia / 2) * math.sin(curve2Angle[0]), 0)
            line2 = toothSketch.sketchCurves.sketchLines.addByTwoPoints(rootPoint2, spline2.startSketchPoint)

            baseLine = toothSketch.sketchCurves.sketchLines.addByTwoPoints(line1.startSketchPoint, line2.startSketchPoint)

            # Make the lines tangent to the spline so the root fillet will behave correctly.            
            line1.isFixed = True
            line2.isFixed = True
            toothSketch.geometricConstraints.addTangent(spline1, line1)
            toothSketch.geometricConstraints.addTangent(spline2, line2)
        
        toothSketch.isComputeDeferred = False

        ### Extrude the tooth.
        
        # Get the profile defined by the tooth.
        prof = toothSketch.profiles.item(0)

        # Create an extrusion input to be able to define the input needed for an extrusion
        # while specifying the profile and that a new component is to be created
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.JoinFeatureOperation)

        # Define that the extent is a distance extent of 5 cm.
        distance = adsk.core.ValueInput.createByReal(thickness)
        extInput.setDistanceExtent(False, distance)

        # Create the extrusion.
        toothExtrude = extrudes.add(extInput)

        # Get the side faces created by the extrude and save their entity tokens.
        tokens = []
        for sideFace in toothExtrude.sideFaces:
            tokens.append(sideFace.entityToken)

        baseFillet = None
        if rootFilletRad > 0:
            ### Find the edges between the base cylinder and the tooth.
            
            # Get the outer cylindrical face from the base extrusion by checking the number
            # of edges and if it's 2 get the other one.
            cylFace = baseExtrude.sideFaces.item(0)
            if cylFace.edges.count == 2:
                cylFace = baseExtrude.sideFaces.item(1)
    
            # Get the two linear edges, which are the connection between the cylinder and tooth.
            edges = adsk.core.ObjectCollection.create()
            for edge in cylFace.edges:
                if isinstance(edge.geometry, adsk.core.Line3D):
                    edges.add(edge)
    
            # Create a fillet input to be able to define the input needed for a fillet.
            fillets = newComp.features.filletFeatures
            filletInput = fillets.createInput()
    
            # Define that the edges and radius of the fillet.
            radius = adsk.core.ValueInput.createByReal(rootFilletRad)
            filletInput.addConstantRadiusEdgeSet(edges, radius, False)
    
            # Create the fillet.
            baseFillet = fillets.add(filletInput)

        # Create a pattern of the tooth extrude and the base fillet.
        circularPatterns = newComp.features.circularPatternFeatures
        entities = adsk.core.ObjectCollection.create()
        entities.add(toothExtrude)
        entities.add(baseFillet)

        cylFace = baseExtrude.sideFaces.item(0)        
        patternInput = circularPatterns.createInput(entities, cylFace)
        numTeethInput = adsk.core.ValueInput.createByString(str(numTeeth))
        patternInput.quantity = numTeethInput
        patternInput.patternComputeOption = adsk.fusion.PatternComputeOptions.IdenticalPatternCompute
        pattern = circularPatterns.add(patternInput)        
        
        # Create an extra sketch that contains a circle of the diametral pitch.
        diametralPitchSketch = sketches.add(xyPlane)
        diametralPitchCircle = diametralPitchSketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0,0,0), pitchDia/2.0)
        diametralPitchCircle.isConstruction = True
        diametralPitchCircle.isFixed = True
        
        # Group everything used to create the gear in the timeline.
        timelineGroups = design.timeline.timelineGroups
        newOccIndex = newOcc.timelineObject.index
        pitchSketchIndex = diametralPitchSketch.timelineObject.index
        timelineGroup = timelineGroups.add(newOccIndex, pitchSketchIndex)
        timelineGroup.name = 'Spur Gear'
        
        # Add an attribute to the component with all of the input values.  This might 
        # be used in the future to be able to edit the gear.     
        gearValues = {}
        gearValues['diametralPitch'] = str(diametralPitch * 2.54)
        gearValues['numTeeth'] = str(numTeeth)
        gearValues['thickness'] = str(thickness)
        gearValues['rootFilletRad'] = str(rootFilletRad)
        gearValues['pressureAngle'] = str(pressureAngle)
        gearValues['holeDiam'] = str(holeDiam)
        gearValues['backlash'] = str(backlash)
        attrib = newComp.attributes.add('SpurGear', 'Values', str(gearValues))
        
        newComp.name = 'Spur Gear (' + str(numTeeth) + ' teeth)'
        return newComp
    except Exception as error:
        ui.messageBox("drawGear Failed : " + str(error)) 
        return None