# Xiao RP2040 Macro Pad Firmware
# GPIO mapping: 1,2,4,3,0,28,26,27 for keys, GPIO6=SDA, GPIO7=SCL for OLED

import board
import digitalio
import busio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

# Initialize display
displayio.release_displays()
i2c = busio.I2C(board.GP7, board.GP6)  # SCL=GP7, SDA=GP6
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Initialize HID
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

# Key pins - adjust these to match your actual GPIO pins
KEY_PINS = [
    board.GP1,   # Key 0
    board.GP2,   # Key 1  
    board.GP4,   # Key 2
    board.GP3,   # Key 3
    board.GP0,   # Key 4
    board.GP28,  # Key 5
    board.GP26,  # Key 6
    board.GP27,  # Key 7
]

# Initialize keys with pull-up resistors
keys = []
for pin in KEY_PINS:
    key = digitalio.DigitalInOut(pin)
    key.direction = digitalio.Direction.INPUT
    key.pull = digitalio.Pull.UP
    keys.append(key)

# Key state tracking for debouncing
key_states = [True] * len(keys)  # True = not pressed (pull-up)
last_key_states = [True] * len(keys)

# Mode tracking
current_mode = 0
max_modes = 4
mode_switch_key = 0  # Key 0 (GPIO1) switches modes

# Define key mappings for each mode
KEY_MAPPINGS = {
    0: {  # Mode 0 - Basic shortcuts
        1: [Keycode.CONTROL, Keycode.C],        # Ctrl+C
        2: [Keycode.CONTROL, Keycode.V],        # Ctrl+V
        3: [Keycode.CONTROL, Keycode.Z],        # Ctrl+Z
        4: [Keycode.CONTROL, Keycode.S],        # Ctrl+S
        5: [Keycode.ALT, Keycode.TAB],          # Alt+Tab
        6: [Keycode.CONTROL, Keycode.T],        # Ctrl+T
        7: [Keycode.CONTROL, Keycode.W],        # Ctrl+W
    },
    1: {  # Mode 1 - Media controls
        1: 'VOLUME_UP',
        2: 'VOLUME_DOWN',
        3: 'MUTE',
        4: 'PLAY_PAUSE',
        5: 'SCAN_NEXT_TRACK',
        6: 'SCAN_PREVIOUS_TRACK',
        7: 'STOP',
    },
    2: {  # Mode 2 - Function keys
        1: [Keycode.F1],
        2: [Keycode.F2],
        3: [Keycode.F3],
        4: [Keycode.F4],
        5: [Keycode.F5],
        6: [Keycode.F6],
        7: [Keycode.F7],
    },
    3: {  # Mode 3 - Programming shortcuts
        1: [Keycode.CONTROL, Keycode.SHIFT, Keycode.P],  # Command palette
        2: [Keycode.CONTROL, Keycode.GRAVE_ACCENT],      # Terminal
        3: [Keycode.CONTROL, Keycode.SHIFT, Keycode.I],  # Dev tools
        4: [Keycode.F5],                                 # Run/Refresh
        5: [Keycode.CONTROL, Keycode.F],                 # Find
        6: [Keycode.CONTROL, Keycode.H],                 # Replace
        7: [Keycode.CONTROL, Keycode.SHIFT, Keycode.F],  # Format
    }
}

def update_display():
    """Update OLED display with current mode"""
    # Create display group
    splash = displayio.Group()
    
    # Mode title
    mode_text = f"Mode {current_mode}"
    mode_label = label.Label(terminalio.FONT, text=mode_text, color=0xFFFFFF, x=10, y=15)
    splash.append(mode_label)
    
    # Mode description
    descriptions = [
        "Basic Shortcuts",
        "Media Controls", 
        "Function Keys",
        "Programming"
    ]
    
    desc_text = descriptions[current_mode]
    desc_label = label.Label(terminalio.FONT, text=desc_text, color=0xFFFFFF, x=10, y=35)
    splash.append(desc_label)
    
    # Key count
    key_count = len(KEY_MAPPINGS[current_mode])
    count_text = f"{key_count} keys active"
    count_label = label.Label(terminalio.FONT, text=count_text, color=0xFFFFFF, x=10, y=55)
    splash.append(count_label)
    
    display.show(splash)

def send_keypress(key_num):
    """Send appropriate keypress based on current mode and key"""
    if key_num not in KEY_MAPPINGS[current_mode]:
        return
        
    mapping = KEY_MAPPINGS[current_mode][key_num]
    
    # Handle media controls
    if isinstance(mapping, str):
        media_codes = {
            'VOLUME_UP': ConsumerControlCode.VOLUME_INCREMENT,
            'VOLUME_DOWN': ConsumerControlCode.VOLUME_DECREMENT,
            'MUTE': ConsumerControlCode.MUTE,
            'PLAY_PAUSE': ConsumerControlCode.PLAY_PAUSE,
            'SCAN_NEXT_TRACK': ConsumerControlCode.SCAN_NEXT_TRACK,
            'SCAN_PREVIOUS_TRACK': ConsumerControlCode.SCAN_PREVIOUS_TRACK,
            'STOP': ConsumerControlCode.STOP,
        }
        if mapping in media_codes:
            cc.send(media_codes[mapping])
    
    # Handle keyboard combinations
    elif isinstance(mapping, list):
        kbd.send(*mapping)

def switch_mode():
    """Switch to next mode"""
    global current_mode
    current_mode = (current_mode + 1) % max_modes
    update_display()
    print(f"Switched to mode {current_mode}")

# Initialize display
update_display()
print("Macro pad initialized")

# Main loop
while True:
    # Read all keys
    for i, key in enumerate(keys):
        key_states[i] = key.value
    
    # Check for key presses (transition from True to False due to pull-up)
    for i in range(len(keys)):
        if last_key_states[i] and not key_states[i]:  # Key pressed
            print(f"Key {i} pressed")
            
            if i == mode_switch_key:
                switch_mode()
            else:
                send_keypress(i)
            
            # Add delay to prevent bouncing
            time.sleep(0.1)
    
    # Update last states
    last_key_states = key_states.copy()
    
    # Small delay for main loop
    time.sleep(0.01)