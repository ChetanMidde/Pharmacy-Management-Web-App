import traceback
import sys

try:
    from backend import main
    print("Backend loaded successfully!")
except Exception as e:
    print("ERROR LOADING BACKEND:")
    traceback.print_exc(file=sys.stdout)
