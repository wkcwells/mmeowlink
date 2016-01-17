
# LICENSE

[![Join the chat at https://gitter.im/oskarpearson/mmeowlink](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/oskarpearson/mmeowlink?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

MMeowlink Copyright (C) 2015 Oskar Pearson and Ben West.
This program comes with ABSOLUTELY NO WARRANTY. See the LICENSE file
for more details.

# NB

Please note that this is not yet in a stable state! I'm running this project
with the [Release Early, Release Often](https://en.wikipedia.org/wiki/Release_early,_release_often)
methodology.

* You must agree to the LICENSE terms
* It does not (yet) have tests, and the code quality is not anywhere where I
  would like it to be.

# MMeowlink

MMeowlink acts as an OpenAPS driver. It allows you to replace the CareLink
USB device with a [MMCommander](https://github.com/jberian/mmcommander) stick.

This is based on the hard work done by Ben West for the [mmblelink](https://github.com/bewest/mmblelink)
project for the [RileyLink](https://github.com/ps2/rileylink).

# Wiki

Please see the Wiki for [Wiki](https://github.com/oskarpearson/mmeowlink/wiki) for
photos, setup instructions and more.

# Setup

As this is still a WIP, I don't have a Python package available yet. Install
it as follows:

    cd ~
    git clone https://github.com/oskarpearson/mmeowlink.git mmeowlink-source
    cd mmeowlink-source
    git checkout master
    sudo pip install -e .

## Add the vendor:

    openaps vendor add --path . mmeowlink.vendors.mmeowlink

This will create an entry like this in your openaps.ini:

    [vendor "mmeowlink.vendors.mmeowlink"]
    path = .
    module = mmeowlink.vendors.mmeowlink


## Remove any existing pump device

Note that you might need to delete any existing 'pump' device before running
the add, so as to disassociate the pump device from CareLink.

If you already have the loop running with CareLink, you should remove the
existing pump definition:

    openaps device remove pump

This will remove this section from your openaps.ini:

    [device "pump"]
    extra = pump.ini

## Add the new pump device

The parameter format is as follows:

    openaps device add pump mmeowlink <radio_type> <port> <serial_number_of_pump>

For example, if you're on an Edison with the subg_rfspy firmware, with pump
serial number 12345 your command would be:

    openaps device add pump mmeowlink subg_rfspy /dev/ttyMFD1 12345

Once run, this would appear in your openaps.ini file:

    [device "pump"]
    vendor = mmeowlink.vendors.mmeowlink
    extra = pump.ini

The pump.ini file would contain the following:

    [device "pump"]
    serial = 12345
    port = /dev/ttyMFD1
    radio_type = subg_rfspy

For the mmcommander hardware, replace 'subg_rfspy' with 'mmcommander'
