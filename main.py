import curses
import json
import os
import sys

# Define chests by wall
chests = {
    "A": [f"A{str(i).zfill(2)}" for i in range(1, 36)],
    "B": [f"B{str(i).zfill(2)}" for i in range(1, 36)],
    "C": [f"C{str(i).zfill(2)}" for i in range(1, 36)],
    "D": [f"D{str(i).zfill(2)}" for i in range(1, 31)],
}

# Category definitions for each wall and chest range
categories = {
    "A": [
        ("A01–A05", "Stone"),
        ("A06–A10", "Deepslate & Variants"),
        ("A11–A12", "Granite/Diorite/Andesite"),
        ("A13–A14", "Dirt & Grass"),
        ("A15", "Gravel & Sand"),
        ("A16", "Clay & Mud"),
        ("A17–A18", "Logs"),
        ("A19–A20", "Planks & Leaves"),
        ("A21", "Nether Stone"),
        ("A22", "Soul Materials"),
        ("A23", "Nether Deco"),
        ("A24", "End Blocks"),
        ("A25", "Obsidian & Crying"),
        ("A26", "Glass"),
        ("A27", "Ice & Snow"),
        ("A28", "Terracotta & Glazed"),
        ("A29", "Sandstone & Red Sandstone"),
        ("A30", "Misc Raw Blocks"),
        ("A31–A35", "Overflow Blocks")
    ],
    "B": [
        ("B01", "Coal"),
        ("B02–B04", "Ores & Ingots"),
        ("B05", "Rare Ores"),
        ("B06", "Pickaxes"),
        ("B07", "Axes & Shovels"),
        ("B08", "Hoes & Shears"),
        ("B09–B10", "Weapons"),
        ("B11", "Iron Armour"),
        ("B12", "Diamond/Neth Armour"),
        ("B13", "Enchanted Gear"),
        ("B14", "Flint/Obsidian Gear"),
        ("B15", "Buckets & Lava"),
        ("B16", "Compass/Clocks"),
        ("B17–B18", "Redstone Base"),
        ("B19–B20", "Redstone Logic"),
        ("B21", "Redstone Motion"),
        ("B22", "Redstone Storage"),
        ("B23", "Crafting Items"),
        ("B24", "Building – Stairs etc."),
        ("B25", "Fences & Gates"),
        ("B26–B27", "Scaffolding/Rails"),
        ("B28", "Signs & Frames"),
        ("B29–B30", "Lighting"),
        ("B31–B35", "Overflow Gear")
    ],
    "C": [
        ("C01–C02", "Crops"),
        ("C03", "Nether Wart"),
        ("C04", "Berries & Kelp"),
        ("C05", "Sugarcane/Cactus"),
        ("C06", "Flowers & Dye Mats"),
        ("C07", "Leather/Feathers"),
        ("C08", "Eggs & Wool"),
        ("C09", "Cooked Meat"),
        ("C10", "Uncooked Meat"),
        ("C11", "Golden Food"),
        ("C12", "Stews & Bread"),
        ("C13–C15", "Bones & String"),
        ("C16–C17", "Gunpowder & Pearls"),
        ("C18", "Slime & Magma"),
        ("C19", "Wither/Blaze Drops"),
        ("C20", "Ghast/Phantom/Shulker"),
        ("C21–C22", "Fishing Loot"),
        ("C23–C24", "Honey Products"),
        ("C25", "Misc Drops"),
        ("C26–C30", "Brewing Items"),
        ("C31–C35", "Potions")
    ],
    "D": [
        ("D01–D02", "Elytra & Shells"),
        ("D03–D04", "Totems & Shards"),
        ("D05–D06", "Enchanted Books"),
        ("D07–D08", "Name Tags & Maps"),
        ("D09–D10", "Music Discs"),
        ("D11–D12", "Recovery Tools"),
        ("D13", "Paintings & Banners"),
        ("D14–D15", "Wool & Concrete"),
        ("D16", "Glazed Terracotta"),
        ("D17–D18", "Rare Blocks"),
        ("D19–D20", "Quartz & Coral"),
        ("D21", "Beds & Mob Heads"),
        ("D22", "Armor Stands"),
        ("D23–D25", "Decoration Items"),
        ("D26–D30", "Overflow / Unsorted")
    ]
}

SAVE_FILE = "storage_data.json"

def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            return json.load(f)
    return {cid: "" for wall in chests.values() for cid in wall}

