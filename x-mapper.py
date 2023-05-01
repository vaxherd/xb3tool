#!/usr/bin/python3
#
# Generate a minimap image for a Xenoblade 3 map, showing the locations of
# selected items or enemies.
#
# Requires PIL (the Python Imaging Library).
#
# Public domain, share and enjoy.
#

import argparse
import glob
import os
import re
import struct
import sys

import PIL.Image

import bdat
import genmap


########################################################################
# Generic feature icon generator

def make_feature_icon(r, g, b):
    """Create a generic feature icon (colored dot) with the given color.

    Parameters:
        r, g, b: Color components for dot interior (each 0-255).
    """
    colormap = {'.': [0,0,0,0],
                'O': [0,0,0,255],
                'i': [r,g,b,255]}
    pattern = ('...OOOOO...',
               '..OiiiiiO..',
               '.OiiiiiiiO.',
               'OiiiiiiiiiO',
               'OiiiiiiiiiO',
               'OiiiiiiiiiO',
               'OiiiiiiiiiO',
               'OiiiiiiiiiO',
               '.OiiiiiiiO.',
               '..OiiiiiO..',
               '...OOOOO...')
    width = len(pattern[0])
    height = len(pattern)
    pixels = tuple(colormap[pixel] for pixel in ''.join(pattern))
    data = b''.join(struct.pack('BBBB',*pixel) for pixel in pixels)
    return PIL.Image.frombytes('RGBA', (width,height), data)


########################################################################
# Feature lookup routines

