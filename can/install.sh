#!/bin/bash

is_root="$(whoami)"
if [[ $is_root =~ "root" ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# Required for Github Action CI
if [[ $1 == "--yes" ]]; then
    FORCE_APT_INSTALL="-y"
fi

$SUDO apt-get install $FORCE_APT_INSTALL \
    can-utils \
    net-tools \
    iproute2

# Required for Github Action CI
kernel_release=$(uname -r)
if [[ $kernel_release == *azure ]]; then
    $SUDO apt-get install $FORCE_APT_INSTALL linux-modules-extra-$(uname -r)
fi
