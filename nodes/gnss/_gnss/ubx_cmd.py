#!/usr/bin/env python3
# https://content.u-blox.com/sites/default/files/documents/u-blox-F9-HPG-1.32_InterfaceDescription_UBX-22008968.pdf

from pyubx2 import UBXMessage, SET

class UbloxCommands:
    def __init__(self) -> None:
        pass

    def reset(self):
        return [0xB5, 0x62, 0x06, 0x09, 0x0D, 0x00, 0xFF, 0xFF, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x03, 0x1B,
                0x9A]

    def change_baudrate_m8(self, baudrate):
        """
        UBX-CFG-PRT
        M8  Tested ok
        F9P Deprecated. Use UBX-CFG-VALSET, UBX-CFGVALGET, UBX-CFG-VALDEL instead
        """
        return self._generate_set_command('CFG', 'CFG-PRT', portID=1, reserved0=0, enable=0, pol=0, pin=0, thres=0, charLen=3, parity=4, nStopBits=0, baudRate=baudrate, inUBX=1, inNMEA=1, inRTCM=0, inRTCM3=1, outUBX=1, outNMEA=1, outRTCM3=1, extendedTxTimeout=0, reserved1=0)

    def change_baudrate_f9p(self, baudrate):
        """
        UBX-CFG-UART1
        M8  Not supported
        """
        header_4_bytes = b"\x00\x05\x00\x00"
        config_data_key_id = b"\x01\x00\x52\x40"
        config_data_value = self._baudrate_to_bytes_array(baudrate)

        return self._generate_set_command(
            "CFG",
            "CFG-VALSET",
            payload=header_4_bytes + config_data_key_id + config_data_value)

    def save_all_command(self):
        """
        UBX-CFG-CFG
        M8  Tested ok
        F9P Old functionality of this message is not available in protocol
            versions greater than 23.01. Use UBX-CFGVALSET, UBX-CFG-VALGET,
            UBX-CFG-VALDEL instead.
        """
        return self._generate_set_command("CFG", "CFG-CFG", saveMask=b"\x1f\x1f\x00\x00", devBBR=1, devFlash=1)

    @staticmethod
    def _generate_set_command(ubxClass, ubxID, **params) -> list:
        return list(UBXMessage(ubxClass, ubxID, SET, **params).serialize())

    @staticmethod
    def _baudrate_to_bytes_array(baudrate):
        return bytes([(baudrate >> 0)  % 256,
                      (baudrate >> 8)  % 256,
                      (baudrate >> 16) % 256,
                      (baudrate >> 24) % 256])


    def generate_val_set_command():
        pass

def main():
    generator = UbloxCommands()

    print("Factory reset")
    print(generator.reset())
    print("")

    print("Save config:")
    print(generator.save_all_command())
    print("")

    print("Change baudrate M8 to 921600:")
    print(generator.change_baudrate_m8(921600))
    print("")

    print("Change baudrate F9P to 921600:")
    print(generator.change_baudrate_f9p(921600))

if __name__ == "__main__":
    main()