def item_locs(item, map_id, tables, verbose=False):
    """Return a list of all locations of the given item on the given map.

    Parameters:
        item: Numeric item ID.
        map_id: Map ID ("ma01a", etc.)
        tables: List of BDAT tables from the game data.
        verbose: True for verbose output.

    Return value:
        List of 3-tuples (x,y,z) containing the world coordinates of each
        instance of the item.
    """
    locs = []

    gmkloc = tables.get('SYS_GimmickLocation_dlc04')
    if not gmkloc:
        gmkloc = tables['SYS_GimmickLocation']
    field_gmk_type = gmkloc.field_index('GimmickType')
    gmk_type_grave = '<29C1467D>'  # murmur32('Grave')
    field_gmk_id = gmkloc.field_index('GimmickID')
    field_gmk_data = gmkloc.field_index('field_6C50B44E')
    field_gmk_x = gmkloc.field_index('X')
    field_gmk_y = gmkloc.field_index('Y')
    field_gmk_z = gmkloc.field_index('Z')

    flden = tables['FLD_EnemyData']
    field_flden_droptable = flden.field_index('field_C6717CFE')
    field_flden_dropkey = flden.field_index('IdDropPrecious')

    droptbl = tables['152F4D70']
    field_droptbl_appoint = droptbl.field_index('field_791E2B72')

    appoint = tables['BTL_EnemyDrop_Appoint']
    field_appoint_item = [appoint.field_index(f'ItemID{i+1}') for i in range(8)]

    reward = tables['ITM_RewardAssort']
    field_reward_item = [reward.field_index(f'Reward{i+1}') for i in range(20)]

    table = tables.get(f'{map_id}_GMK_Collection')
    if table:
        ids = []
        field_id = table.field_index('ID')
        field_items = [table.field_index(f'ItemId{i+1}') for i in range(10)]
        for row in range(table.num_rows):
            if item in (table.get(row, field) for field in field_items):
                ids.append(table.get(row, field_id))
        for row in range(gmkloc.num_rows):
            if gmkloc.get(row, field_gmk_data) in ids:
                x = gmkloc.get(row, field_gmk_x)
                y = gmkloc.get(row, field_gmk_y)
                z = gmkloc.get(row, field_gmk_z)
                if verbose:
                    print(f'{item}: [collection {gmkloc.get(row, field_gmk_data)} gimmick {gmkloc.get(row, field_gmk_id)}] {x}, {y}, {z}')
                locs.append((x, y, z))
    # end if

    table = tables.get(f'{map_id}_GMK_EnemyPop')
    if table:
        ids = []
        field_id = table.field_index('ID')
        field_enemies = [table.field_index(f'EnemyID{i+1}') for i in range(6)]
        for row in range(table.num_rows):
            for flden_id in (table.get(row, field) for field in field_enemies):
                if flden_id == 0:
                    continue
                found = False
                flden_row = flden.id_to_row(flden_id)
                if flden.get(flden_row, field_flden_dropkey) == item:
                    found = True
                else:
                    drop_id = flden.get(flden_row, field_flden_droptable)
                    drop_row = droptbl.id_to_row(drop_id)
                    appoint_id = droptbl.get(drop_row, field_droptbl_appoint)
                    if appoint_id:
                        appoint_row = appoint.id_to_row(appoint_id)
                        found = item in (appoint.get(appoint_row, field)
                                         for field in field_appoint_item)
                if found:
                    gmk_id = table.get(row, field_id)
                    for gmk_row in range(gmkloc.num_rows):
                        if gmkloc.get(gmk_row, field_gmk_data) == gmk_id and gmkloc.get(gmk_row, field_gmk_type) != gmk_type_grave:
                            x = gmkloc.get(gmk_row, field_gmk_x)
                            y = gmkloc.get(gmk_row, field_gmk_y)
                            z = gmkloc.get(gmk_row, field_gmk_z)
                            if verbose:
                                print(f'{item}: [enemy-pop {gmk_id}] {x}, {y}, {z}')
                            locs.append((x, y, z))
    # end if

    table = tables.get(f'{map_id}_GMK_Precious')
    if table:
        field_id = table.field_index('ID')
        field_item = table.field_index('ItemID')
        for row in range(table.num_rows):
            if table.get(row, field_item) == item:
                gmk_row = gmkloc.id_to_row(table.get(row, field_id),
                                           field_gmk_id)
                if gmk_row is None:
                    if verbose:
                        print(f'{item}: [gimmick {table.get(row, field_id)}] not found')
                else:
                    x = gmkloc.get(gmk_row, field_gmk_x)
                    y = gmkloc.get(gmk_row, field_gmk_y)
                    z = gmkloc.get(gmk_row, field_gmk_z)
                    if verbose:
                        print(f'{item}: [gimmick {table.get(row, field_id)}] {x}, {y}, {z}')
                    locs.append((x, y, z))
    # end if

    table = tables.get(f'{map_id}_GMK_TreasureBox')
    if table:
        field_id = table.field_index('ID')
        field_reward = table.field_index('RewardID')
        for row in range(table.num_rows):
            id = table.get(row, field_id)
            reward_id = table.get(row, field_reward)
            reward_row = reward.id_to_row(reward_id)
            if item in (reward.get(reward_row, field)
                        for field in field_reward_item):
                gmk_row = gmkloc.id_to_row(id, field_gmk_id)
                if gmk_row is None:
                    if verbose:
                        print(f'{item}: [treasure {id}] not found')
                else:
                    x = gmkloc.get(gmk_row, field_gmk_x)
                    y = gmkloc.get(gmk_row, field_gmk_y)
                    z = gmkloc.get(gmk_row, field_gmk_z)
                    if verbose:
                        print(f'{item}: [treasure {table.get(row, field_id)}] {x}, {y}, {z}')
                    locs.append((x, y, z))
    # end if

    # Special case for DLC4 (XC2 style white chests, table name unknown):
    table = tables.get('C566F8E6')
    if map_id == 'ma40a' and table:
        field_id = table.field_index('ID')
        field_reward = table.field_index('RewardID')
        for row in range(table.num_rows):
            id = table.get(row, field_id)
            reward_id = table.get(row, field_reward)
            reward_row = reward.id_to_row(reward_id)
            if item in (reward.get(reward_row, field)
                        for field in field_reward_item):
                gmk_row = gmkloc.id_to_row(id, field_gmk_id)
                if gmk_row is None:
                    if verbose:
                        print(f'{item}: [treasure2 {id}] not found')
                else:
                    x = gmkloc.get(gmk_row, field_gmk_x)
                    y = gmkloc.get(gmk_row, field_gmk_y)
                    z = gmkloc.get(gmk_row, field_gmk_z)
                    if verbose:
                        print(f'{item}: [treasure2 {table.get(row, field_id)}] {x}, {y}, {z}')
                    locs.append((x, y, z))
    # end if

    return locs


