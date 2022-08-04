"""
Source: https://github.com/hbldh/bleak/blob/master/examples/service_explorer.py
220521 rg v1
220522 rg v2

Service Explorer
----------------

An example showing how to access and print out the services, characteristics and
descriptors of a connected GATT server.

Created on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""

import sys
import platform
import asyncio
import logging

from bleak import BleakClient

logger = logging.getLogger(__name__)

#ADDRESS = (
#    "24:71:89:cc:09:05"
#    if platform.system() != "Darwin"
#    else "B9EA5233-37EF-4DD6-87A8-2A875E821C46"
#)

# DIE GoDice
ADDRESS = "D0CC6BEC-3905-874A-CC20-5F94225A7D28" # RED UUID - this works !!
ADDRESS = "9F38B8FD-4189-47C6-7E65-84C208ED9B3E" # BLUE" \

async def main(address):

    logger.info( f"Called with address = {address}" )


    async with BleakClient(address) as client:
        logger.info(f"Connected: {client.is_connected}")
        logger.info(f"{client.services}")
        # logger.info(f"{await client.get_services()}")

        logger.info(f"[List dir(client)] {dir(client)}")

        logger.info(f"[List client.services] {client.services}")
        logger.info(f"[List dir(client.services)] {dir(client.services)}")

        for service in client.services:

            logger.info(f"++++++++++++++++++++++++++")
            logger.info(f"[Service] {service}")

            for char in service.characteristics:

                logger.info(f"-------------------------")
                logger.info(f"[List Chracteristics] {dir(char)}")

                if "read" in char.properties:
                    try:
                        value = bytes(await client.read_gatt_char(char.uuid))

                        logger.info(
                            f"\t[Read Val Characteristic] {char} ({','.join(char.properties)}), Value: {value}"
                        )

                    except Exception as e:
                        logger.error(
                            f"\t[Read Err Characteristic] {char} ({','.join(char.properties)}), Value: {e}"
                        )

                else:
                    value = None
                    logger.info(
                        f"\t[None Characteristic] {char} ({','.join(char.properties)}), Value: {value}"
                    )


                for descriptor in char.descriptors:
                    try:
                        value = bytes(
                            await client.read_gatt_descriptor(descriptor.handle)
                        )
                        logger.info(f"\t\t[Val Descriptor] {descriptor}) | Value: {value}")
                        logger.info(f"\t\t[Len Descriptor] {descriptor}) | Value: {len(value)}")

                    except Exception as e:
                        logger.error(f"\t\t[Err Descriptor] {descriptor}) | Value: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(sys.argv[1] if len(sys.argv) == 2 else ADDRESS))
