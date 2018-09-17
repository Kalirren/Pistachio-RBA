# -*- coding: utf-8 -*-
"""
Created on Sun Dec  3 18:51:46 2017

@author: Daniel Y Poon Syverson
"""

from opentrons import robot, containers, instruments

#Set robot speed
robot.head_speed(x=16000,y=16000,z=4000,a=1000,b=1000)

##Use the workaround for properly sorted custom containers
def create_container_instance(name, grid, spacing, diameter, depth,
                              volume=0, slot=None, label=None):
    from opentrons import robot
    from opentrons.containers.placeable import Container, Well
    
    if slot is None:
        raise RuntimeError('"slot" argument is required.')
    if label is None:
        label = name
    columns, rows = grid
    col_spacing, row_spacing = spacing
    custom_container = Container()
    well_properties = {
        'type': 'custom',
        'diameter': diameter,
        'height': depth,
        'total-liquid-volume': volume
    }

    for r in range(rows):
        for c in range(columns):
            well = Well(properties=well_properties)
            well_name = chr(c + ord('A')) + str(1 + r)
            coordinates = (c * col_spacing, r * row_spacing, 0)
            custom_container.add(well, well_name, coordinates)

    # if a container is added to Deck AFTER a Pipette, the Pipette's
    # Calibrator must update to include all children of Deck
    for _, instr in robot.get_instruments():
        if hasattr(instr, 'update_calibrator'):
            instr.update_calibrator()
            
    custom_container.properties['type'] = name
    custom_container.get_name = lambda: label

    # add to robot deck
    robot.deck[slot].add(custom_container, label)

    return custom_container

#Define a container for the anthrone trough

containers.create(
        'trough-15ml',
        grid = (1,1),
        spacing = (20,20),
        diameter = 30,
        depth = 30
        )

SamplesLeft = create_container_instance(
    'double-tube-rack-40-half', # aluminum tube rack for 1.7 ml microcentrifuge tubes; has 8x5 arrangement, fits in two slots
    grid = (4, 5), # 4 columns and 5 rows
    spacing = (19, 19), # 20 mm apart
    diameter = 10, # each tube 10 mm in diameter
    depth = 40, # each tube 3.5 mm deep, plus tolerance
    slot = 'C3')
SamplesRight = create_container_instance(
    'double-tube-rack-40-half', # aluminum tube rack for 1.7 ml microcentrifuge tubes; has 8x5 arrangement, fits in two slots
    grid = (4, 5), # 4 columns and 5 rows
    spacing = (19, 19), # 20 mm apart
    diameter = 10, # each tube 10 mm in diameter
    depth = 40, # each tube 3.5 mm deep, plus tolerance
    slot = 'D3')

#Setup directions to human in comments.
Tip_rack_1 = containers.load('tiprack-200ul', 'A3')
# p200 tip rack for 1-channel in slot A3
Tip_rack_8 = containers.load('tiprack-200ul', 'E1')
# p200 tip rack for 8-channel in slot E1
TrashB = containers.load('trash-box', 'A2')
# trash for 1-channel in slot A2 
TrashA = containers.load('trash-box', 'C1')
# trash for 8-channel in slot C1
Anthrone = containers.load('trough-15ml', 'E2','anthrone-trough')
#Fill trough with 13 mL anthrone reagent (0.1 % in concentrated sulfuric acid) in slot D2; you'll use 12
Assay96 = containers.load('96-PCR-flat','C2')
# place the assay plate in slot C2
Glucose = SamplesLeft.wells(7)
# place 0.25 mg/ml glucose stock in a 1.7 ml tube in slot D2 of bay C3
Water = SamplesRight.wells(7)
# place water in a 1.7 ml tube in slot D2 of bay D3

#Pipettes mounted: p200 in axis B, p200-8-channel in axis A
B = instruments.Pipette(
    name = "p200",
    trash_container = TrashB,
    tip_racks = [Tip_rack_1],
    max_volume = 200,
    min_volume = 20,
    axis="b",
    aspirate_speed=1000,
    dispense_speed=1000
)

A = instruments.Pipette(
    name = "p300-8channel",
    trash_container = TrashA,
    tip_racks= [Tip_rack_8],
    max_volume = 250, #the bottom 30 ul on this 300 ul pipette are unusable
    min_volume = 30,
    channels = 8,
    axis = "a",
    aspirate_speed=1000,
    dispense_speed=1000
    )

#Robot's procedure:
#Use p200 to make standard curve
#Use p200 to distribute 50 ul of each sample into 3 adjoining wells.
#Use p200-8channel to pipette 150 ul of anthrone into each well in which a sample has been put and mix the sample thoroughly. Blow out the tip, touch-tip, and change tips each time.

for targetwell in Assay96.cols('A'):
    A.transfer( 150, Anthrone.well(0), targetwell,
               air_gap = 25, mix_after = (10,75), new_tip = 'always')
#End protocol