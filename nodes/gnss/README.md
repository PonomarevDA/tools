# GPS_MAG_BARO


## Test gnss script

The following script automatically:

1. Downloads the latest required firmware and upload it to the target
2. Retrive the board data (software version, hardware, UID) and provides auto test of GNSS, Magnetometer and Barometer
3. Optionally, sends report to the printer (tested with XPRINTER XP-365B)

```bash
./nodes/gnss/test.sh --protocol cyphal # or dronecan
```

For details type `--help` option.
