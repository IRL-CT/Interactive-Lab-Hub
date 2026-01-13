# SPDX-FileCopyrightText: 2017 Michael McWethy for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`APDS9960`
====================================================

Driver class for the APDS9960 board.  Supports gesture, proximity, and color
detection.

* Author(s): Michael McWethy, Erik Hess

Implementation Notes
--------------------

**Hardware:**

* Adafruit `APDS9960 Proximity, Light, RGB, and Gesture Sensor
  <https://www.adafruit.com/product/3595>`_ (Product ID: 3595)

* Adafruit `CLUE
  <https://www.adafruit.com/product/4500>`_ (Product ID: 4500)

* Adafruit `Feather nRF52840 Sense
  <https://www.adafruit.com/product/4516>`_ (Product ID: 4516)

* Adafruit `Proximity Trinkey
  <https://www.adafruit.com/product/5022>`_ (Product ID: 5022)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

import time

from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const

try:
    # Only used for typing
    from typing import Tuple

    from busio import I2C
except ImportError:
    pass

__version__ = "3.1.16"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_APDS9960.git"

# Only one address is possible for the APDS9960, no alternates are available
_APDS9960_I2C_ADDRESS = const(0x39)
_DEVICE_IDS = (const(0xAB), const(0xA8))

# APDS9960_RAM        = const(0x00)
_APDS9960_ENABLE = const(0x80)
_APDS9960_ATIME = const(0x81)
# _APDS9960_WTIME      = const(0x83)
# _APDS9960_AILTIL     = const(0x84)
# _APDS9960_AILTH      = const(0x85)
# _APDS9960_AIHTL      = const(0x86)
# _APDS9960_AIHTH      = const(0x87)
_APDS9960_PILT = const(0x89)
_APDS9960_PIHT = const(0x8B)
_APDS9960_PERS = const(0x8C)
# _APDS9960_CONFIG1    = const(0x8D)
# _APDS9960_PPULSE = const(0x8E)
_APDS9960_CONTROL = const(0x8F)
# _APDS9960_CONFIG2 = const(0x90)
_APDS9960_ID = const(0x92)
_APDS9960_STATUS = const(0x93)
_APDS9960_CDATAL = const(0x94)
# _APDS9960_CDATAH     = const(0x95)
# _APDS9960_RDATAL     = const(0x96)
# _APDS9960_RDATAH     = const(0x97)
# _APDS9960_GDATAL     = const(0x98)
# _APDS9960_GDATAH     = const(0x99)
# _APDS9960_BDATAL     = const(0x9A)
# _APDS9960_BDATAH     = const(0x9B)
_APDS9960_PDATA = const(0x9C)
# _APDS9960_POFFSET_UR = const(0x9D)
# _APDS9960_POFFSET_DL = const(0x9E)
# _APDS9960_CONFIG3    = const(0x9F)
_APDS9960_GPENTH = const(0xA0)
_APDS9960_GEXTH = const(0xA1)
_APDS9960_GCONF1 = const(0xA2)
_APDS9960_GCONF2 = const(0xA3)
# _APDS9960_GOFFSET_U  = const(0xA4)
# _APDS9960_GOFFSET_D  = const(0xA5)
# _APDS9960_GOFFSET_L  = const(0xA7)
# _APDS9960_GOFFSET_R  = const(0xA9)
_APDS9960_GPULSE = const(0xA6)
# _APDS9960_GCONF3 = const(0xAA)
_APDS9960_GCONF4 = const(0xAB)
_APDS9960_GFLVL = const(0xAE)
_APDS9960_GSTATUS = const(0xAF)
# _APDS9960_IFORCE     = const(0xE4)
# _APDS9960_PICLEAR    = const(0xE5)
# _APDS9960_CICLEAR    = const(0xE6)
_APDS9960_AICLEAR = const(0xE7)
_APDS9960_GFIFO_U = const(0xFC)
# APDS9960_GFIFO_D    = const(0xFD)
# APDS9960_GFIFO_L    = const(0xFE)
# APDS9960_GFIFO_R    = const(0xFF)

