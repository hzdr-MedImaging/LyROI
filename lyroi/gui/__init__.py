import sys
import signal

def error_handler(exctype, value, traceback):
  print()
  print("Error:", value, file=sys.stderr)
  sys.exit(1)

def exit_handler(signal, frame):
  print()
  print("User abort (CTRL-C) received.")
  sys.exit(0)

signal.signal(signal.SIGINT, exit_handler)
sys.excepthook = error_handler