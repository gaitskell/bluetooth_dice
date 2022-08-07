# Scan for Specific Bluetooth GoDice Devices and then Record Their Rolls for defined period
# 220804 rg v2.1 Build from previous code
# 2208
# https://pypi.org/project/bleak/
#
#

maxDataTakingPeriod = 10.  # sec SET BY USER
timeout_period = maxDataTakingPeriod  # sec # Don't have a way to tieout individual dice yet


import asyncio
from bleak import BleakClient
from bleak import BleakScanner

# https://bleak.readthedocs.io/en/latest/troubleshooting.html#pass-more-parameters-to-a-notify-callback
from functools import partial

import asyncio
import datetime
import numpy as np
import gdl  # Supoort routines for GoDice

if 0:
    # Use this in console when debugging to reload a library
    from importlib import reload  # Python 3.4+
    godicelib = reload(gdl)


diceOutcomes = np.zeros((100000,3)) # Prereserve data array for recording results
diceOutcomesIndex = 0 # Position to write data into
startTime = datetime.datetime.now() # Record time of each roll

# Bluetooth Devices
global devices
global listGoDice
listGoDice = []



# Look up device uuid and return device name
def device_UUID2Name( uuid_address ):
    global listGoDice
    for d in listGoDice:
        if d.address is uuid_address:
            return( d.name )
    return( "--No Name--" )


def device_UUID2DiceIndex( uuid_address ):
    global listGoDice
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

    d = gdl.decodeDice(data)
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


# This version is currently too simple
# - need to find another way that will attempt a reconnect
# although it does appear that bluetooth does attempt to reconnect so may not be necessary
def handle_disconnect(  client : BleakClient ):  # _: BleakClient
    print( f"\nWARNING: Device was disconnected" )
    print( client )
    print( "\n" )
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
    # This method is run for each GoDice
    global startTime, flagContinue

    # print(f"Notify: color = {g.color}")
    # print(f"address   = {g.address}")
    # print(f"char_uuid = {g.char_uuid}")

    # See https://www.w3schools.com/python/python_try_except.asp
    # https://docs.python.org/3/reference/compound_stmts.html#the-try-statement
    try:
        async with BleakClient(g.address , disconnected_callback= handle_disconnect ) as client:
        #
        # async with BleakClient(g.address , disconnected_callback=partial( handle_disconnect , client ) ) as client:
        # In above client is not set yet for the partial statement - how do I pass the client info???
        #
        # client = BleakClient(g.address)

            if client.is_connected:
                print(f"\n{g.name} - Connected")
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
                    print( f"{g.name} - {timeout_period}s timeout")
                    await asyncio.sleep(timeout_period)  # Wait for ?? secs to collect new state information

                else :
                    # Allow user to trigger early end by not rolling dice
                    # This code doesn't work at present
                    while (
                            flagContinue
                            and
                            ( (datetime.datetime.now() - startTime).total_seconds() ) < maxDataTakingPeriod
                    ) :
                        flagContinue = False # if no roll during timeout period stop
                        await asyncio.sleep(timeout_period)  # Wait for ?? secs to collect new state information

                print(f"{g.name} - Stop")
                # async with BleakClient(g.address) as client:
                await client.stop_notify( g.char_uuid )

            else:
                print(f"{g.name} Not Connected")

    except Exception as ex:
        print( f"\n{g.name} - ERROR: Bleak excepton" )
        print( ex )
        print( "\n")

# https://bleak.readthedocs.io/en/latest/troubleshooting.html#connecting-to-multiple-devices-at-the-same-time

async def main(  ):
    global diceOutcomesIndex, diceOutcomes
    global maxDataTakingPeriod, timeout_period

    global devices # All bluetooth devices in range / used in diagnostics

    global listGoDice # All GoDice
    listGoDice = []

    #---------------------------------------------------------------
    # SCAN BLUETOOTH FOR GODICE
    print('\n\nSCANNING for any GoDice')
    # All bluetooth devices
    devices = await BleakScanner.discover() # Not using explicit timeout
    # list( enumerate( devices ) ) # Diagnostic

    # Look through bluetooth list for any GoDice
    for d in devices:
        if False: gdl.print_device_details(d) # Diagnostic
        # Check for GoDice e.g. name: GoDice_F84146_R_v03
        if isinstance(d.name, str) and d.name.startswith("GoDice"):
            listGoDice.append( gdl.GoDice(d.name , d.address) )

    if len( listGoDice ) > 0:
        print(f"\nFound {len(listGoDice)} Dice:")
        for g in listGoDice: print(g)
    else:
        print("WARNING: No GoDice Found")
        return()
    print("\n")

    print( f'Take data for a maximum of {maxDataTakingPeriod} secs')
    # print( f'An individual dice will time out after {timeout_period} secs')
    # print("\n")

    await asyncio.gather( *( connect_and_notify(g) for g in listGoDice ) )

    # print( f"Total Data {diceOutcomesIndex}")
    diceOutcomes = np.delete( diceOutcomes , np.s_[diceOutcomesIndex:] , 0) # Get rid of not used elements

    outfile = 'data/DiceOutcomes_'+startTime.strftime('%y%m%dT%H%M%S')
    np.save( outfile, diceOutcomes  ) # diceOutcomesIndex

    print(f"\n========================================")
    print(f"Saved results from {diceOutcomesIndex} rolls")
    print(f"based on {len(np.unique(diceOutcomes[:,1]))} dice")
    print(f"and a period of {(diceOutcomes[-1,0]-diceOutcomes[0,0])/60.:.1f} minutes")
    print(f"see file - {outfile}.npy")

# Run the main loop
asyncio.run( main(  ) )


"""
if 0:
    print( '\n\nACCESS DEVICE - doesnt work yet for GoDice' )

    async with BleakClient(address) as client:
        model_number = await client.read_gatt_char(MODEL_NBR_UUID)
        print("Model Number: {0}".format("".join(map(chr, model_number))))
"""
