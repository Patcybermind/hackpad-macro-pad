import storage
import usb_cdc
import usb_hid

# Disable USB storage (CIRCUITPY drive won't appear)
storage.disable_usb_drive()

# Optional: Also disable serial console if you want
# usb_cdc.disable()