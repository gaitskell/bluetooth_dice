# Scan for Bluetooth devices
# 220521 rg v1
#
# https://pypi.org/project/bleak/
#
#

import asyncio
from bleak import BleakScanner

async def main():
    devices = await BleakScanner.discover()
    for d in devices:
        print(d)

asyncio.run(main())
