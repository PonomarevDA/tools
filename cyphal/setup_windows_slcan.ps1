<#
    Run Next command in PowerShell first to enable executable scripts:
    Set-ExecutionPolicy RemoteSigned
    type: Yes
#>
$env:UAVCAN__CAN__IFACE = "slcan:COM16@1000000" # COM16 should be replaced with the exact name of your device.
$env:UAVCAN__CAN__MTU = "8"
$env:UAVCAN__CAN__BITRATE = "1000000 1000000"
$env:UAVCAN__NODE__ID = "127"
$env:CYPHAL_PATH = "C:\workspace\pycyphal\demo\public_regulated_data_types" #path should be replaced with the exact location of your compiled DSDL.