_BIT_MASK_ENABLE_EN = const(0x01)
_BIT_MASK_ENABLE_COLOR = const(0x02)
_BIT_MASK_ENABLE_PROX = const(0x04)
_BIT_MASK_ENABLE_PROX_INT = const(0x20)
_BIT_MASK_ENABLE_GESTURE = const(0x40)
_BIT_MASK_STATUS_AVALID = const(0x01)
_BIT_MASK_STATUS_GINT = const(0x04)
_BIT_MASK_GSTATUS_GFOV = const(0x02)
_BIT_MASK_GCONF4_GFIFO_CLR = const(0x04)

_BIT_POS_PERS_PPERS = const(4)
_BIT_MASK_PERS_PPERS = const(0xF0)

_BIT_POS_CONTROL_AGAIN = const(0)
_BIT_MASK_CONTROL_AGAIN = const(3)

_BIT_POS_CONTROL_PGAIN = const(2)
_BIT_MASK_CONTROL_PGAIN = const(0x0C)

_BIT_POS_GCONF2_GGAIN = const(5)
_BIT_MASK_GCONF2_GGAIN = const(0x60)


class APDS9960:
    """
    Provide basic driver services for the APDS9960 breakout board

    :param ~busio.I2C i2c: The I2C bus the APDS9960 is connected to
    :param int rotation: Rotation of the device. Defaults to :const:`0`
    :param bool reset: If true, reset device on init. Defaults to :const:`True`
    :param bool set_defaults: If true, set sensible defaults on init. Defaults to :const:`True`


    **Quickstart: Importing and using the APDS9960**

        Here is an example of using the :class:`APDS9960` class.
        First you will need to import the libraries to use the sensor

        .. code-block:: python

            import board
            from adafruit_apds9960.apds9960 import APDS9960

        Once this is done you can define your `board.I2C` object and define your sensor object

        .. code-block:: python

            i2c = board.I2C()   # uses board.SCL and board.SDA
            apds = APDS9960(i2c)

        Now you have access to the :attr:`apds.proximity_enable` and :attr:`apds.proximity`
        attributes

        .. code-block:: python

            apds.proximity_enable = True
            proximity = apds.proximity

        .. note:: There is no ``address`` argument because the APDS-9960 only has one address and
           doesn't offer any option to configure alternative addresses.
    """

    def __init__(
        self, i2c: I2C, *, rotation: int = 0, reset: bool = True, set_defaults: bool = True
    ):
        self.rotation = rotation

        self.buf129 = None  # Gesture FIFO buffer, only instantiated if needed
        self.buf4 = None  # Gesture data processing buffer, only instantiated if needed
        self.buf2 = bytearray(2)  # I2C communication buffer

        self.i2c_device = I2CDevice(i2c, _APDS9960_I2C_ADDRESS)

        if self._read8(_APDS9960_ID) not in _DEVICE_IDS:
            raise RuntimeError()

        if reset:
            # Disable prox, gesture, and color engines
            self.enable_proximity = False
            self.enable_gesture = False
            self.enable_color = False

            # Reset basic config registers to power-on defaults
            self.proximity_interrupt_threshold = (0, 0, 0)
            self._write8(_APDS9960_GPENTH, 0)
            self._write8(_APDS9960_GEXTH, 0)
            self._write8(_APDS9960_GCONF1, 0)
            self._write8(_APDS9960_GCONF2, 0)
            self._write8(_APDS9960_GCONF4, 0)
            self._write8(_APDS9960_GPULSE, 0)
            self._write8(_APDS9960_ATIME, 255)
            self._write8(_APDS9960_CONTROL, 0)

            # Clear all non-gesture interrupts
            self.clear_interrupt()

            # Clear gesture FIFOs and interrupt
            self._set_bit(_APDS9960_GCONF4, _BIT_MASK_GCONF4_GFIFO_CLR, True)

            # Disable sensor and all functions/interrupts
            self._write8(_APDS9960_ENABLE, 0)
            time.sleep(0.025)  # Sleeping could take at ~2-25 ms if engines were looping

            # Re-enable sensor and wait 10ms for the power on delay to finish
            self.enable = True
            time.sleep(0.010)

        if set_defaults:
            # Trigger proximity interrupt at >= 5, PPERS: 4 cycles
            self.proximity_interrupt_threshold = (0, 5, 4)
            # Enter gesture engine at >= 5 proximity counts
            self._write8(_APDS9960_GPENTH, 0x05)
            # Exit gesture engine if all counts drop below 30
            self._write8(_APDS9960_GEXTH, 0x1E)
            # GEXPERS: 2 (4 cycles), GEXMSK: 0 (default) GFIFOTH: 2 (8 datasets)
            self._write8(_APDS9960_GCONF1, 0x82)
            # GGAIN: 2 (4x), GLDRIVE: 100 mA (default), GWTIME: 1 (2.8ms)
            self._write8(_APDS9960_GCONF2, 0x41)
            # GPULSE: 5 (6 pulses), GPLEN: 2 (16 us)
            self._write8(_APDS9960_GPULSE, 0x85)
            # ATIME: 256 (712ms color integration time, max count of 65535)
            self.color_integration_time = 256
            # AGAIN: 1 (4x color gain)
            self.color_gain = 1

    ## BOARD
    @property
    def enable(self) -> bool:
        """If ``True``, the sensor is enabled.

        If set to ``False``, the sensor will enter a low-power sleep state

        When enabled, the sensor's state machine will run through the following steps in sequence,
        repeating from the top after all states are run through.

        #. **Idle State**

            - Will only remain in this state if all three sense engines are disabled.

        #. **Proximity Engine** *(if enabled)*

            - Will only run if `enable_proximity` is ``True``.
            - Will run once, storing fresh data in the sensor's proximity data registers. If
              proximity data is is lower than or exceeds the configured proximity thresholds an
              internal persistence is incremented on each run as well.

        #. **Gesture Engine** *(if enabled)*

            - Will only run if `enable_gesture` is ``True`` and if entry threshold of `proximity`
              is greater or equal to the gesture proximity entry threshold of 5 counts.
            - Will continuously loop, storing new results in the sensor's gesture FIFO buffers,
              until one of four conditions occur.

                - Exit threshold is met. *(all gesture measurements <= 30 counts)*
                - The gesture engine or sensor are disabled. *(`enable_gesture` or `enable`
                  properties are set to ``False``)*
                - The sensor is re-initalized by the driver
                - The sensor is power cycled

        #. **Wait Timer** *(set to 0 by default)*

            - This driver does not set or make available the ``WAIT`` or ``WLONG`` registers that
              control this function and, on intialization, leaves the timer at its power-on default
              state of ``0``, effectively disabling this timer.

        #. **Color/Light Engine** *(if enabled)*

            - Will run start if `enable_color` is ``True``.
            - Will run once, storing fresh data in the sensor's color data registers on each run.

        .. note:: Waking the sensor from its sleep state takes at least 7 ms. Disabling the sensor
           and entering a sleep state can take as little as 2.78 ms, more typically about 25 ms, or
           potentially quite a bit longer depending on what engines were enabled and what state was
           active at the time the disable command was received.

        .. hint:: When in a sleep state the sensor's power usage drops to as little as 1-10 uA,
           compared as much as 790 uA of power usage when enabled with proximity and/or gesture
           engines running. While in a sleep state, the sensor will still listen for and respond
           to I2C communication which can lead to minor increases in power usage.
        """
        return self._get_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_EN)

    @enable.setter
    def enable(self, value: bool) -> None:
        self._set_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_EN, value)

    ## Proximity Properties
    @property
    def enable_proximity(self) -> bool:
        """If ``True``, the sensor's proximity engine is enabled."""
        return self._get_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_PROX)

    @enable_proximity.setter
    def enable_proximity(self, value: bool) -> None:
        self._set_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_PROX, value)

    @property
    def enable_proximity_interrupt(self) -> bool:
        """If ``True``, the internal proximity interrupt asserts the sensor's interrupt pin.

        Internal proximity interrupt triggering is configured via `proximity_interrupt_threshold`.

        .. tip:: Using this interrupt will require attaching the sensor's ``INT`` pin to an
           available digital I/O with an internal or external pull-up resistor.

           For boards with built-in sensors the pin is likely already mapped within ``board``.

            .. csv-table::
               :header: "Board", "Pin Mapping"

               "CLUE", "``board.PROXIMITY_LIGHT_INTERRUPT``"
               "Feather nRF52840 Sense", "``board.PROXIMITY_LIGHT_INTERRUPT``"
               "Proximity Trinkey", "``board.INTERRUPT``"
        """
        return self._get_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_PROX_INT)

    @enable_proximity_interrupt.setter
    def enable_proximity_interrupt(self, value: bool) -> None:
        self._set_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_PROX_INT, value)

    @property
    def proximity_interrupt_threshold(self) -> Tuple[int, int, int]:
        """Tuple representing proximity engine low/high threshold and persistence, which determine
        when the sensor's proximity interrupt is asserted.

        1. Low Threshold (``PILT``)
        2. High Threshold (``PIHT``) *(optional)*
        3. Proximity Persistence (``PERS<PPERS>``) *(optional)*

        The first two items are the "low threshold" and "high threshold" values. These can be set
        to any number between ``0`` and ``255``. If the proximity value is lower than the low
        threshold or higher than the high threshold for enough cycles, an interrupt will be
        asserted.

        The third item is the "persistence" value. This can be set to any value between ``0`` to
        ``15``. This represents the number of 2.78 ms out-of-threshold cycles to wait for before
        asserting the interrupt. This is basically a filter to prevent premature/false interrupts.

        .. hint:: For example, setting a low threshold of ``0`` and a high threshold of ``5`` will
           cause the interrupt to be asserted very early when an object **enters the sensor's line
           of sight**. Coversely, a low threshold of ``5`` and a high threshold of ``255`` will
           trigger an interrupt only if an object **is removed from the sensor's line of sight**.

        .. hint:: Tuning the persistence value can be useful in some use cases but for most
           situations the driver's default value of 4 should provide for stable results without
           much delay in interrupt triggering.
        """
        return (
            self._read8(_APDS9960_PILT),
            self._read8(_APDS9960_PIHT),
            self._get_bits(_APDS9960_PERS, _BIT_POS_PERS_PPERS, _BIT_MASK_PERS_PPERS),
        )

    @proximity_interrupt_threshold.setter
    def proximity_interrupt_threshold(self, setting_tuple: Tuple[int, ...]) -> None:
        if setting_tuple and 0 <= setting_tuple[0] <= 255:
            self._write8(_APDS9960_PILT, setting_tuple[0])
        if len(setting_tuple) > 1 and 0 <= setting_tuple[0] <= 255:
            self._write8(_APDS9960_PIHT, setting_tuple[1])
        persist = 4  # default 4
        if len(setting_tuple) > 2 and 0 <= setting_tuple[0] <= 15:
            persist = min(setting_tuple[2], 15)
            self._set_bits(_APDS9960_PERS, _BIT_POS_PERS_PPERS, _BIT_MASK_PERS_PPERS, persist)

    @property
    def proximity_gain(self) -> int:
        """Proximity sensor gain value.

        This sets the gain multiplier for the ADC during proximity engine operations.

        .. csv-table::
           :header: "``proximity_gain``", "Gain Multiplier", "Note"

           0, "1x", "Power-on Default"
           1, "2x", ""
           2, "4x", ""
           3, "8x", ""
        """
        return self._get_bits(_APDS9960_CONTROL, _BIT_POS_CONTROL_PGAIN, _BIT_MASK_CONTROL_PGAIN)

    @proximity_gain.setter
    def proximity_gain(self, value: int) -> None:
        self._set_bits(_APDS9960_CONTROL, _BIT_POS_CONTROL_PGAIN, _BIT_MASK_CONTROL_PGAIN, value)

    def clear_interrupt(self) -> None:
        """Clears all non-gesture interrupts.

        This includes all of the following internal interrupts:

        * **Proximity Interrupt** (``PINT``)
        * **Proximity Saturation Interrupt** (``STATUS<PGSAT>``)
        * **Color/Light Interrupt** (``STATUS<AINT>``)
        * **Color/Light Clear Saturation Interrupt** (``STATUS<CPSAT>``)
        """
        self._writecmdonly(_APDS9960_AICLEAR)

    ## Gesture Properties
    @property
    def enable_gesture(self) -> bool:
        """If ``True``, the sensor's gesture engine is enabled.

        .. note:: The gesture engine will only operate if `enable_proximity` is also set to ``True``
        """
        return self._get_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_GESTURE)

    @enable_gesture.setter
    def enable_gesture(self, value: bool) -> None:
        self._set_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_GESTURE, value)

    @property
    def gesture_gain(self) -> int:
        """Gesture mode gain value.

        This sets the gain multiplier for the ADC during gesture engine operations.

        .. csv-table::
           :header: "``gesture_gain``", "Gain Multiplier", "Note"

           0, "1x", "Power-on Default"
           1, "2x", ""
           2, "4x", "Driver Default"
           3, "8x", ""
        """
        return self._get_bits(_APDS9960_GCONF2, _BIT_POS_GCONF2_GGAIN, _BIT_MASK_GCONF2_GGAIN)

    @gesture_gain.setter
    def gesture_gain(self, value: int) -> None:
        self._set_bits(_APDS9960_GCONF2, _BIT_POS_GCONF2_GGAIN, _BIT_MASK_GCONF2_GGAIN, value)

    @property
    def rotation(self) -> int:
        """Clock-wise offset to apply to gesture results.

        Acceptable values are ``0``, ``90``, ``180``, ``270``.

        .. tip:: The sensor's "top" end is the one with the larger of the two circular windows.

            Some rotation examples for various boards with the APS-9960 built in:

            .. csv-table::
               :header: "Board", "Rotation"

               "CLUE", 270
               "Feather nRF52840 Sense, with USB port to the left", 270
               "Proximity Trinkey, plugged into right-side laptop USB port", 270
               "Proximity Trinkey, plugged into left-side laptop USB port", 90
        """
        return self._rotation

    @rotation.setter
    def rotation(self, new_rotation: int) -> None:
        if new_rotation in {0, 90, 180, 270}:
            self._rotation = new_rotation
        else:
            raise ValueError("Rotation value must be one of: 0, 90, 180, 270")

    ## Color/Light Properties
    @property
    def enable_color(self) -> bool:
        """If ``True``, the sensor's color/light engine is enabled"""
        return self._get_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_COLOR)

    @enable_color.setter
    def enable_color(self, value: bool) -> None:
        self._set_bit(_APDS9960_ENABLE, _BIT_MASK_ENABLE_COLOR, value)

    @property
    def color_data_ready(self) -> int:
        """Color data ready flag.

        Returns ``0`` if no new data is ready, ``1`` if new data is ready.

        This flag is reset when `color_data` is read."""
        return self._get_bit(_APDS9960_STATUS, _BIT_MASK_STATUS_AVALID)

    @property
    def color_gain(self) -> int:
        """Color/light sensor gain value.

        This sets the gain multiplier for the ADC during color/light engine operations.

        .. csv-table::
           :header: "``color_gain``", "Gain Multiplier", "Note"

           0, "1x", "Power-on Default"
           1, "4x", "Driver Default"
           2, "16x", ""
           3, "64x", ""

        .. tip:: To get useful, predictable `color_data` results it is important to tune this,
           along with `color_integration_time`, to accommodate different lighting conditions, sensor
           placements, material transparencies, expected object reflectivity, and environmental
           conditions.

           For instance, measuring color of objects close to the sensor with bright, nearby
           illumination (such as the white LEDs on the `Adafruit CLUE
           <https://www.adafruit.com/product/4500>`_) may work well with a `color_gain` of ``0``
           and a `color_integration_time` of ``72`` or lower.

           However, measuring the intensity and color temperature of ambient light through
           difusion glass or plastic is likely to require experimenting with a wide range of
           integration time and gain settings before useful data can be obtained."""
        return self._get_bits(_APDS9960_CONTROL, _BIT_POS_CONTROL_AGAIN, _BIT_MASK_CONTROL_AGAIN)

    @color_gain.setter
    def color_gain(self, value: int) -> None:
        self._set_bits(_APDS9960_CONTROL, _BIT_POS_CONTROL_AGAIN, _BIT_MASK_CONTROL_AGAIN, value)

    @property
    def color_integration_time(self) -> int:
        """Color/light sensor gain.

        Represents the integration time in number of 2.78 ms cycles for the ADC during color/light
        engine operations. This also effectively sets the maxmium value returned for each channel
        by `color_data`.

        .. csv-table::
           :header: "``color_integration_time``", "Time", "Max Count", "Note"

           1, "2.78 ms", 1025, "Power-on Default"
           10, "27.8 ms", 10241, ""
           37, "103 ms", 37889, ""
           72, "200 ms", 65535, ""
           256, "712 ms", 65535, "Driver Default"
        """
        return 256 - self._read8(_APDS9960_ATIME)

    @color_integration_time.setter
    def color_integration_time(self, value: int) -> None:
        self._write8(_APDS9960_ATIME, 256 - value)

    ## PROXIMITY
    @property
    def proximity(self) -> int:
        """Proximity sensor data.

        The proximity engine returns a number between ``0`` and ``255`` which represents the
        intensity of the reflected IR light detected from the sensor's internal LEDs, which pulse
        continously during proximity engine operation.

        A value of ``0`` indicates no reflected IR light was received. This typically indicates
        that no object(s) were in the sensor's line of sight and within detectable range of its IR
        LED pulses.

        A value of ``255`` indicates that the maximum detectable amount of reflected IR light was
        received. This typically indicates that an object was detected very close to the sensor.

        .. caution:: Will always return ``0`` if `enable_proximity` is not set ``True``.

        .. note:: The sensor itself offers a very wide variety of configuration options for tuning
           the proximity engine, such as the LEDs (pulse count/length, drive power) and the
           photosensors (gain, offsets, masking). However, this driver does not make those readily
           available in order to keep file size and memory footprint to a minimum, which is
           critical for its use on more constrained platforms.
        """
        return self._read8(_APDS9960_PDATA)

    ## GESTURE DETECTION
    def gesture(self) -> int:
        """Gesture sensor data.

        This checks the sensor for new gesture engine results and, if they are present, retrieves
        and processes the results to determine what, if any, gesture can be deduced from the sensor
        data.

        Returns a gesture code indicating the direction of the gesture. Before returning the code,
        the `rotation` value is used to "rotate" the result as intended.

        .. csv-table::
           :header: "Code", "Direction"

            0, "No gesture detected"
            1, "Up"
            2, "Down"
            3, "Left"
            4, "Right"

        .. caution:: Will always return ``0`` if `enable_proximity` and `enable_gesture` are not set
           to ``True``.

        The data returned by the sensor is a continuous stream of four proximtiy measurements
        constrained to up/down/left/right dimensions by using four directionally-aligned sensors.
        The sensor itself doesn't include any logic to determine the gesture, leaving that work to
        the implementer.

        This driver implements an algorithm that reliably detects simple gestures in most scenarios
        while remaining small and efficient enough to work within the resource constraints of as
        many CircuitPython boards/platforms as possible.

        .. tip:: Detecting gestures with this driver's algorithm requires actively, continously
           polling for a gesture, with as little time as possible between `gesture()` calls. Even
           with continous polling, however, its possible that gestures may go undetected by
           `gesture()` calls if they occurred between or on the edges of `gesture()` method
           execution.

        .. warning:: If gesture data becomes available from the sensor, this driver will
           continuously pull in that new data and analyze it until the sensor's gesture engine
           exits and the sensor's FIFO buffers are clear. This allows for much more reliable
           gesture detection by comparing the "first" to the "last" detected state at the cost of
           blocking until the FIFOs are all clear. This will only happen if all four gesture values
           drop below ``30``.

           As a result, if an object is close to the sensor when `gesture()` is called, the method
           will not return until it moves away.

        .. note:: The sensor itself offers a very wide variety of configuration options for tuning
           the gesture engine, such as the LEDs (pulse count/length, drive power), the photosensors
           (gain, offsets, masking), the gesture engine's entry/exit thresholds, wait time, and
           more. However, this driver does not make those readily available in order to keep file
           size and memory footprint to a minimum, which is critical for its use on more
           constrained platforms."""
        # If FIFOs have overflowed we're already way too late, so clear those FIFOs and wait
        if self._get_bit(_APDS9960_GSTATUS, _BIT_MASK_GSTATUS_GFOV):
            self._set_bit(_APDS9960_GCONF4, _BIT_MASK_GCONF4_GFIFO_CLR, True)
            wait_cycles = 0
            # Don't wait forever though, just enough to see if a gesture is happening
            while not self._get_bit(_APDS9960_STATUS, _BIT_MASK_STATUS_GINT) and wait_cycles <= 30:
                time.sleep(0.003)
                wait_cycles += 1

        # Only start retrieval if there are datasets to retrieve
        frame = []
        datasets_available = self._read8(_APDS9960_GFLVL)
        if self._get_bit(_APDS9960_STATUS, _BIT_MASK_STATUS_GINT) and datasets_available > 0:
            if not self.buf129:
                self.buf129 = bytearray(129)

            buffer = self.buf129
            buffer[0] = _APDS9960_GFIFO_U

            if not self.buf4:
                self.buf4 = bytearray(4)

            buffer_dataset = self.buf4

            # Retrieve new data until our FIFOs are truly empty
            while True:
                dataset_count = self._read8(_APDS9960_GFLVL)
                if dataset_count == 0:
                    break

                with self.i2c_device as i2c:
                    i2c.write_then_readinto(
                        buffer,
                        buffer,
                        out_end=1,
                        in_start=1,
                        in_end=min(129, 1 + (dataset_count * 4)),
                    )

                # Unpack data stream into more usable U/D/L/R datasets for analysis
                idx = 0
                for i in range(dataset_count):
                    rec = i + 1
                    idx = 1 + ((rec - 1) * 4)

                    buffer_dataset[0] = buffer[idx]
                    buffer_dataset[1] = buffer[idx + 1]
                    buffer_dataset[2] = buffer[idx + 2]
                    buffer_dataset[3] = buffer[idx + 3]

                    # Drop fully-saturated and fully-zero to conserve memory
                    # Filter to remove useless (saturated, empty, low-count) datasets
                    if (
                        (not all(val == 255 for val in buffer_dataset))
                        and (not all(val == 0 for val in buffer_dataset))
                        and (all(val >= 30 for val in buffer_dataset))
                    ):
                        if len(frame) < 2:
                            frame.append(tuple(buffer_dataset))
                        else:
                            frame[1] = tuple(buffer_dataset)

                # Wait a very short time to see if new FIFO data has arrived before we drop out
                time.sleep(0.03)

        # If we only got one useful frame, that's not enough to make a solid guess
        if len(frame) < 2:
            return 0

        # We should have a dataframe with two tuples now, a "first" and "last" entry.
        # Time to process the dataframe!

        # Determine our up/down and left/right ratios along with our first/last deltas
        f_r_ud = ((frame[0][0] - frame[0][1]) * 100) // (frame[0][0] + frame[0][1])
        f_r_lr = ((frame[0][2] - frame[0][3]) * 100) // (frame[0][2] + frame[0][3])

        l_r_ud = ((frame[1][0] - frame[1][1]) * 100) // (frame[1][0] + frame[1][1])
        l_r_lr = ((frame[1][2] - frame[1][3]) * 100) // (frame[1][2] + frame[1][3])

        delta_ud = l_r_ud - f_r_ud
        delta_lr = l_r_lr - f_r_lr

        # Make our first guess at what gesture we saw, if any
        state_ud = 0
        state_lr = 0

        if delta_ud >= 30:
            state_ud = 1
        elif delta_ud <= -30:
            state_ud = -1

        if delta_lr >= 30:
            state_lr = 1
        elif delta_lr <= -30:
            state_lr = -1

        # Make our final decision based on our first guess and, if required, the delta data
        gesture_found = 0

        # Easy cases
        if state_ud == -1 and state_lr == 0:
            gesture_found = 1
        elif state_ud == 1 and state_lr == 0:
            gesture_found = 2
        elif state_ud == 0 and state_lr == -1:
            gesture_found = 3
        elif state_ud == 0 and state_lr == 1:
            gesture_found = 4

        # Not so easy cases
        if gesture_found == 0:
            if state_ud == -1 and state_lr == 1:
                if abs(delta_ud) > abs(delta_lr):
                    gesture_found = 1
                else:
                    gesture_found = 4
            elif state_ud == 1 and state_lr == -1:
                if abs(delta_ud) > abs(delta_lr):
                    gesture_found = 2
                else:
                    gesture_found = 3
            elif state_ud == -1 and state_lr == -1:
                if abs(delta_ud) > abs(delta_lr):
                    gesture_found = 1
                else:
                    gesture_found = 3
            elif state_ud == 1 and state_lr == 1:
                if abs(delta_ud) > abs(delta_lr):
                    gesture_found = 2
                else:
                    gesture_found = 3

        if gesture_found != 0:
            if self._rotation != 0:
                # If we need to rotate our gesture, lets do that before returning
                dir_lookup = [1, 4, 2, 3]
                idx = (dir_lookup.index(gesture_found) + self._rotation // 90) % 4
                return dir_lookup[idx]

        return gesture_found

    ## COLOR
    @property
    def color_data(self) -> Tuple[int, int, int, int]:
        """Tuple containing red, green, blue, and clear light intensity values detected by the
        sensor during the latest color/light engine run.

        Each value is a 16-bit integer with a possible value of ``0`` to ``65535``.

        .. caution:: Will always return ``(0, 0, 0, 0)`` if `enable_color` is not set to ``True``.

        .. tip:: To get useful, predictable `color_data` results it is important to tune
           `color_gain` and `color_integration_time`, to accommodate different lighting conditions,
           sensor placements, plastic/glass transparencies, expected object reflectivity, and
           environmental conditions.

           For instance, measuring color of objects close to the sensor with bright, nearby
           illumination (such as the white LEDs on the `Adafruit Clue
           <https://www.adafruit.com/product/4500>`_) may work well with a `color_gain` of ``0``
           and a `color_integration_time` of ``72``.

           However, measuring the intensity and color temperature of ambient light through
           difusion glass or plastic is likely to require experimenting with a wide range of
           `color_gain` and `color_integration_time` settings before useful data can be obtained.
        """
        return (
            self._color_data16(_APDS9960_CDATAL + 2),
            self._color_data16(_APDS9960_CDATAL + 4),
            self._color_data16(_APDS9960_CDATAL + 6),
            self._color_data16(_APDS9960_CDATAL),
        )

    # method for reading and writing to I2C
    def _write8(self, command: int, abyte: int) -> None:
        """Write a command and 1 byte of data to the I2C device"""
        buf = self.buf2
        buf[0] = command
        buf[1] = abyte
        with self.i2c_device as i2c:
            i2c.write(buf)

    def _writecmdonly(self, command: int) -> None:
        """Writes a command and 0 bytes of data to the I2C device"""
        buf = self.buf2
        buf[0] = command
        with self.i2c_device as i2c:
            i2c.write(buf, end=1)

    def _read8(self, command: int) -> int:
        """Sends a command and reads 1 byte of data from the I2C device"""
        buf = self.buf2
        buf[0] = command
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_end=1)
        return buf[0]

    def _get_bit(self, register: int, mask: int) -> bool:
        """Gets a single bit value from the I2C device's register"""
        buf = self.buf2
        buf[0] = register
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        return bool(buf[1] & mask)

    def _set_bit(self, register: int, mask: int, value: bool) -> None:
        """Sets a single bit value in the I2C device's register"""
        buf = self.buf2
        buf[0] = register
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        if value:
            buf[1] |= mask
        else:
            buf[1] &= ~mask
        with self.i2c_device as i2c:
            i2c.write(buf, end=2)

    def _get_bits(self, register: int, pos: int, mask: int) -> int:
        """Sets a multi-bit value in the I2C device's register"""
        buf = self.buf2
        buf[0] = register
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        return (buf[1] & mask) >> pos

    def _set_bits(self, register: int, pos: int, mask: int, value: int) -> None:
        """Sets a multi-bit value in the I2C device's register"""
        buf = self.buf2
        buf[0] = register
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        buf[1] = (buf[1] & ~mask) | (value << pos)
        with self.i2c_device as i2c:
            i2c.write(buf, end=2)

    def _color_data16(self, command: int) -> int:
        """Sends a command and reads 2 bytes of data from the I2C device
        The returned data is low byte first followed by high byte"""
        buf = self.buf2
        buf[0] = command
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1)
        return buf[1] << 8 | buf[0]