def enemy_locs(enemy, map_id, tables, verbose=False):
    """Return a list of all locations of the given enemy on the given map.

    Parameters:
        enemy: FLD_EnemyData ID for enemy.
        map_id: Map ID ("ma01a", etc.)
        tables: List of BDAT tables from the game data.
        verbose: True for verbose output.

    Return value:
        List of 3-tuples (x,y,z) containing the world coordinates of each
        instance of the enemy.
    """
    locs = []

    gmkloc = tables.get('SYS_GimmickLocation_dlc04')
    if not gmkloc:
        gmkloc = tables['SYS_GimmickLocation']
    field_gmk_type = gmkloc.field_index('GimmickType')
    gmk_type_grave = '<29C1467D>'  # murmur32('Grave')
    field_gmk_id = gmkloc.field_index('GimmickID')
    field_gmk_data = gmkloc.field_index('field_6C50B44E')
    field_gmk_x = gmkloc.field_index('X')
    field_gmk_y = gmkloc.field_index('Y')
    field_gmk_z = gmkloc.field_index('Z')

    table = tables.get(f'{map_id}_GMK_EnemyPop')
    if table:
        ids = []
        field_id = table.field_index('ID')
        field_enemies = [table.field_index(f'EnemyID{i+1}') for i in range(6)]
        for row in range(table.num_rows):
            if enemy in (table.get(row, field) for field in field_enemies):
                gmk_id = table.get(row, field_id)
                for gmk_row in range(gmkloc.num_rows):
                    if gmkloc.get(gmk_row, field_gmk_data) == gmk_id and gmkloc.get(gmk_row, field_gmk_type) != gmk_type_grave:
                        x = gmkloc.get(gmk_row, field_gmk_x)
                        y = gmkloc.get(gmk_row, field_gmk_y)
                        z = gmkloc.get(gmk_row, field_gmk_z)
                        if verbose:
                            print(f'{enemy}: [enemy-pop {gmk_id}] {x}, {y}, {z}')
                        locs.append((x, y, z))
    # end if

    return locs


########################################################################
# Program entry point

