# Cyphal/CAN tools

A few Cyphal related scripts are collected here.

## PREPARATION

There are a few approaches here.

1. If you have a CAN-sniffer ([RL CAN-sniffer](https://docs.raccoonlab.co/guide/programmer_sniffer/) or [Zubax Babel](https://zubax.com/products/babel)) and you want a simple connection to your device, the recommended cross-platform way is to use [Python-CAN](https://python-can.readthedocs.io/en/stable/) [CAN over Serial / SLCAN](https://python-can.readthedocs.io/en/stable/interfaces/slcan.html) interface.

    On Linux you can simply run the following script:

    ```bash
    source cyphal/setup_linux_slcan.sh
    ```

    On Windows you can try [setup.ps1](https://gist.github.com/sainquake/7f06a2425ee54178633eac60f9002608) script.

2. If you have Linux, alternatively you can use [socketcan interface](https://python-can.readthedocs.io/en/stable/interfaces/socketcan.html). Unlike SLCAN, socketcan interface allows to share the same virtual CAN interface with multiple processes, so you run a few pycyphal scripts, yukon, yakut simultaniously.

    <details><summary>Click here for details how to use cyphal/init.sh script to setup CAN interface with socketcan on Linux</summary>

    cyphal/init.sh automatically:

    1. Create SLCAN based on CAN-sniffer or create virtual CAN inreface
    2. Configure environment variables if they are not already configured (`UAVCAN__CAN__IFACE`, `UAVCAN__CAN__MTU`, `UAVCAN__NODE__ID`, `YAKUT_PATH`)
    3. Compile DSDL based on public regulated data types and ds015

    Install dependencies:

    ```bash
    sudo apt-get install can-utils
    python3 -m pip install yakut
    ```

    Clone [PonomarevDA/tools](https://github.com/PonomarevDA/tools.git) repository and [OpenCyphal/public_regulated_data_types](https://github.com/OpenCyphal/public_regulated_data_types) in the same folder:

    ```bash
    git clone https://github.com/PonomarevDA/tools.git
    cd tools
    git clone https://github.com/OpenCyphal/public_regulated_data_types.git
    ```

    Let's say, your CAN-interface is not initialized yet. You can check it with `ifconfig`. You can delete it with `sudo ip link delete slcan0`. Normally, you don't need to delete it, but let's keep this command here just in case.

    If you want to create SLCAN based on a real CAN-sniffer such as [RaccoonLab CAN-sniffer and STM32 programmer](https://docs.raccoonlab.co/guide/programmer_sniffer/) or [Zubax Babel-Babel](https://shop.zubax.com/products/zubax-babel-babel-all-in-one-debugger-for-robotics-drone-development), you can type:

    ```bash
    source cyphal/init.sh -i slcan0 -n 127 # All options in the command are actually defaults, so you can skip them
    ```

    If you want to run it without a real CAN-sniffer hardware, you can run the following command:

    ```bash
    source cyphal/init.sh -i slcan0 -n 127 -v
    ```

    ![](https://github.com/PonomarevDA/tools/blob/docs/assets/cyphal/cyphal_init.gif?raw=true)

    For additional usage details please type:

    ```bash
    source cyphal/init.sh --help
    ```

    For usage example without a real hardware you can also check the workflows:
    - [.github/workflows/cyphal_init.yml](../.github/workflows/cyphal_init.yml)
    - [.github/workflows/specification_checker.yml](../.github/workflows/specification_checker.yml)

    </details>
