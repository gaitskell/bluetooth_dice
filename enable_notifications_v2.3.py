# -*- coding: utf-8 -*-
# 220522 Copied from bleak
#   https://github.com/hbldh/bleak/blob/develop/examples/enable_notifications.py
#
# 220522 rg v1 Shows rolls from single die
# 220523 rg v2.1 Extend to multiple die and include device UUIC
# 220523 rg v2.2 Use gather( ) access two dice
# 220524 rg v2.3 Add all dice
# 220608 rg Add counter in window

"""
Notifications
-------------

Example showing how to add notifications to a characteristic and handle the responses.

Updated on 2019-07-03 by hbldh <henrik.blidh@gmail.com>

"""

import sys
import asyncio
import platform
import datetime
import time
import numpy as np
import pynput

from bleak import BleakClient

# https://bleak.readthedocs.io/en/latest/troubleshooting.html#pass-more-parameters-to-a-notify-callback
from functools import partial

'''
# Listen for mouse down - exits run
from pynput.mouse import Listener

def on_click(x, y, button, pressed):   # https://pythonhosted.org/pynput/mouse.html#monitoring-the-mouse
    print('{0} at {1}'.format(
        'Pressed' if pressed else 'Released',
        (x, y)))

    if pressed:
        flagContinue = False

    if not pressed:
        # Stop listener
        return False

with Listener(on_click = on_click ) as listener:
    listener.join()

''';

flagContinue = True # Whether to keep looping

maxDataTakingPeriod = 20. # sec
timeout_period = 240.  # sec

diceOutcomes = np.zeros((100000,3))
diceOutcomesIndex = 0 # Position to write data into
startTime = datetime.datetime.now()

# you can change these to match your device or override them from the command line
# 6e400003-b5a3-f393-e0a9-e50e24dcca9e

class GoDice:
    def __init__(self, ADDRESS, CHARACTERISTIC_UUID, COLOR , NAME , DICEINDEX):
        self.address = ADDRESS
        self.char_uuid = CHARACTERISTIC_UUID
        self.color = COLOR
        self.connected = False
        self.name = NAME
        self.diceIndex = DICEINDEX # numerical index for data handling

    def __repr__(self):  # Representation
        return (f"Color:{self.color}, Address:{self.address}, Char:{self.char_uuid}")

    def __str__(self):  # For printing
        return (f"Color:{self.color}, Address:{self.address}, Char:{self.char_uuid}")

"""
Setup list of goDice
D0CC6BEC-3905-874A-CC20-5F94225A7D28: GoDice_F84146_R_v03
9F38B8FD-4189-47C6-7E65-84C208ED9B3E: GoDice_43F96D_B_v03
717DF7DA-6B7B-B515-E0F3-9E35BA7BE2E3: GoDice_15A25D_K_v03
B50E2850-31EB-B32E-28AA-D23638C7D9F6: GoDice_2388F4_Y_v03
9A3A97AC-E2CA-06BC-DF36-1D8D57283CAE: GoDice_017260_G_v03
E440F3E5-3136-5A68-DFC5-012407A84B39: GoDice_2DAD6A_O_v03
"""

listGoDice = []

listGoDice.append(GoDice(
    COLOR='R'
    , NAME='RED   '
    , DICEINDEX = 11
    , ADDRESS="D0CC6BEC-3905-874A-CC20-5F94225A7D28"
    , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Channel to listen to
))

listGoDice.append(GoDice(
    COLOR='B'
    , NAME='BLUE  '
    , DICEINDEX=15
    , ADDRESS="9F38B8FD-4189-47C6-7E65-84C208ED9B3E"
    , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Channel to listen to
))

listGoDice.append(GoDice(
    COLOR='K'
    , NAME='BLACK '
    , DICEINDEX=16
    , ADDRESS="717DF7DA-6B7B-B515-E0F3-9E35BA7BE2E3"
    , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Channel to listen to
))

listGoDice.append(GoDice(
    COLOR='Y'
    , NAME='YELLOW'
    , DICEINDEX=13
    , ADDRESS="B50E2850-31EB-B32E-28AA-D23638C7D9F6"
    , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Channel to listen to
))

listGoDice.append(GoDice(
    COLOR='G'
    , NAME='GREEN '
    , DICEINDEX=14
    , ADDRESS="9A3A97AC-E2CA-06BC-DF36-1D8D57283CAE"
    , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Channel to listen to
))

listGoDice.append(GoDice(
    COLOR='O'
    , NAME='ORANGE'
    , DICEINDEX = 12
    , ADDRESS="E440F3E5-3136-5A68-DFC5-012407A84B39"
    , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Channel to listen to
))

# Darwin is MacOS - requires full UUID
# ADDRESS = (
#    "00:00:00:00:00:00"
#    if platform.system() != "Darwin"
#    else "D0CC6BEC-3905-874A-CC20-5F94225A7D28" # GoDice R UUID - this works !!
# )


def distMod(a,b,m): # distance between a,b in modulus m
  diff = abs( b - a )
  return min( diff, m - diff )

def dmt(a,b): # distance between a,b in modulus 256 is <= 16
  return (min( abs( b - a ), 256 - abs( b - a ) ) <= 16)

