# Scan for Bluetooth devices
# 220521 rg v1
#
# https://pypi.org/project/bleak/
#
#

import asyncio
from bleak import BleakClient
from bleak import BleakScanner

address = ""
# NOT USED
#address = "E3:9E:7C:46:41:F8"
#MODEL_NBR_UUID = "D0CC6BEC-3905-874A-CC20-5F94225A7D28"
#address = MODEL_NBR_UUID
#address = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'

async def main(address):

    print( '\n\nSCANNING for any GoDice' )
    devices = await BleakScanner.discover()
    flag = True
    for d in devices:
        if flag and "GoDice" in d.name :
            print("\n--------------------------------")
            print(d)
            type(d)
            print( dir(d) )
            print('Name' , d.name )
            print( 'Dice?:' , 'GoDice' in d.name )
            print('Address' , d.address )
            print('Details' , d.details )
            print('Meta' , d.metadata )
            print('RSSI' , d.rssi )

            flag = True
#        if "GoDice" in d:
#            print(d)

"""
    if 0:
        print( '\n\nACCESS DEVICE - doesnt work yet for GoDice' )

        async with BleakClient(address) as client:
            model_number = await client.read_gatt_char(MODEL_NBR_UUID)
            print("Model Number: {0}".format("".join(map(chr, model_number))))
"""



asyncio.run(main(address))
