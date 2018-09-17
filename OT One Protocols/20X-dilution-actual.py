# -*- coding: utf-8 -*-
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

#define trough type for water
containers.create(
        'trough-15ml',
        grid = (1,1),
        spacing = (20,20),
        diameter = 30,
        depth = 30
        )

#Setup directions to human in comments.
tiprack200 = containers.load('tiprack-200ul', 'A3') # p200 tip rack in slot A3
Tip_rack_8 = containers.load('tiprack-200ul', 'E1') # p200 tip rack for 8-channel in slot E1
TrashA = containers.load('trash-box', 'C1') # trash for 8-channel in slot C1
TrashB = containers.load('trash-box', 'A2') # trash for single in slot A2 
Water = containers.load('trough-15ml', 'E2','water-trough')
SamplesLeft = create_container_instance(
    'double-tube-rack-40-half', # aluminum tube rack for 1.7 ml microcentrifuge tubes; has 8x5 arrangement, fits in two slots
    grid = (4, 5), # 4 columns and 5 rows
    spacing = (19.5, 19.5), # 20 mm apart
    diameter = 10, # each tube 10 mm in diameter
    depth = 40, # each tube 3.5 mm deep, plus tolerance
    slot = 'C3')
SamplesRight = create_container_instance(
    'double-tube-rack-40-half', # aluminum tube rack for 1.7 ml microcentrifuge tubes; has 8x5 arrangement, fits in two slots
    grid = (4, 5), # 4 columns and 5 rows
    spacing = (19.5, 19.5), # 20 mm apart
    diameter = 10, # each tube 10 mm in diameter
    depth = 40, # each tube 3.5 mm deep, plus tolerance
    slot = 'D3')
# Put the 24 samples in 1.7 ml microcentrifuge tubes in alternating rows of a 40 rack in slots D3 and E3
dest = containers.load('96-deep-well', 'E3')
# Prepare 24 empty 1.7 ml microcentrifuge tubes in alternating rows of a 40 rack in slots D1 and E1
#Distribute 380 ul H2O into each of the 24 tubes
#Pipets mounted: p200 in axis B
B = instruments.Pipette(
    name = "p200",
    trash_container = TrashB,
    tip_racks = [tiprack200],
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

#Pipet 20 ul of each sample into the corresponding tube
B.pick_up_tip()
for (i,j) in [(0,0),(8,32),(16,64)]:
    for k in range(4):
        B.transfer(20,SamplesLeft.wells(i+k).top(-30),dest.wells(j+k), new_tip='never')
        B.transfer(20,SamplesRight.wells(i+k).top(-30),dest.wells(j+k+4), new_tip='never')

B.drop_tip()

#Do the dilution
A.pick_up_tip()
for i in ['A0','A4','A8']:
    A.transfer(380,Water.wells(0),dest.wells(i),new_tip='never')