import sys
import os
import signal
import traceback

def error_handler(exctype, value, traceback):
  print()
  print("Error:", value, file=sys.stderr)
  sys.exit(1)

def exit_handler(signal, frame):
  print()
  print("User abort (CTRL-C) received.")
  sys.exit(0)

def show_error_dialog_win(title, message):
  """Display a Windows error message box"""
  import ctypes
  ctypes.windll.user32.MessageBoxW(
    0,  # HWND owner (NULL for no owner)
    message,
    title,
    0x10 | 0x1000  # MB_ICONERROR | MB_SYSTEMMODAL
  )

def error_handler_win(exc_type, exc_value, exc_traceback):
  """Handle any uncaught exception"""
  # Format the error
  error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

  # Show in message box
  show_error_dialog_win(
    "Application Error",
    f"An unexpected error occurred:\n\n{error_msg}"
  )

  sys.exit(1)

signal.signal(signal.SIGINT, exit_handler)
# signal.signal(signal.SIGBREAK, empty_handler) # prevent GUI from dying on Windows
if os.name == 'nt':
  sys.excepthook = error_handler_win
else:
  sys.excepthook = error_handler