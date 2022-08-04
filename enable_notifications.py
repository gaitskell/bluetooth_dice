# -*- coding: utf-8 -*-
# 220522 Copied from bleak
#   https://github.com/hbldh/bleak/blob/develop/examples/enable_notifications.py
#
#
"""
Notifications
-------------

Example showing how to add notifications to a characteristic and handle the responses.

Updated on 2019-07-03 by hbldh <henrik.blidh@gmail.com>

"""

import sys
import asyncio
# import platform

from bleak import BleakClient

timeout_period = 20.# sec

# you can change these to match your device or override them from the command line
# 6e400003-b5a3-f393-e0a9-e50e24dcca9e

if 1:
    # GoDice R
    ADDRESS = "D0CC6BEC-3905-874A-CC20-5F94225A7D28"
    CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e" # GoDice R - Possible channel to listen to
    COLOR = 'R'

if 0:
    # GoDice B
    ADDRESS = "9F38B8FD-4189-47C6-7E65-84C208ED9B3E"
    CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
    COLOR = 'B'


#ADDRESS = (
#    "00:00:00:00:00:00"
#    if platform.system() != "Darwin"
#    else "D0CC6BEC-3905-874A-CC20-5F94225A7D28" # GoDice R UUID - this works !!
#)


def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    print("{0}: {1}".format(sender, data))


async def main(address, char_uuid):
    async with BleakClient(address) as client:

        print(f"address   = {address}")
        print(f"char_uuid = {char_uuid}")

        print(f"Connected = {client.is_connected}")

        await client.start_notify(char_uuid, notification_handler)
        await asyncio.sleep( timeout_period ) # Wait for ?? secs to collect new state information
        await client.stop_notify(char_uuid)


if __name__ == "__main__":
    print(f'\nCOLOR = {COLOR}\n')
    asyncio.run(
        main(
            sys.argv[1] if len(sys.argv) > 1 else ADDRESS,
            sys.argv[2] if len(sys.argv) > 2 else CHARACTERISTIC_UUID,
        )
    )