def save_data(data):
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_category_for_chest(chest_id):
    """Get the category description for a given chest ID."""
    wall = chest_id[0]
    if wall not in categories:
        return "Unknown"
    
    for range_str, category in categories[wall]:
        # Parse range (e.g., "A01–A05" or "A26")
        if "–" in range_str:
            start, end = range_str.split("–")
            start_num = int(start[1:])
            end_num = int(end[1:])
            chest_num = int(chest_id[1:])
            if start_num <= chest_num <= end_num:
                return category
        else:
            if range_str == chest_id:
                return category
    return "Unknown"

def search_chests(data, query):
    """Search for chests containing the query string."""
    results = []
    query_lower = query.lower()
    for chest_id, chest_data in data.items():
        # Handle different data formats
        if isinstance(chest_data, str):
            # Old string format
            if query_lower in chest_data.lower() or query_lower in chest_id.lower():
                results.append((chest_id, chest_data))
        elif isinstance(chest_data, dict):
            # New slot format - search through item names
            found_items = []
            for value in chest_data.values():
                if isinstance(value, list) and len(value) >= 2:
                    item_name = value[0]
                    if item_name and query_lower in item_name.lower():
                        found_items.append(item_name)
                elif isinstance(value, tuple) and len(value) >= 2:
                    item_name = value[0]
                    if item_name and query_lower in item_name.lower():
                        found_items.append(item_name)
            
            # If we found matching items or chest ID matches, add to results
            if found_items or query_lower in chest_id.lower():
                if found_items:
                    # Show first few matching items
                    item_summary = ", ".join(found_items[:3])
                    if len(found_items) > 3:
                        item_summary += f" (+{len(found_items)-3} more)"
                    results.append((chest_id, item_summary))
                else:
                    # Just chest ID matched
                    total_quantity = sum(v[1] for v in chest_data.values() if isinstance(v, (list, tuple)) and len(v) >= 2)
                    results.append((chest_id, f"{total_quantity} items"))
    return sorted(results)

def parse_command(command, data):
    """Parse and execute commands for quick chest updates.
    
    Syntax:
    UPD:WALL:CHEST:SLOT:(ItemName, Qty) - Update slot with item
    REM:WALL:CHEST:SLOT - Remove item from slot
    ~:WALL:CHEST:SLOT:(ItemName, Qty) - Short update
    -:WALL:CHEST:SLOT - Short remove
    
    Examples:
    UPD:B:01:5:(Diamond, 64)
    REM:B:01:5
    ~:B:01:5:(Iron Ingot, 32)
    -:B:01:5
    """
    try:
        command = command.strip()
        if not command:
            return "Empty command"
            
        # Split by colon
        parts = command.split(':')
        
        if len(parts) < 4:
            return "Invalid command format. Use: UPD:WALL:CHEST:SLOT:(Item,Qty) or REM:WALL:CHEST:SLOT"
        
        cmd_type = parts[0].upper()
        wall = parts[1].upper()
        chest_num = parts[2].zfill(2)  # Pad with zero if needed
        slot_str = parts[3]
        
        # Validate wall
        if wall not in ['A', 'B', 'C', 'D']:
            return f"Invalid wall '{wall}'. Use A, B, C, or D"
        
        # Validate chest number
        try:
            chest_int = int(chest_num)
            if wall == 'D' and (chest_int < 1 or chest_int > 30):
                return f"Invalid chest number for wall D. Use 01-30"
            elif wall != 'D' and (chest_int < 1 or chest_int > 35):
                return f"Invalid chest number for wall {wall}. Use 01-35"
        except ValueError:
            return f"Invalid chest number '{chest_num}'"
        
        chest_id = f"{wall}{chest_num}"
        
        # Validate slot
        try:
            slot = int(slot_str)
            if slot < 0 or slot > 53:
                return "Invalid slot number. Use 0-53"
        except ValueError:
            return f"Invalid slot number '{slot_str}'"
        
        # Handle command types
        if cmd_type in ['UPD', '~']:
            # Update command - need item data
            if len(parts) < 5:
                return "Update command needs item data: UPD:WALL:CHEST:SLOT:(ItemName,Qty)"
            
            item_data = ':'.join(parts[4:])  # Join remaining parts
            
            # Parse item data: (ItemName, Qty)
            if not item_data.startswith('(') or not item_data.endswith(')'):
                return "Item data must be in format: (ItemName, Qty)"
            
            item_content = item_data[1:-1]  # Remove parentheses
            item_parts = [p.strip() for p in item_content.split(',')]
            
            if len(item_parts) != 2:
                return "Item data must be: (ItemName, Qty)"
            
            item_name = item_parts[0].strip()
            try:
                qty = int(item_parts[1].strip())
                if qty < 1:
                    return "Quantity must be positive"
            except ValueError:
                return f"Invalid quantity '{item_parts[1]}'"
            
            # Initialize chest data if needed
            if chest_id not in data:
                data[chest_id] = {}
            elif isinstance(data[chest_id], str):
                data[chest_id] = {}
            
            # Add/update the item
            data[chest_id][str(slot)] = [item_name, qty]
            
            return f"Updated {chest_id} slot {slot}: {item_name} x{qty}"
            
        elif cmd_type in ['REM', '-']:
            # Remove command
            if chest_id not in data or not isinstance(data[chest_id], dict):
                return f"Chest {chest_id} has no items to remove"
            
            slot_key = str(slot)
            if slot_key not in data[chest_id]:
                return f"Slot {slot} in {chest_id} is already empty"
            
            # Remove the item
            item_info = data[chest_id][slot_key]
            del data[chest_id][slot_key]
            
            if isinstance(item_info, list) and len(item_info) >= 2:
                return f"Removed from {chest_id} slot {slot}: {item_info[0]} x{item_info[1]}"
            else:
                return f"Removed item from {chest_id} slot {slot}"
        
        else:
            return f"Unknown command '{cmd_type}'. Use UPD/~ for update or REM/- for remove"
            
    except Exception as e:
        return f"Command error: {str(e)}"

