# Use this file to configure virtual devices. Set `CONNECTED_DEVICES` to be a list of VirtualDevice instances. VirtualDevice can be used to emulate any usb device, not just WP spectrometers.

# Some messages are easiest to handle by ignoring them, since we have no real firmware or bus to configure
NOOP = lambda *k, **kw: None

# Using this to create a plausible response to EEPROM request
from .eeprom_gen import EEPROM

# show some fake noise in get_line's
from random import random
import os

# get spectra from CSV
spectrum = []
with open(os.path.dirname(__file__) + os.sep + "target.csv", "rt") as target:
    
    # skip header
    L = target.readline()
    
    L = target.readline()
    while L:
        Pixel,Wavenumber,Processed,Raw,Dark = L.split(",")
        spectrum.append(float(Processed))
        L = target.readline()

class Ignore:
    def __getattr__(self, a):
        print("WARNING: UNIMPLEMENTED ATTRIBUTE", a)

        # by default return a NOOP function, so we can get the ball rolling
        return NOOP

class VirtualDevice(Ignore):

    # --- DATA ---

    # see DeviceFinderUSB.py for a list of WP supported VIDs
    idVendor = 0x24aa # Wasatch Photonics
    idProduct = 0x1000 # Hamamatsu Silicon

    product = "Wasatch Photonics Virtual Hamamatsu Silicon"
    serial_number = "0x000000"

    address = 0 # only used in logs
    bus = 0

    # END DATA ---

    set_configuration = NOOP

    _eeprom_page = 0

    def __init__(self, custom_eeprom=None):
        # populating some fields for Wasatch.PY
        self.dev = self
        self.idproduct = self.idProduct
        self.idvendor = self.idVendor

        if custom_eeprom:
            self.eeprom = custom_eeprom
        else:
            self.eeprom = EEPROM()

        self.eeprom.generate_write_buffers()

    def ctrl_transfer(self, dev_handle, bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength = None, timeout = None):
        """ Here we pretend to be the device firmware """

        # REQUEST EEPROM
        if dev_handle == 0xc0 and bmRequestType == 0xff and bRequest == 0x1 and wIndex == 0x40:
            buf = self.eeprom.write_buffers[self._eeprom_page]
            self._eeprom_page += 1
            return buf

        # REQUEST FPGA COMPILATION OPTIONS
        if dev_handle == 0xc0 and bmRequestType == 0xff and bRequest == 0x4 and wIndex == 0x40:
            return [0xFF, 0xFF]

        # REQUEST LINE LENGTH (pid=0x1000)
        if dev_handle == 0xc0 and bmRequestType == 0xff and bRequest == 0x3 and wValue == 0x0 and wIndex == 0x40 and self.idProduct == 0x1000:
            return [0x00, 0x04]

        # log unhandled ctrl messages 
        def display(k):
            if type(k) == int:
                return hex(k)
            if k is None:
                return None
            else:
                return str(k) 
        print("unhandled ctrl_t:", 'dev_handle ==', display(dev_handle), 'and bmRequestType ==', display(bmRequestType), 'and bRequest ==', display(bRequest), 'and wValue ==', display(wValue), 'and wIndex ==', display(wIndex), 'and data_or_wLength ==', display(data_or_wLength), 'and timeout ==',timeout)

    def read(self, endpoint, msgLen, timeout):
        """ Lets just spit out a spectrum ! (tho this could be EEPROM, i think, depending on last ctrl_t)
        No EEPROM is not from bulk read"""

        if msgLen in [1024, 2048]:

            # very simple simulated spectra
            # just to output anything on graph !

            # (pixel, counts)
            peaks = [(500,5000), (700, 3000), (200, 10000)]
            noise = 100

            # using spectra from target.csv
            pixels = [0 for i in range(300)]+[int(spectrum[x]+noise*random()) for x in range(1952-300)]
            lsb = [x&0xFFFF for x in pixels]
            msb = [(x>>16)&0x00FF for x in pixels]

            # funky one-liner to interleave arrays, see other places for a better example
            return sum(map(list, zip(lsb, msb)), start=[])
        else:
            return [0 for i in range(msgLen)] 

    class Ctx(Ignore):
        managed_claim_interface = NOOP
    _ctx = Ctx()


FX2 = VirtualDevice()

eeprom_xs = EEPROM()
eeprom_xs.model = 'Test XS'
XS = VirtualDevice(eeprom_xs)
XS.pid = 0x4000
XS.has_battery = True
XS.has_laser = True

CONNECTED_DEVICES = [XS]
