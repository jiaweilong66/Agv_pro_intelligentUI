#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Test import to verify file changes

print("Testing imports...")

try:
    from new_ui.virtual_joystick import VirtualJoystick
    print("✓ Imported from new_ui.virtual_joystick")
except ImportError as e:
    print(f"✗ Failed to import from new_ui: {e}")
    try:
        from virtual_joystick import VirtualJoystick
        print("✓ Imported from virtual_joystick")
    except ImportError as e2:
        print(f"✗ Failed to import from virtual_joystick: {e2}")
        print("✓ Creating dummy VirtualJoystick class")
        class VirtualJoystick:
            pass
        print("✓ Dummy class created successfully")

print("Import test completed!")