def main(argv):
    """Program entry point."""
    DEF_COLOR = '#00FF00'

    parser = argparse.ArgumentParser(
        description='Generate a Xenoblade 3 map image showing feature locations.')
    parser.add_argument('-v', '--verbose', action='count',
                        help='Output status messages during parsing.')
    parser.add_argument('-s', '--scale', type=int,
                        help=('Map scale to render (1 = highest resolution, 2 = 1/2 scale, 3 = 1/4 scale). Defaults to the highest scale (smallest image) available for the selected map and layer.'))
    parser.add_argument('-e', '--expansions', help='Expansions to use, these replace specific map portions based on story progress. Use a comma-separated list of suffixes. (Example: "-e ex,ex02,ex03" for ma07a)')
    parser.add_argument('-l', '--language', help='Set the language code to use for name lookups (default "gb" for English).')
    parser.add_argument('-E', '--enemies', metavar='ENEMIES',
                        help=('IDs (from FLD_EnemyData) or names (with internal commas omitted) of enemies to show, separated by commas.\n'
                              'Each ID/name may optionally be followed by ":#RRGGBB" to set the icon color for the enemy (default '+DEF_COLOR+').'))
    parser.add_argument('-I', '--items', metavar='ITEMS',
                        help=('IDs or names of items to show, separated by commas.\n'
                              'Each ID/name may optionally be followed by ":#RRGGBB" as for enemies.'))
    parser.add_argument('datadir', metavar='DATADIR',
                        help='Pathname of directory containing Xenoblade 3 data.')
    parser.add_argument('map_id', metavar='MAP-ID',
                        help='Map ID (such as "ma01a").')
    parser.add_argument('layer', metavar='LAYER', type=int,
                        help='Map layer index (0 = main area map).')
    parser.add_argument('output', metavar='OUTPUT',
                        help=('Pathname for output PNG file.\n'
                              'If "-", the PNG data is written to standard output.\n'
                              '(Note that -v will also write to standard output.)'))
    args = parser.parse_args()
    verbose = args.verbose if args.verbose is not None else 0
    scale = args.scale if args.scale is not None else 0
    expansions = args.expansions.split(',') if args.expansions is not None else []
    lang = args.language if args.language is not None else 'gb'

    enemies = args.enemies.split(',') if args.enemies is not None else []
    for i in range(len(enemies)):
        enemy = enemies[i]
        if ':' in enemy:
            id, color = enemy.split(':', 1)
        else:
            id = enemy
            color = ''
        if color == '':
            color = DEF_COLOR
        try:
            id = int(id)
        except ValueError:
            pass
        if not re.match(r'#[0-9A-F]{6}$', color):
            raise ValueError(f'Invalid color specification for enemy {enemy}: {color}')
        r, g, b = (int(color[1:3],16), int(color[3:5],16), int(color[5:7],16))
        enemies[i] = (id, make_feature_icon(r, g, b))

    items = args.items.split(',') if args.items is not None else []
    for i in range(len(items)):
        item = items[i]
        if ':' in item:
            id, color = item.split(':', 1)
        else:
            id = item
            color = ''
        if color == '':
            color = DEF_COLOR
        try:
            id = int(id)
        except ValueError:
            pass
        if not re.match(r'#[0-9A-F]{6}$', color):
            raise ValueError(f'Invalid color specification for item {item}: {color}')
        r, g, b = (int(color[1:3],16), int(color[3:5],16), int(color[5:7],16))
        items[i] = (id, make_feature_icon(r, g, b))

    if (not os.path.exists(os.path.join(args.datadir, 'menu'))
            or not os.path.exists(os.path.join(args.datadir, 'bdat'))):
        raise Exception(f'Xenoblade 3 data not found at {args.datadir}')

    # Assume English for translating enemy names -> IDs
    files = (glob.glob(os.path.join(args.datadir, 'bdat/*.bdat'))
             + glob.glob(os.path.join(args.datadir, f'bdat/{lang}/game/*.bdat')))
    for file in files:
        bdat.Bdat.load_debug_strings(file, verbose)
    tables = {}
    for file in files:
        bdat_file = bdat.Bdat(file, verbose)
        for table in bdat_file.tables():
            tables[table.name] = table

    for i in range(len(enemies)):
        id, icon = enemies[i]
        if isinstance(id, str):
            found = False
            flden = tables['FLD_EnemyData']
            field_flden_name = flden.field_index('MsgName')
            msg = tables['msg_enemy_name']
            field_msg_name = msg.field_index('name')
            for row in range(flden.num_rows):
                name_id = flden.get(row, field_flden_name)
                if name_id == 0:
                    continue
                name = msg.get(msg.id_to_row(name_id),
                                   field_msg_name)
                name = name.replace(',', '')
                if name == id:
                    if not found:
                        found = True
                        enemies[i] = (row+1, icon)
                    else:
                        enemies.append((row+1, icon))
            if not found:
                raise ValueError(f'Unknown enemy name: {id}')

    for i in range(len(items)):
        id, icon = items[i]
        if isinstance(id, str):
            found = False
            item_tables = ((tables[itmname], tables[msgname])
                           for itmname, msgname
                           in (('ITM_Accessory', 'msg_item_accessory'),
                               ('ITM_Collection', 'msg_item_collection'),
                               ('ITM_Info', 'CA2198EC'),
                               ('ITM_Precious', 'msg_item_precious')))
            for itm, msg in item_tables:
                field_itm_name = itm.field_index('Name')
                field_msg_name = msg.field_index('name')
                for row in range(itm.num_rows):
                    name_id = itm.get(row, field_itm_name)
                    if name_id == 0:
                        continue
                    name = msg.get(msg.id_to_row(name_id),
                                   field_msg_name)
                    name = name.replace(',', '')
                    if name == id:
                        num_id = itm.get(row, 0) # Numeric ID is always field 0
                        if not found:
                            found = True
                            items[i] = (num_id, icon)
                        else:
                            items.append((num_id, icon))
            if not found:
                raise ValueError(f'Unknown item name: {id}')

    mi = genmap.MapInfo(os.path.join(args.datadir,
                                     f'menu/minimap/{args.map_id}.mi'),
                        verbose, expansions)
    image = mi.image(args.layer, scale)

    for item, icon in items:
        for wx, wy, wz in item_locs(item, args.map_id, tables, verbose):
            x, y = mi.image_pos(args.layer, scale, wx, wy, wz)
            x = int(x+0.5) - int(icon.width/2)
            y = int(y+0.5) - int(icon.height/2)
            x = min(max(x, 0), image.width - icon.width)
            y = min(max(y, 0), image.height - icon.height)
            image.alpha_composite(icon, dest=(x,y))

    for enemy, icon in enemies:
        for wx, wy, wz in enemy_locs(enemy, args.map_id, tables, verbose):
            x, y = mi.image_pos(args.layer, scale, wx, wy, wz)
            x = int(x+0.5) - int(icon.width/2)
            y = int(y+0.5) - int(icon.height/2)
            x = min(max(x, 0), image.width - icon.width)
            y = min(max(y, 0), image.height - icon.height)
            image.alpha_composite(icon, dest=(x,y))

    image.save(sys.stdout.buffer if args.output == '-' else args.output,
               format='png')
# end def


if __name__ == '__main__':
    main(sys.argv)