def decodeDice( ba ):
  tol = 16 # tolerance
  x = list( ba )
  '''
          public const string Battery = "Bat";
          public const string Roll = "R";
          public const string Stable = "S";
          public const string FakeStable = "FS";
          public const string MoveStable = "MS";
          public const string TiltStable = "TS";
  '''
  if len(x) > 0:
    if x[0] == ord('R'):
      return(0) # Rolling
    elif x[0]== ord('S'):
      ix = 1 # Stable
    elif x[1]== ord('S'):
      ix = 2 # Other rolls that we can use
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
  if dmt(x[ix+0],192) and dmt(x[ix+1],0) and dmt(x[ix+2],0): return(1)
  if dmt(x[ix+2], 64) and dmt(x[ix+0],0) and dmt(x[ix+1],0): return(2)
  if dmt(x[ix+1], 64) and dmt(x[ix+0],0) and dmt(x[ix+2],0): return(3)
  if dmt(x[ix+1],192) and dmt(x[ix+0],0) and dmt(x[ix+2],0): return(4)
  if dmt(x[ix+2],192) and dmt(x[ix+0],0) and dmt(x[ix+1],0): return(5)
  if dmt(x[ix+0], 64) and dmt(x[ix+1],0) and dmt(x[ix+2],0): return(6)

  return(-1) # shouldn't get this unless dice is on edge



# Look up device uuid and return device name
def device_UUID2Name( uuid_address ):
    for d in listGoDice:
        if d.address is uuid_address:
            return( d.name )
    return( "--No Name--" )

def device_UUID2DiceIndex( uuid_address ):
    for d in listGoDice:
        if d.address is uuid_address:
            return( d.diceIndex )
    return( -1 )


# Simple notification handler which prints the data received.
def notification_handler(sender, data):
    print( f"{sender}: {data}" )


# Notification callback with client awareness
# https://bleak.readthedocs.io/en/latest/troubleshooting.html#pass-more-parameters-to-a-notify-callback
def notification_handler_with_client_input(
        client: BleakClient
        , sender: int
        , data: bytearray
    ):
    global diceOutcomesIndex, diceOutcomes, flagContinue

    d = decodeDice(data)
    if d>0 :
        print(
            f"({diceOutcomesIndex:3d}) Device {device_UUID2Name(client.address)},"
            # f"Char handle {client.services.get_characteristic(sender)},"
            #f"Data: {data}"
            f"Data: {d}"
        )

        diceOutcomes[diceOutcomesIndex, :] = [
            (datetime.datetime.now() - startTime).total_seconds()
            , device_UUID2DiceIndex(client.address)
            , d
        ]
        diceOutcomesIndex += 1
        flagContinue = True # Refresh since dice has been rolled recently


# This version is too simple - need to find another one that will attempt a reconnect
def handle_disconnect(  client : BleakClient ):  # _: BleakClient
    print( f"\nWARNING: Device was disconnected." )
    print( client )
    # print( f"\nDevice {client.address} was disconnected.\n" )
    #
    # Need to set g.connected = False
    #
    # cancelling all tasks effectively ends the program
    #for task in asyncio.all_tasks():
    #    task.cancel()
#     async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
#         await client.start_notify(UART_TX_CHAR_UUID, handle_rx)


async def connect_and_notify( g ):
    global startTime, flagContinue
    #print(f"Notify: color = {g.color}")
    # print(f"address   = {g.address}")
    # print(f"char_uuid = {g.char_uuid}")

    try: # See https://www.w3schools.com/python/python_try_except.asp
         # https://docs.python.org/3/reference/compound_stmts.html#the-try-statement

        async with BleakClient(g.address , disconnected_callback= handle_disconnect ) as client:
        #
        # async with BleakClient(g.address , disconnected_callback=partial( handle_disconnect , client ) ) as client:
        # In above client is not set yet for the partial statement - how do I pass the client info???
        #
        # client = BleakClient(g.address)


            if client.is_connected:
                print(f"{g.name} Connected")
                g.connected = True

                await client.start_notify(
                    g.char_uuid  # char_specifier
                    , partial(notification_handler_with_client_input, client)  # Allows device to be identified
                )
                """
                # Simple handler only gets notification handler
                await client.start_notify(
                    g.char_uuid, notification_handler
                )
                """

                # print( f"Wait" )
                if 1:
                    # Simple wait for timeout
                    await asyncio.sleep(timeout_period)  # Wait for ?? secs to collect new state information
                else :
                    # Allow user to trigger early end by not rolling dice
                    while (
                            flagContinue
                            and
                            ( (datetime.datetime.now() - startTime).total_seconds() ) < maxDataTakingPeriod
                    ) :
                        flagContinue = False # if no roll during timeout period stop
                        await asyncio.sleep(timeout_period)  # Wait for ?? secs to collect new state information

                print(f"Stop: color = {g.name}")
                # async with BleakClient(g.address) as client:
                await client.stop_notify( g.char_uuid )

            else:
                print(f"{g.name} Not Connected")


    except Exception as ex:
        print( "ERROR: Bleak problem" )
        #print( ex )
        #print( "\n")

# https://bleak.readthedocs.io/en/latest/troubleshooting.html#connecting-to-multiple-devices-at-the-same-time

async def main(listDevices):
    global diceOutcomesIndex, diceOutcomes
    global maxDataTakingPeriod, timeout_period

    print("\nList of Dice:")
    for g in listDevices:
        print(g)
    print("\n")

    print( f'Take data for a maximum of {maxDataTakingPeriod} secs')
    print( f'An individual dice will time out after {timeout_period} secs')
    print("\n")

    await asyncio.gather( *( connect_and_notify(g) for g in listDevices ) )

    print( f"\n\nTotal Data {diceOutcomesIndex}")
    diceOutcomes = np.delete( diceOutcomes , np.s_[diceOutcomesIndex:] , 0) # Get rid of not used elements

    outfile = 'DiceOutcomes_'+startTime.strftime('%y%m%dT%H%M%S')
    np.save( outfile, diceOutcomes  ) # diceOutcomesIndex

# if __name__ == "__main__":
# Not handling shell call arguments

asyncio.run(main(listGoDice))
