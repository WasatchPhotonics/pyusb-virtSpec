# Use this file to configure virtual devices. Set `CONNECTED_DEVICES` to be a list of VirtualDevice instances. VirtualDevice can be used to emulate any usb device, not just WP spectrometers.

# Some messages are easiest to handle by ignoring them, since we have no real firmware or bus to configure
NOOP = lambda *k, **kw: None

# Using this to create a plausible response to EEPROM request
from .eeprom_gen import EEPROM
eeprom = EEPROM()
eeprom.generate_write_buffers()

# show some fake noise in get_line's
from random import random

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

    def __init__(self):
        # populating some fields for Wasatch.PY
        self.dev = self
        self.idproduct = self.idProduct
        self.idvendor = self.idVendor

    def ctrl_transfer(self, dev_handle, bmRequestType, bRequest, wValue=0, wIndex=0, data_or_wLength = None, timeout = None):
        """ Here we pretend to be the device firmware """

        # REQUEST EEPROM
        if dev_handle == 0xc0 and bmRequestType == 0xff and bRequest == 0x1 and wIndex == 0x40:
            buf = eeprom.write_buffers[self._eeprom_page]
            self._eeprom_page += 1
            return buf

        # REQUEST FPGA COMPILATION OPTIONS
        if dev_handle == 0xc0 and bmRequestType == 0xff and bRequest == 0x4 and wIndex == 0x40:
            return [0xFFFF, 0xFF]

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
        " Lets just spit out a spectrum ! (tho this could be EEPROM, i think, depending on last ctrl_t) "

        if msgLen == 2048:

            # very simple simulated spectra
            # just to output anything on graph !

            # (pixel, counts)
            peaks = [(500,5000), (700, 3000), (200, 10000)]
            noise = 100

            # funky one-liner for spectra gen, sorry. Trying to wrap this up and move on 
            pixels = [int(sum([p[1]/(1+(x-p[0])**2) for p in peaks])+noise*random()) for x in range(1024)]
            lsb = [x&0xFFFF for x in pixels]
            msb = [(x>>16)&0x00FF for x in pixels]

            # funky one-liner to interleave arrays, see other places for a better example
            return sum(map(list, zip(lsb, msb)), start=[])
        else:
            return [0 for i in range(msgLen)] 

    class Ctx(Ignore):
        managed_claim_interface = NOOP
    _ctx = Ctx()


CONNECTED_DEVICES = [VirtualDevice()]
