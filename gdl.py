from bleak import BleakClient
from bleak import BleakScanner
import asyncio
import datetime
import numpy as np

global listGoDice

# Representation used in rest of code for each dice
class GoDice:
    global listGoDice

    """
    GoDice parameters of the form
          NAME = 'GoDice_F84146_R_v03'
        , ADDRESS="D0CC6BEC-3905-874A-CC20-5F94225A7D28"
        , COLOR ='R'
        , COLORLONG = 'RED   '
        , DICEINDEX = 11
        , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Channel to listen to - same for all dice
    """

    def _extractDiceColor(self,name):
        if isinstance(name,str) and name[13:14] == '_' and name[15:16] == '_':
            c = name[14:15]  # Color as single letter in the name
        else:
            print(f'WARNING: Unable to recognize dice color from device name {name}')
            print(f'... Expected fixed length string of content e.g. GoDice_F84146_R_v03')
            print(f'... _<col char>_ does not appear where expected')
            c = 'X' # Color not known

        return( c )

    _diceLookup = {
        "K": (600, "BLACK  ")
        , "R": (601, "RED    ")
        , "G": (602, "GREEN  ")
        , "B": (603, "BLUE   ")
        , "Y": (604, "ORANGE ")
        , "O": (605, "YELLOW ")
        , "X": (699, "UNKNOWN") # Color not recognized
    }


    def _extractDiceIndex(self,name):
        color = self._extractDiceColor(name)
        return( self._diceLookup[color][0] )

    def _extractDiceColorLong(self,name):
        color = self._extractDiceColor(name)
        return( self._diceLookup[color][1] )

    def __init__(self, NAME , ADDRESS):
        self.name = NAME
        self.color = self._extractDiceColor(NAME)
        self.address = ADDRESS
        self.colorlong = self._extractDiceColorLong(NAME)
        self.char_uuid = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
        self.connected = False
        self.diceIndex = self._extractDiceIndex(NAME) # numerical index for dice used in data analysis

    def __repr__(self):  # Representation
        # return (f"Color:{self.color}, Address:{self.address}, Char:{self.char_uuid}")
        return (f"{self.color} - Color:{self.colorlong}, Address:{self.address}")

    def __str__(self):  # For printing
        # return (f"Color:{self.color}, Address:{self.address}, Char:{self.char_uuid}")
        return (f"{self.color} - Color:{self.colorlong}, Address:{self.address}")

# The following should be brought into line with GoDice standard way of detemining face
# The methods should also be part of the GoDice class

def distMod(a,b,m): # distance between a,b in modulus m
  diff = abs( b - a )
  return min( diff, m - diff )

def dmt(a,b): # distance between a,b in modulus 256 is <= 16
  return (min( abs( b - a ), 256 - abs( b - a ) ) <= 16)

def decodeDice( ba ):
  # tol = 16 # tolerance for determining face that is up, typically 16 - set in function

  x = list( ba )

  '''
          public const string Battery = "Bat";
          public const string Roll = "R";
          public const string Stable = "S";
          public const string FakeStable = "FS";
          public const string MoveStable = "MS";
          public const string TiltStable = "TS";
  '''

  # ix is character for next read from string
  if len(x) > 0:
    if x[0] == ord('R'):
      return(0) # Rolling
    elif x[0]== ord('S'):
      ix = 1 # Stable
    elif x[1]== ord('S'):
      ix = 2 # Other roll results FS,MS,TS that may be usable
    else:
      return(0) # Don't recognize return

  '''
  uvw table
  1 \xc0 \x00 \x00     3 0 0
  2 \x00 \x00 \x40     0 0 1    
  3 \x00 \x40 \x00     0 1 0 
  4 \x00 \xc0 \x00     0 3 0
  5 \x00 \x00 \xc0     0 0 3 
  6 \x40 \x00 \xff     1 0 0
  '''

  # If we are close to known orientation return the six-sided dice result
  if dmt(x[ix+0],192) and dmt(x[ix+1],0) and dmt(x[ix+2],0): return(1)
  if dmt(x[ix+2], 64) and dmt(x[ix+0],0) and dmt(x[ix+1],0): return(2)
  if dmt(x[ix+1], 64) and dmt(x[ix+0],0) and dmt(x[ix+2],0): return(3)
  if dmt(x[ix+1],192) and dmt(x[ix+0],0) and dmt(x[ix+2],0): return(4)
  if dmt(x[ix+2],192) and dmt(x[ix+0],0) and dmt(x[ix+1],0): return(5)
  if dmt(x[ix+0], 64) and dmt(x[ix+1],0) and dmt(x[ix+2],0): return(6)

  return(-1) # shouldn't get this unless dice is on edge


# Used for diagnostics
def print_device_details(d: object) -> object:
    print("\n--------------------------------")
    print(d)
    type(d)
    print(dir(d))
    print('Name', d.name)
    print('Dice?:', 'GoDice' in d.name)
    print('Address', d.address)
    print('Details', d.details)
    print('Meta', d.metadata)
    print('RSSI', d.rssi)
