# -*- coding: utf-8 -*-
# 220522 Copied from bleak
#   https://github.com/hbldh/bleak/blob/develop/examples/enable_notifications.py
#
# 220522 rg v1 Shows rolls from single die
# 220523 rg v2.1 Extend to multiple die and include device UUIC
# 220523 rg v2.2 Use gather( )
#

"""
Notifications
-------------

Example showing how to add notifications to a characteristic and handle the responses.

Updated on 2019-07-03 by hbldh <henrik.blidh@gmail.com>

"""

import sys
import asyncio
import platform

from bleak import BleakClient

# https://bleak.readthedocs.io/en/latest/troubleshooting.html#pass-more-parameters-to-a-notify-callback
from functools import partial

timeout_period = 20.  # sec

# you can change these to match your device or override them from the command line
# 6e400003-b5a3-f393-e0a9-e50e24dcca9e

class GoDice:
    def __init__(self, ADDRESS, CHARACTERISTIC_UUID, COLOR):
        self.address = ADDRESS
        self.char_uuid = CHARACTERISTIC_UUID
        self.color = COLOR

    def __repr__(self):  # Representation
        return (f"Color:{self.color}, Address:{self.address}, Char:{self.char_uuid}")

    def __str__(self):  # For printing
        return (f"Color:{self.color}, Address:{self.address}, Char:{self.char_uuid}")


# Setup list of goDice
listGoDice = []

if 1:
    listGoDice.append(GoDice(
        COLOR='R'
        , ADDRESS="D0CC6BEC-3905-874A-CC20-5F94225A7D28"
        , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # GoDice R - Possible channel to listen to
    ))

if 1:
    listGoDice.append(GoDice(
        COLOR='B'
        , ADDRESS="9F38B8FD-4189-47C6-7E65-84C208ED9B3E"
        , CHARACTERISTIC_UUID="6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # GoDice R - Possible channel to listen to
    ))

# Darwin is MacOS - requires full UUID
# ADDRESS = (
#    "00:00:00:00:00:00"
#    if platform.system() != "Darwin"
#    else "D0CC6BEC-3905-874A-CC20-5F94225A7D28" # GoDice R UUID - this works !!
# )

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
    print(
        f"Device {client.address},"
        f"Char handle {client.services.get_characteristic(sender)},"
        f"Data: {data}"
    )

async def connect_and_notify( g ):
    print(f"Notify: color = {g.color}")
    # print(f"address   = {g.address}")
    # print(f"char_uuid = {g.char_uuid}")

    async with BleakClient(g.address) as client:
    # client = BleakClient(g.address)
        print(f"  Connected = {client.is_connected}")

        if 1:
            await client.start_notify(
                g.char_uuid  # char_specifier
                , partial(notification_handler_with_client_input, client)  # Allows device to be identified
            )
        else:
            # Simple handler only gets notification handler
            await client.start_notify(
                g.char_uuid, notification_handler
            )

        print( f"Wait" )
        await asyncio.sleep(timeout_period)  # Wait for ?? secs to collect new state information

        print(f"Stop: color = {g.color}")
        # async with BleakClient(g.address) as client:
        await client.stop_notify( g.char_uuid )


# https://bleak.readthedocs.io/en/latest/troubleshooting.html#connecting-to-multiple-devices-at-the-same-time

async def main(listDevices):
    print("\nList of Dice:")
    for g in listDevices:
        print(g)
    print("\n")

    await asyncio.gather( *( connect_and_notify(g) for g in listDevices ) )


# if __name__ == "__main__":
# Not handling shell call arguments

asyncio.run(main(listGoDice))
