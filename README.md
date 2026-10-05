# Aluminium Extrusions

Fusion add-in that inserts a 20-series aluminium extrusion as a new component, extruded to the length you enter.

## Usage

1. In the **Design** workspace, open **SOLID > CREATE** and click **Aluminum Extrusion** (next to Pipe).
2. Pick the **Profile**: 2020, 2040, 2060, 2080, 4040 or C-beam 4080 (all 20 mm slot series).
3. Enter the **Length** in mm and click **OK**.

The add-in creates a component named `<series>_<profile>_<length mm>`, imports the profile sketch, extrudes it, assigns the Fusion "Aluminum" material, and groups the steps in the timeline.

## Limits

- Only the 2020 series ships. 3030 and 4040-series profiles are in progress on the `dev` branch.
- Profiles are nominal-geometry DXFs. Check them against your supplier's drawing for tight-fit work.

## Install from source

Copy this folder into Fusion's `API/AddIns` directory, then run **Extrusions** from **UTILITIES > Add-Ins**.

## Support

Open an issue at https://github.com/alex-crr/ExtrusionsGenerator/issues.
