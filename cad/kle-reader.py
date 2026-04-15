# -*- coding: utf-8 -*-
"""
KLE to KiCad PCB placement script
Based on keyboard community implementations
"""

import json
import math
import re
from pathlib import Path

import pcbnew


# =========================
# CONFIG
# =========================
KLE_JSON_PATH = "/Users/mori/Documents/MyProject/mami-kbd/kle/layout.json"
PITCH_MM = 19.05  # Standard MX spacing
ORIGIN_X_MM = 30
ORIGIN_Y_MM = 70
FOOTPRINT_REF_REGEX = r"^SW\d+$"
FLIP_Y = False


def natural_sort_key(text):
    """Natural sort for reference names like SW1, SW2, SW10"""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]


def mm_to_pcb_units(x_mm, y_mm):
    """Convert mm to KiCad units"""
    if hasattr(pcbnew, "VECTOR2I"):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))
    return pcbnew.wxPointMM(x_mm, y_mm)


def set_fp_position(fp, x_mm, y_mm):
    fp.SetPosition(mm_to_pcb_units(x_mm, y_mm))


def set_fp_rotation(fp, deg):
    if hasattr(fp, "SetOrientationDegrees"):
        fp.SetOrientationDegrees(deg)
    else:
        fp.SetOrientation(int(round(deg * 10)))


def parse_kle(kle_data):
    """
    Parse KLE raw data format
    Returns list of keys with their positions
    """
    keys = []
    
    # Rotation state (persistent across rows)
    rotation_angle = 0
    rotation_x = 0
    rotation_y = 0
    
    for row in kle_data:
        if not isinstance(row, list):
            continue
            
        # Check if this row only contains metadata
        has_key_data = any(not isinstance(item, dict) or 
                          any(k in item for k in ['x', 'y', 'w', 'h', 'r', 'rx', 'ry'])
                          for item in row)
        if not has_key_data:
            continue
        
        # Row-local X position (resets for each row)
        current_x = 0
        
        # Temporary properties for next key
        next_x = 0
        next_y = 0
        next_w = 1.0
        next_h = 1.0
        
        for item in row:
            if isinstance(item, dict):
                # Property object
                
                # Rotation properties (persistent)
                if 'r' in item:
                    rotation_angle = item['r']
                if 'rx' in item:
                    rotation_x = item['rx']
                    current_x = 0  # Reset x when rx changes
                if 'ry' in item:
                    rotation_y = item['ry']
                
                # Position/size properties (for next key only)
                if 'x' in item:
                    next_x += item['x']
                if 'y' in item:
                    next_y = item['y']  # Absolute Y from rotation origin
                if 'w' in item:
                    next_w = item['w']
                if 'h' in item:
                    next_h = item['h']
                    
            else:
                # This is a key
                label = str(item) if item else ""
                
                # Calculate key position relative to rotation origin
                key_x = current_x + next_x
                key_y = next_y
                
                # Key center in local coordinates
                center_x = key_x + next_w / 2.0
                center_y = key_y + next_h / 2.0
                
                # Apply rotation around (rotation_x, rotation_y)
                if rotation_angle != 0:
                    rad = math.radians(rotation_angle)
                    dx = center_x - rotation_x
                    dy = center_y - rotation_y
                    rotated_x = rotation_x + dx * math.cos(rad) - dy * math.sin(rad)
                    rotated_y = rotation_y + dx * math.sin(rad) + dy * math.cos(rad)
                else:
                    rotated_x = center_x + rotation_x
                    rotated_y = center_y + rotation_y
                
                keys.append({
                    'label': label,
                    'x': rotated_x,
                    'y': rotated_y,
                    'w': next_w,
                    'h': next_h,
                    'rotation': rotation_angle,
                    'rotation_x': rotation_x,
                    'rotation_y': rotation_y
                })
                
                # Move to next key position
                current_x = key_x + next_w
                
                # Reset temporary properties
                next_x = 0
                next_y = 0
                next_w = 1.0
                next_h = 1.0
    
    return keys


def main():
    # Load KLE data
    kle_path = Path(KLE_JSON_PATH)
    if not kle_path.exists():
        raise FileNotFoundError(f"KLE JSON not found: {kle_path}")
    
    with kle_path.open('r', encoding='utf-8') as f:
        kle_data = json.load(f)
    
    # Parse KLE
    keys = parse_kle(kle_data)
    
    # Get KiCad board
    board = pcbnew.GetBoard()
    if not board:
        raise RuntimeError("No board is open in PCB Editor")
    
    # Get all switch footprints
    footprints = [fp for fp in board.GetFootprints() 
                  if re.match(FOOTPRINT_REF_REGEX, fp.GetReference())]
    
    if not footprints:
        raise RuntimeError("No switch footprints found")
    
    # Create mapping from reference to footprint
    fp_map = {fp.GetReference(): fp for fp in footprints}
    
    print(f"[INFO] Found {len(keys)} keys in KLE")
    print(f"[INFO] Found {len(footprints)} switch footprints in PCB")
    print(f"[INFO] Using {PITCH_MM}mm pitch")
    
    placed = 0
    
    for key in keys:
        # Extract switch number from label
        label = key['label']
        match = re.match(r'^SW(\d+)$', label)
        
        if not match:
            print(f"[SKIP] Non-switch label: {label}")
            continue
        
        ref = f"SW{match.group(1)}"
        
        if ref not in fp_map:
            print(f"[WARN] Footprint {ref} not found on board")
            continue
        
        fp = fp_map[ref]
        
        # Calculate position in mm
        x_mm = ORIGIN_X_MM + key['x'] * PITCH_MM
        y_mm = ORIGIN_Y_MM + key['y'] * PITCH_MM
        
        if FLIP_Y:
            y_mm = -y_mm
        
        # Set position and rotation
        set_fp_position(fp, x_mm, y_mm)
        set_fp_rotation(fp, -key['rotation'])  # Negative for KiCad convention
        
        print(f"[PLACE] {ref:>5} @ ({x_mm:>7.2f}, {y_mm:>7.2f}) rot={-key['rotation']:>6.1f}°")
        placed += 1
    
    # Refresh display
    pcbnew.Refresh()
    
    print(f"\n[DONE] Placed {placed} switches")


if __name__ == "__main__":
    main()