def show_command_help():
    """Return help text for commands."""
    return [
        "Command Syntax:",
        "  UPD:WALL:CHEST:SLOT:(ItemName, Qty) - Update slot",
        "  REM:WALL:CHEST:SLOT - Remove from slot",
        "  ~:WALL:CHEST:SLOT:(ItemName, Qty) - Short update",
        "  -:WALL:CHEST:SLOT - Short remove",
        "",
        "Examples:",
        "  UPD:B:01:5:(Diamond, 64)",
        "  ~:B:01:5:(Iron Ingot, 32)", 
        "  REM:B:01:5",
        "  -:B:01:5",
        "",
        "WALL: A, B, C, D",
        "CHEST: 01-35 (01-30 for D)",
        "SLOT: 0-53"
    ]

def edit_item_in_slot(stdscr, chest_id, slot_data):
    """TUI for managing items within a double chest (54 slots)."""
    selected_slot = 0
    
    while True:
        stdscr.clear()
        
        # Header
        stdscr.addstr(0, 2, f"Double Chest {chest_id} - Item Management", curses.A_BOLD)
        
        # Display slots in a 9x6 grid (54 slots total)
        for row in range(6):
            for col in range(9):
                slot_idx = row * 9 + col
                item, qty = slot_data.get(slot_idx, ("", 0))
                
                # Create abbreviated display (3 chars + quantity)
                if item:
                    abbrev = item[:3].upper()
                    display = f"{abbrev}:{qty:2d}"
                else:
                    display = "[----]"
                
                # Position on screen
                y_pos = row + 2
                x_pos = col * 8 + 2
                
                # Highlight selected slot
                if slot_idx == selected_slot:
                    stdscr.addstr(y_pos, x_pos, display, curses.A_REVERSE)
                else:
                    # Color filled slots differently
                    if item:
                        stdscr.addstr(y_pos, x_pos, display, curses.color_pair(1))
                    else:
                        stdscr.addstr(y_pos, x_pos, display)
        
        # Display full item info for selected slot
        if slot_data.get(selected_slot):
            full_item, full_qty = slot_data[selected_slot]
            info_text = f"Selected: {full_item} (Quantity: {full_qty})"
        else:
            info_text = f"Selected: Slot {selected_slot + 1} [Empty]"
        
        stdscr.addstr(9, 2, info_text[:curses.COLS - 4])
        
        # Instructions
        stdscr.addstr(11, 2, "Arrow Keys: Navigate  |  Enter: Edit Item  |  Del: Clear Slot  |  q: Back to Chests")
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key in [ord('q'), ord('Q')]:
            break
        elif key == curses.KEY_DOWN:
            if selected_slot < 45:  # Don't go past bottom row
                selected_slot += 9
        elif key == curses.KEY_UP:
            if selected_slot >= 9:  # Don't go past top row
                selected_slot -= 9
        elif key == curses.KEY_RIGHT:
            if selected_slot % 9 < 8:  # Don't go past right edge
                selected_slot += 1
        elif key == curses.KEY_LEFT:
            if selected_slot % 9 > 0:  # Don't go past left edge
                selected_slot -= 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            # Edit item in selected slot
            curses.echo()
            stdscr.addstr(13, 2, "Enter item name: ")
            stdscr.clrtoeol()
            try:
                item_name = stdscr.getstr(13, 19, 40).decode('utf-8')
                if item_name.strip():  # Only ask for quantity if item name provided
                    stdscr.addstr(14, 2, "Enter quantity: ")
                    stdscr.clrtoeol()
                    qty_str = stdscr.getstr(14, 18, 10).decode('utf-8')
                    qty = int(qty_str) if qty_str.isdigit() else 1
                    slot_data[selected_slot] = (item_name.strip(), qty)
                else:
                    # Empty name = clear slot
                    if selected_slot in slot_data:
                        del slot_data[selected_slot]
            except (ValueError, KeyboardInterrupt):
                pass
            curses.noecho()
        elif key in [curses.KEY_DC, ord('x'), ord('X')]:  # Delete key or 'x'
            # Clear selected slot
            if selected_slot in slot_data:
                del slot_data[selected_slot]

