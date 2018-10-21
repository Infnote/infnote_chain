import sys
import os

# Add current path to python path for fixing wrong importing in protobuf generated file
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