def chest_tui(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(0)
    
    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Filled chests
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Category headers
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Instructions
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)    # Search mode
    
    current_wall = "A"
    selected_idx = 0
    data = load_data()
    search_mode = False
    search_query = ""
    search_results = []
    view_offset = 0

    while True:
        stdscr.clear()
        
        # Header
        if search_mode:
            header = f"Search Mode: '{search_query}' ({len(search_results)} results)"
            stdscr.addstr(0, 2, header, curses.color_pair(4) | curses.A_BOLD)
        else:
            header = f"Minecraft Storage Tracker - Wall {current_wall}"
            stdscr.addstr(0, 2, header, curses.A_BOLD)
            
            # Show wall stats
            wall_chests_data = {cid: data[cid] for cid in chests[current_wall]}
            filled_chests = 0
            total_items = 0
            for chest_data in wall_chests_data.values():
                if isinstance(chest_data, dict):
                    # Sum up quantities from slot-based data (handle both string and list formats)
                    chest_total = 0
                    for value in chest_data.values():
                        if isinstance(value, list) and len(value) >= 2:
                            # Format: ["item_name", quantity]
                            item_name, qty = value[0], value[1]
                            if item_name and item_name.strip():
                                chest_total += qty
                        elif isinstance(value, tuple) and len(value) >= 2:
                            # Format: ("item_name", quantity)
                            item_name, qty = value[0], value[1]
                            if item_name and item_name.strip():
                                chest_total += qty
                    if chest_total > 0:
                        filled_chests += 1
                        total_items += chest_total
                elif isinstance(chest_data, str):
                    # Old label-based data
                    filled_chests += 1 if chest_data.strip() else 0
            total_chests = len(wall_chests_data)
            stats = f"({filled_chests}/{total_chests} chests, {total_items} items)"
            stdscr.addstr(0, len(header) + 4, stats, curses.color_pair(1))

        max_display_lines = curses.LINES - 6  # Leave space for header, categories, and instructions
        
        if search_mode:
            # Display search results
            for idx, (chest_id, label) in enumerate(search_results[view_offset:view_offset + max_display_lines]):
                display_idx = idx + view_offset
                y_pos = idx + 2
                
                category = get_category_for_chest(chest_id)
                display_label = label if label.strip() else "<empty>"
                display = f"{chest_id}: {display_label} ({category})"
                
                if len(display) > curses.COLS - 4:
                    display = display[:curses.COLS - 7] + "..."
                
                if display_idx == selected_idx:
                    stdscr.addstr(y_pos, 2, display, curses.A_REVERSE)
                else:
                    color = curses.color_pair(1) if label.strip() else 0
                    stdscr.addstr(y_pos, 2, display, color)
        else:
            # Display current wall - single column only, simple scrolling
            wall_chests_list = chests[current_wall]
            current_category = ""
            display_line = 2
            
            for idx in range(view_offset, min(view_offset + max_display_lines, len(wall_chests_list))):
                chest_id = wall_chests_list[idx]
                
                # Show category headers
                category = get_category_for_chest(chest_id)
                if category != current_category:
                    if display_line < curses.LINES - 4:
                        stdscr.addstr(display_line, 2, f"--- {category} ---", curses.color_pair(2) | curses.A_BOLD)
                        display_line += 1
                        current_category = category
                
                if display_line >= curses.LINES - 4:
                    break
                
                chest_data = data.get(chest_id, "")
                if isinstance(chest_data, dict):
                    # Sum up all quantities in the chest (handle both string and list formats)
                    total_quantity = 0
                    for value in chest_data.values():
                        if isinstance(value, list) and len(value) >= 2:
                            # Format: ["item_name", quantity]
                            item_name, qty = value[0], value[1]
                            if item_name and item_name.strip():
                                total_quantity += qty
                        elif isinstance(value, tuple) and len(value) >= 2:
                            # Format: ("item_name", quantity)
                            item_name, qty = value[0], value[1]
                            if item_name and item_name.strip():
                                total_quantity += qty
                    if total_quantity > 0:
                        display_label = f"{total_quantity} items"
                    else:
                        display_label = "<empty>"
                elif isinstance(chest_data, str):
                    display_label = chest_data if chest_data.strip() else "<empty>"
                else:
                    display_label = "<empty>"
                
                display = f"{chest_id}: {display_label}"
                
                if len(display) > curses.COLS - 4:
                    display = display[:curses.COLS - 7] + "..."
                
                if idx == selected_idx:
                    stdscr.addstr(display_line, 2, display, curses.A_REVERSE)
                else:
                    has_items = False
                    if isinstance(chest_data, dict):
                        # Check if chest has items (handle both string and list formats)
                        for value in chest_data.values():
                            if isinstance(value, list) and len(value) >= 2:
                                item_name, qty = value[0], value[1]
                                if item_name and item_name.strip():
                                    has_items = True
                                    break
                            elif isinstance(value, tuple) and len(value) >= 2:
                                item_name, qty = value[0], value[1]
                                if item_name and item_name.strip():
                                    has_items = True
                                    break
                    elif isinstance(chest_data, str):
                        has_items = chest_data.strip() != ""
                    
                    color = curses.color_pair(1) if has_items else 0
                    stdscr.addstr(display_line, 2, display, color)
                
                display_line += 1

        # Instructions
        if search_mode:
            instructions = "ESC: Exit search  |  ↑↓: Navigate  |  Enter: Edit  |  Backspace: Delete char  |  Type: Search"
        else:
            instructions = "←→: Switch wall  |  ↑↓: Navigate  |  Enter: Edit  |  /: Search  |  :: Command  |  ?: Help  |  q: Quit"
        
        if curses.LINES > 2:
            stdscr.addstr(curses.LINES - 2, 2, instructions[:curses.COLS - 4], curses.color_pair(3))
            
        # Show scroll indicator
        if not search_mode:
            total_items = len(chests[current_wall])
        else:
            total_items = len(search_results)
            
        if total_items > max_display_lines:
            scroll_info = f"[{view_offset + 1}-{min(view_offset + max_display_lines, total_items)}/{total_items}]"
            stdscr.addstr(curses.LINES - 1, curses.COLS - len(scroll_info) - 2, scroll_info)
        
        stdscr.refresh()
        key = stdscr.getch()

        if key in [ord('q'), ord('Q')] and not search_mode:
            break
        elif key == 27:  # ESC key
            if search_mode:
                search_mode = False
                search_query = ""
                search_results = []
                selected_idx = 0
                view_offset = 0
        elif key == ord('/') and not search_mode:
            search_mode = True
            search_query = ""
            selected_idx = 0
            view_offset = 0
        elif key == ord(':') and not search_mode:
            # Command mode
            curses.echo()
            stdscr.addstr(curses.LINES - 1, 2, "Command: ")
            stdscr.clrtoeol()
            try:
                command = stdscr.getstr(curses.LINES - 1, 11, 80).decode('utf-8')
                if command.strip():
                    result = parse_command(command, data)
                    save_data(data)  # Save after command execution
                    
                    # Show result message
                    stdscr.addstr(curses.LINES - 1, 2, result[:curses.COLS - 4])
                    stdscr.refresh()
                    stdscr.getch()  # Wait for keypress
            except KeyboardInterrupt:
                pass
            curses.noecho()
        elif key == ord('?') and not search_mode:
            # Show help
            stdscr.clear()
            stdscr.addstr(0, 2, "Command Help", curses.A_BOLD)
            help_lines = show_command_help()
            for i, line in enumerate(help_lines):
                if i + 2 < curses.LINES - 2:
                    stdscr.addstr(i + 2, 2, line)
            stdscr.addstr(curses.LINES - 1, 2, "Press any key to continue...")
            stdscr.refresh()
            stdscr.getch()
        elif search_mode:
            if key == curses.KEY_BACKSPACE or key == 127:
                if search_query:
                    search_query = search_query[:-1]
                    search_results = search_chests(data, search_query)
                    selected_idx = 0
                    view_offset = 0
            elif 32 <= key <= 126:  # Printable characters
                search_query += chr(key)
                search_results = search_chests(data, search_query)
                selected_idx = 0
                view_offset = 0
            elif key == curses.KEY_DOWN:
                if search_results:
                    selected_idx = min(selected_idx + 1, len(search_results) - 1)
                    # Auto-scroll
                    if selected_idx >= view_offset + max_display_lines:
                        view_offset += 1  # Move down only 1 item instead of jumping a full page
            elif key == curses.KEY_UP:
                if search_results:
                    selected_idx = max(selected_idx - 1, 0)
                    # Auto-scroll
                    if selected_idx < view_offset:
                        view_offset -= 1  # Move up only 1 item instead of jumping a full page
            elif key in [curses.KEY_ENTER, 10, 13] and search_results:
                # Edit selected search result
                chest_id, _ = search_results[selected_idx]
                curses.echo()
                stdscr.addstr(curses.LINES - 3, 2, "Enter new label: ")
                stdscr.clrtoeol()
                try:
                    label = stdscr.getstr(curses.LINES - 3, 18, 50).decode('utf-8')
                    data[chest_id] = label
                    save_data(data)
                    # Update search results
                    search_results = search_chests(data, search_query)
                except:
                    pass
                curses.noecho()
        else:
            # Normal navigation mode
            if key == curses.KEY_RIGHT:
                walls = list(chests.keys())
                current_wall = walls[(walls.index(current_wall) + 1) % len(walls)]
                selected_idx = 0
                view_offset = 0
            elif key == curses.KEY_LEFT:
                walls = list(chests.keys())
                current_wall = walls[(walls.index(current_wall) - 1) % len(walls)]
                selected_idx = 0
                view_offset = 0
            elif key == curses.KEY_DOWN:
                wall_chests_list = chests[current_wall]
                if selected_idx < len(wall_chests_list) - 1:
                    selected_idx += 1
                    
                    # Simple scrolling: if selection goes off bottom of screen, scroll down
                    if selected_idx >= view_offset + max_display_lines:
                        view_offset = selected_idx - max_display_lines + 1
                        # Make sure we don't scroll too far
                        if view_offset > len(wall_chests_list) - max_display_lines:
                            view_offset = max(0, len(wall_chests_list) - max_display_lines)
                            
            elif key == curses.KEY_UP:
                if selected_idx > 0:
                    selected_idx -= 1
                    
                    # Simple scrolling: if selection goes off top of screen, scroll up
                    if selected_idx < view_offset:
                        view_offset = selected_idx
            elif key == curses.KEY_NPAGE:  # Page Down
                wall_chests_list = chests[current_wall]
                selected_idx = min(selected_idx + max_display_lines, len(wall_chests_list) - 1)
                view_offset = min(view_offset + max_display_lines, max(0, len(wall_chests_list) - max_display_lines))
            elif key == curses.KEY_PPAGE:  # Page Up
                selected_idx = max(selected_idx - max_display_lines, 0)
                view_offset = max(view_offset - max_display_lines, 0)
            elif key in [curses.KEY_ENTER, 10, 13]:
                chest_id = chests[current_wall][selected_idx]
                # Initialize slot data if it doesn't exist
                if chest_id not in data:
                    data[chest_id] = {}
                elif isinstance(data[chest_id], str):
                    # Convert old string format to slot format
                    data[chest_id] = {}
                
                # Convert string keys to integers for slot data
                slot_data = {}
                if isinstance(data[chest_id], dict):
                    for key, value in data[chest_id].items():
                        # Convert string keys to int keys
                        try:
                            int_key = int(key)
                            slot_data[int_key] = tuple(value) if isinstance(value, list) else value
                        except (ValueError, TypeError):
                            # Skip invalid keys
                            pass
                
                edit_item_in_slot(stdscr, chest_id, slot_data)
                
                # Convert back to string keys for JSON storage
                data[chest_id] = {str(k): list(v) if isinstance(v, tuple) else v for k, v in slot_data.items()}
                save_data(data)
            elif key in [ord('d'), ord('D')]:
                # Delete/clear current chest
                chest_id = chests[current_wall][selected_idx]
                data[chest_id] = ""
                save_data(data)

    save_data(data)

if __name__ == "__main__":
    curses.wrapper(chest_tui)
    