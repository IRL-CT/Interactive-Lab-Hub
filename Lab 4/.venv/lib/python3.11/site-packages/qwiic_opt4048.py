# -------------------------------------------------------------------------------
# qwiic_opt4048.py
#
# Do you like this library? Help support SparkFun. Buy a board!
# * Qwiic 1x1:  https://www.sparkfun.com/products/22638
# * Qwiic Mini: https://www.sparkfun.com/products/22639

# Python library for the SparkFun Qwiic OPT4048 Tristiumulus Color Sensor, available here:
# * https://www.github.com/SparkFun/Qwiic_OPT4048_Py
# -------------------------------------------------------------------------------
# Written by SparkFun Electronics, November, 2023 This python library supports the SparkFun Electroncis Qwiic ecosystem
# More information on Qwiic is at https://www.sparkfun.com/qwiic
#
# ===============================================================================
# Copyright (c) 2023 SparkFun Electronics
# SPDX-License-Identifier: MIT
# ===============================================================================

from dataclasses import dataclass
import qwiic_i2c
import opt4048_registers as REGS

OPT4048_ADDR_HIGH = 0x45
OPT4048_ADDR_SCL = 0x45
OPT4048_ADDR_LOW = 0x44
OPT4048_ADDR_DEF = 0x44
OPT4048_ADDR_SDA = 0x46

OPT4048_DEVICE_ID = 0x821
_DEFAULT_NAME = "Qwiic OPT4048 Color Sensor"
_AVAILABLE_I2C_ADDRESS = [OPT4048_ADDR_LOW, OPT4048_ADDR_HIGH, OPT4048_ADDR_SDA]


@dataclass
class sfe_color_t:
    """
    Dataclass for storing color data from the OPT4048.
    """

    red: int = 0
    green: int = 0
    blue: int = 0
    white: int = 0
    counterR: int = 0
    counterG: int = 0
    counterB: int = 0
    counterW: int = 0
    CRCR: int = 0
    CRCG: int = 0
    CRCB: int = 0
    CRCW: int = 0


class QwOpt4048:
    """
    QwOpt4048
    """

    device_name = _DEFAULT_NAME
    available_addresses = _AVAILABLE_I2C_ADDRESS

    # This matrix is used to convert the ADC values to CIE values.
    cie_matrix = [
        [0.000234892992, -0.0000189652390, 0.0000120811684, 0],
        [0.0000407467441, 0.000198958202, -0.0000158848115, 0.00215],
        [0.0000928619404, -0.0000169739553, 0.000674021520, 0],
        [0, 0, 0, 0],
    ]

    OPT_MATRIX_ROWS = 4
    OPT_MATRIX_COLS = 4

    def __init__(self, address=None, i2c_driver=None):
        """
        Initialize the QwOpt4048 device class.
        :param address: The I2C address to use for the device.
        :param i2c_driver: An existing i2c driver object to use (optional).
        :return: The QwOpt4048 device object.
        :rtype: Object
        """
        # Did the user specify an I2C address?
        self.address = self.available_addresses[0] if address is None else address

        # load the I2C driver if one isn't provided
        if i2c_driver is None:
            self._i2c = qwiic_i2c.getI2CDriver()
            if self._i2c is None:
                print("Unable to load I2C driver for this platform.")
                return
        else:
            self._i2c = i2c_driver

    def is_connected(self):
        """
        Determine if a OPT4048 device is conntected to the system..

        :return: True if the device is connected, otherwise False.
        :rtype: bool

        """
        return qwiic_i2c.isDeviceConnected(self.address)

    connected = property(is_connected)

    def begin(self):
        """
        Initializes this device with default parameters

        :return: Returns `True` if successful, otherwise `False`
        :rtype: bool
        """

        if self.get_device_id() != OPT4048_DEVICE_ID:
            return False

        return True

    def get_device_id(self):
        """
        Retrieve the unique device ID of the OPT4048.

        :return: Unique device ID.
        :rtype: int
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_DEVICE_ID, 2
        )

        unique_id = (block[0] << 8) | block[1]

        return unique_id

    def set_basic_setup(self):
        """
        Configure basic setup for the OPT4048.

        This function sets the range, conversion time, and operation mode to default values.
        It's meant to just get the device up and running with minimal thought from the user.

        :return: None
        """
        self.set_range(REGS.opt4048RangeT.RANGE_AUTO.value)
        self.set_conversion_time(
            REGS.opt4048ConversionTimeT.CONVERSION_TIME_200MS.value
        )
        self.set_operation_mode(
            REGS.opt4048OperationModeT.OPERATION_MODE_CONTINUOUS.value
        )

    def set_range(self, color_range):
        """
        Set the range of the OPT4048.

        :param range: The desired range to set.
        :type range: REGS.opt4048RangeT
        :return: None
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]
        control_reg &= ~0x3C00
        control_reg |= color_range << 10

        block[0] = control_reg >> 8
        block[1] = control_reg & 0x00FF

        self._i2c.writeBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, block)

    def get_range(self):
        """
        Retrieve the current range setting of the OPT4048.

        :return: Current range setting.
        :rtype: REGS.opt4048RangeT
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]

        return (control_reg & 0x3C00) >> 10

    def set_conversion_time(self, time):
        """
        Set the time used to convert light to analog values. Longer times result in more accurate
        readings.
        :param time: The desired conversion time to set.
        :type time: int
        :return: None
        """

        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]
        control_reg &= ~0x03C0
        control_reg |= time << 6

        block[0] = control_reg >> 8
        block[1] = control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_CONTROL,
            block,
        )

    def get_conversion_time(self):
        """
        Gets the time used to convert light to analog values. Longer times result in more accurate
        readings.
        :return: Current conversion time setting.
        :rtype: int
        """

        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]

        return (control_reg & 0x03C0) >> 6

    def set_qwake(self, enable=True):
        """
        Sets the quick wake bit for the OPT4048. When enabled, not all systems are put into
        deep sleep when the device is set to this mode, resulting in faster wake times.
        :param enable: Enable or disable quick wake.
        :type enable: bool
        """

        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]
        control_reg &= ~0x8000
        control_reg |= enable << 15

        block[0] = control_reg >> 8
        block[1] = control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_CONTROL,
            block,
        )

    def get_qwake(self):
        """
        Retrieve the quick wake bit for the OPT4048. When enabled, not all systems are put into
        deep sleep when the device is set to this mode, resulting in faster wake times.
        :return: Quick wake bit.
        :rtype: int
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]

        return (control_reg & 0x8000) >> 15

    def set_operation_mode(self, mode):
        """
        Set the operation mode of the OPT4048: Power-down, Forced auto-range, one-shot, or continuous.
        :param mode: The desired operation mode to set.
        :type mode: int
        :return: None
        """

        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]
        control_reg &= ~0x0030
        control_reg |= mode << 4

        block[0] = control_reg >> 8
        block[1] = control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_CONTROL,
            block,
        )

    def get_operation_mode(self):
        """
        Retrieve the current operation mode of the OPT4048.
        :return: Current operation mode.
        :rtype: int
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]

        return (control_reg & 0x0030) >> 4

    def set_int_latch(self, enable=True):
        """
        Set the interrupt latch of the OPT4048. When enabled, the interrupt pin will remain active
        until the interrupt register is read.
        :param enable: Enable or disable interrupt latch.
        :type enable: bool
        :return: None
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]
        control_reg &= ~0x0008
        control_reg |= enable << 3

        block[0] = control_reg >> 8
        block[1] = control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_CONTROL,
            block,
        )

    def get_int_latch(self):
        """
        Retrieve the interrupt latch of the OPT4048. When enabled, the interrupt pin will remain active
        until the interrupt register is read.
        :return: Interrupt latch.
        :rtype: bool
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]

        return control_reg & 0x0008

    def set_int_active_high(self, enable=True):
        """
        Set the interrupt polarity of the OPT4048. When enabled, the interrupt pin is active high.
        :param enable: Enable or disable interrupt polarity.
        :type enable: bool
        :return: None
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]
        control_reg &= ~0x0004
        control_reg |= enable << 2

        block[0] = control_reg >> 8
        block[1] = control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_CONTROL,
            block,
        )

    def get_int_active_high(self):
        """
        Retrieve the interrupt polarity of the OPT4048. When enabled, the interrupt pin is active high.
        :return: Interrupt polarity.
        :rtype: bool
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]

        return (control_reg & 0x0004) >> 2

    def set_int_input(self, enable=True):
        """
        Set the interrupt input of the OPT4048. When enabled, the interrupt pin is used as an input.
        :param enable: Enable or disable interrupt input.
        :type enable: bool
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_INT_CONTROL, 2
        )

        int_control_reg = (block[0] << 8) | block[1]
        int_control_reg &= ~0x0010
        int_control_reg |= enable << 4

        block[0] = int_control_reg >> 8
        block[1] = int_control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_INT_CONTROL,
            block,
        )

    def get_int_input_enable(self):
        """
        Retrieve the interrupt input of the OPT4048. When enabled, the interrupt pin is used as an input.
        :return: Interrupt input.
        :rtype: bool
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_INT_CONTROL, 2
        )

        int_control_reg = (block[0] << 8) | block[1]

        return (int_control_reg & 0x0010) >> 4

    def set_int_mechanism(self, mechanism):
        """
        Set the interrupt mechanism of the OPT4048: SMBus Alert, INT Pin data ready for next channel,
        or INT Pin data ready for all channels.
        :param enable: Enable or disable interrupt mechanism.
        :type enable: bool
        :return: None
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_INT_CONTROL, 2
        )

        int_control_reg = (block[0] << 8) | block[1]
        int_control_reg &= ~0x000C
        int_control_reg |= mechanism << 2

        block[0] = int_control_reg >> 8
        block[1] = int_control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_INT_CONTROL,
            block,
        )

    def get_int_mechanism(self):
        """
        Retrieve the interrupt mechanism of the OPT4048: SMBus Alert, INT Pin data ready for next channel,
        or INT Pin data ready for all channels.
        :return: Interrupt mechanism.
        :rtype: int
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_INT_CONTROL, 2
        )

        int_control_reg = (block[0] << 8) | block[1]

        return (int_control_reg & 0x000C) >> 2

    def get_all_flags(self):
        """
        Retrieve all flags of the OPT4048.
        :return: All flags of the OPT4048.
        :rtype: int
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_FLAGS, 2)

        return block[0] << 8 | block[1]

    def get_overload_flag(self):
        """
        Retrieve the flag that indicates the ADC is overloaded.
        :return: Flag that indicates the ADC is overloaded.
        :rtype: bool
        """
        flag_reg = REGS.opt4048_reg_flags_t()

        flag_reg.word = self.get_all_flags()

        return flag_reg.bits.overload_flag

    def get_conv_ready_flag(self):
        """
        Retrieve the flag that indicates a conversion is ready to be read.
        :return: Flag that indicates a conversion is ready to be read.
        :rtype: bool
        """
        flag_reg = REGS.opt4048_reg_flags_t()

        flag_reg.word = self.get_all_flags()

        return flag_reg.bits.conv_ready_flag

    def get_too_bright_flag(self):
        """
        Retrieve the flag that indicates lux has is above the current range. This
        is considered a fault and is stored int the fault register.
        :return: Flag that indicates lux is above the current range.
        :rtype: bool
        """
        flag_reg = REGS.opt4048_reg_flags_t()

        flag_reg.word = self.get_all_flags()

        return flag_reg.bits.flag_high

    def get_too_dim_flag(self):
        """
        Retrieve the flag that indicates lux has is below the current range. This
        is considered a fault and is stored int the fault register.
        :return: Flag that indicates lux is below the current range.
        :rtype: bool
        """
        flag_reg = REGS.opt4048_reg_flags_t()

        flag_reg.word = self.get_all_flags()

        return flag_reg.bits.flag_low

    def set_fault_count(self, count):
        """
        Set the number of faults needed to trigger an interupt.
        :param count: Number of faults needed to trigger an interupt.
        :type count: int
        :return: None
        """

        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]
        control_reg &= ~0x0003
        control_reg |= count

        block = control_reg >> 8
        block = control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_CONTROL,
            block,
        )

    def get_fault_count(self):
        """
        Retrieve the number of faults that have been triggered.
        :return: Number of faults that have been triggered.
        :rtype: int
        """

        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_CONTROL, 2)

        control_reg = (block[0] << 8) | block[1]

        return control_reg & 0x0003

    def set_threshold_low(self, thresh):
        """
        Set the low interrupt threshold value of the OPT4048.
        :param thresh: Low interrupt threshold value.
        :type thresh: int
        :return: None
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_THRESH_L_EXP_RES, 2
        )

        thresh_reg = (block[0] << 8) | block[1]
        thresh_reg &= ~0xF000
        thresh_reg |= thresh << 12

        block[0] = thresh_reg >> 8
        block[1] = thresh_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_THRESH_L_EXP_RES,
            block,
        )

    def get_threshold_low(self):
        """
        Retrieve the low interrupt threshold value of the OPT4048.
        :return: Low interrupt threshold value.
        :rtype: int
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_THRESH_L_EXP_RES, 2)

        thresh_reg = (block[0] << 8) | block[1]

        return thresh_reg >> 12

    def set_threshold_high(self, thresh):
        """
        Set the high interrupt threshold value of the OPT4048.
        :param thresh: High interrupt threshold value.
        :type thresh: int
        :return: None
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_THRESH_H_EXP_RES, 2
        )

        thresh_reg = (block[0] << 8) | block[1]
        thresh_reg &= ~0xF000
        thresh_reg |= thresh << 12

        block[0] = thresh_reg >> 8
        block[1] = thresh_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_THRESH_H_EXP_RES,
            block,
        )

    def get_threshold_high(self):
        """
        Retrieve the high interrupt threshold value of the OPT4048.
        :return: High interrupt threshold value.
        :rtype: int
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_THRESH_H_EXP_RES, 2
        )

        thresh_reg = (block[0] << 8) | block[1]

        return thresh_reg >> 12

    def set_i2c_burst(self, enable=True):
        """
        Set the I2C burst setting of the OPT4048: auto-increment or single register I2C reads.
        :param enable: Enable or disable I2C burst setting.
        :type enable: bool
        :return: None
        """
        block = self._i2c.readBlock(self.address, REGS.SFE_OPT4048_REGISTER_INT_CONTROL, 2)

        int_control_reg = (block[0] << 8) | block[1]
        int_control_reg &= ~0x0001
        int_control_reg |= enable

        block = int_control_reg >> 8
        block = int_control_reg & 0x00FF

        self._i2c.writeBlock(
            self.address,
            REGS.SFE_OPT4048_REGISTER_INT_CONTROL,
            block,
        )

    def get_i2c_burst(self):
        """
        Retrieve the I2C burst setting of the OPT4048: auto-increment or single register I2C reads.
        On by default.
        :return: I2C burst setting.
        :rtype: bool
        """
        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_INT_CONTROL, 2
        )

        int_control_reg = (block[0] << 8) | block[1]

        return int_control_reg & 0x0001

    def get_adc_ch0(self):
        """
        Retrieve the ADC value of channel 0 of the OPT4048.
        :return: ADC value of channel 0.
        :rtype: int
        """
        adc_code = 0
        mantissa = 0

        adc_reg = REGS.opt4048_reg_exp_res_ch0_t()
        adc1_reg = REGS.opt4048_reg_res_cnt_crc_ch0_t()

        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_EXP_RES_CH0, 4
        )

        adc_reg.word = (block[0] << 8) | block[1]
        adc1_reg.word = (block[2] << 8) | block[3]

        mantissa = (adc_reg.bits.result_msb_ch0 << 8) | adc1_reg.bits.result_lsb_ch0

        adc_code = mantissa << adc_reg.bits.exponent_ch0

        return adc_code

    def get_adc_ch1(self):
        """
        Retrieve the ADC value of channel 1 of the OPT4048.
        :return: ADC value of channel 1.
        :rtype: int
        """
        adc_code = 0
        mantissa = 0

        adc_reg = REGS.opt4048_reg_exp_res_ch1_t()
        adc1_reg = REGS.opt4048_reg_res_cnt_crc_ch1_t()

        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_EXP_RES_CH1, 4
        )

        adc_reg.word = (block[0] << 8) | block[1]
        adc1_reg.word = (block[2] << 8) | block[3]

        mantissa = (adc_reg.bits.result_msb_ch1 << 8) | adc1_reg.bits.result_lsb_ch1

        adc_code = mantissa << adc_reg.bits.exponent_ch1

        return adc_code

    def get_adc_ch2(self):
        """
        Retrieve the ADC value of channel 2 of the OPT4048.
        :return: ADC value of channel 2.
        :rtype: int
        """
        adc_code = 0
        mantissa = 0

        adc_reg = REGS.opt4048_reg_exp_res_ch2_t()
        adc1_reg = REGS.opt4048_reg_res_cnt_crc_ch2_t()

        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_EXP_RES_CH2, 4
        )

        adc_reg.word = (block[0] << 8) | block[1]
        adc1_reg.word = (block[2] << 8) | block[3]

        mantissa = (adc_reg.bits.result_msb_ch2 << 8) | adc1_reg.bits.result_lsb_ch2

        adc_code = mantissa << adc_reg.bits.exponent_ch2

        return adc_code

    def get_adc_ch3(self):
        """
        Retrieve the ADC value of channel 3 of the OPT4048.
        :return: ADC value of channel 3.
        :rtype: int
        """
        adc_code = 0
        mantissa = 0

        adc_reg = REGS.opt4048_reg_exp_res_ch3_t()
        adc1_reg = REGS.opt4048_reg_res_cnt_crc_ch3_t()

        block = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_EXP_RES_CH3, 4
        )

        adc_reg.word = (block[0] << 8) | block[1]
        adc1_reg.word = (block[2] << 8) | block[3]

        mantissa = (adc_reg.bits.result_msb_ch3 << 8) | adc1_reg.bits.result_lsb_ch3

        adc_code = mantissa << adc_reg.bits.exponent_ch3

        return adc_code

    def get_all_adc(self):
        """
        Retrieve the ADC values of all channels of the OPT4048.
        :return: ADC values of all channels.
        :rtype: sfe_color_t
        """
        color = sfe_color_t()
        color.red = self.get_adc_ch0()
        color.green = self.get_adc_ch1()
        color.blue = self.get_adc_ch2()
        color.white = self.get_adc_ch3()

        return color

    def get_all_channel_data(self, color):
        """
        Retrieve the ADC values of all channels of the OPT4048.
        :return: ADC values of all channels.
        :rtype: sfe_color_t
        """
        adc0_msb = REGS.opt4048_reg_exp_res_ch0_t()
        adc0_lsb = REGS.opt4048_reg_res_cnt_crc_ch0_t()

        adc1_msb = REGS.opt4048_reg_exp_res_ch1_t()
        adc1_lsb = REGS.opt4048_reg_res_cnt_crc_ch1_t()

        adc2_msb = REGS.opt4048_reg_exp_res_ch2_t()
        adc2_lsb = REGS.opt4048_reg_res_cnt_crc_ch2_t()

        adc3_msb = REGS.opt4048_reg_exp_res_ch3_t()
        adc3_lsb = REGS.opt4048_reg_res_cnt_crc_ch3_t()

        buff = self._i2c.readBlock(
            self.address, REGS.SFE_OPT4048_REGISTER_EXP_RES_CH0, 16
        )

        adc0_msb.word = (buff[0] << 8) | buff[1]
        adc0_lsb.word = (buff[2] << 8) | buff[3]

        adc1_msb.word = (buff[4] << 8) | buff[5]
        adc1_lsb.word = (buff[6] << 8) | buff[7]

        adc2_msb.word = (buff[8] << 8) | buff[9]
        adc2_lsb.word = (buff[10] << 8) | buff[11]

        adc3_msb.word = (buff[12] << 8) | buff[13]
        adc3_lsb.word = (buff[14] << 8) | buff[15]

        mantissa_ch0 = (
            adc0_msb.bits.result_msb_ch0 << 8
        ) | adc0_lsb.bits.result_lsb_ch0
        adc_code_ch0 = mantissa_ch0 << adc0_msb.bits.exponent_ch0

        mantissa_ch1 = (
            adc1_msb.bits.result_msb_ch1 << 8
        ) | adc1_lsb.bits.result_lsb_ch1
        adc_code_ch1 = mantissa_ch1 << adc1_msb.bits.exponent_ch1

        mantissa_ch2 = (
            adc2_msb.bits.result_msb_ch2 << 8
        ) | adc2_lsb.bits.result_lsb_ch2
        adc_code_ch2 = mantissa_ch2 << adc2_msb.bits.exponent_ch2

        mantissa_ch3 = (
            adc3_msb.bits.result_msb_ch3 << 8
        ) | adc3_lsb.bits.result_lsb_ch3
        adc_code_ch3 = mantissa_ch3 << adc3_msb.bits.exponent_ch3

        color.red = adc_code_ch0
        color.green = adc_code_ch1
        color.blue = adc_code_ch2
        color.white = adc_code_ch3

        color.counterR = adc0_lsb.bits.counter_ch0
        color.counterG = adc1_lsb.bits.counter_ch1
        color.counterB = adc2_lsb.bits.counter_ch2
        color.counterW = adc3_lsb.bits.counter_ch3

        color.CRCR = adc0_lsb.bits.crc_ch0
        color.CRCG = adc1_lsb.bits.crc_ch1
        color.CRCB = adc2_lsb.bits.crc_ch2
        color.CRCW = adc3_lsb.bits.crc_ch3

        return color

    def get_lux(self):
        """
        Retrieve the Lux value of the OPT4048.
        :return: Lux value.
        :rtype: float
        """
        adc_ch1 = self.get_adc_ch1()

        return adc_ch1 * self.cie_matrix[1][3]

    def get_CIEx(self):
        """
        Retrieve the CIEx value of the OPT4048.
        :return: CIEx value.
        :rtype: float
        """
        x, y, z = 0, 0, 0
        color = sfe_color_t()

        self.get_all_channel_data(color)

        for row in range(self.OPT_MATRIX_ROWS):
            x += color.red * self.cie_matrix[row][0]
            y += color.green * self.cie_matrix[row][1]
            z += color.blue * self.cie_matrix[row][2]

        if (x + y + z) == 0:
            return 0

        # Calculate the CIE x value, all of the
        # math required to do this is in the datasheet.
        return x / (x + y + z)

    def get_CIEy(self):
        """
        Retrieve the CIEy value of the OPT4048.
        :return: CIEy value.
        :rtype: float
        """
        x, y, z = 0, 0, 0
        color = sfe_color_t()

        self.get_all_channel_data(color)

        for row in range(self.OPT_MATRIX_ROWS):
            x += color.red * self.cie_matrix[row][0]
            y += color.green * self.cie_matrix[row][1]
            z += color.blue * self.cie_matrix[row][2]

        if (x + y + z) == 0:
            return 0

        # Calculate the CIE y value, all of the
        # math required to do this is in the datasheet.
        return y / (x + y + z)

    def get_CCT(self):
        """
        Retrieve the CCT value of the OPT4048.
        :return: CCT value.
        :rtype: float
        """
        x, y, z = 0, 0, 0
        color = sfe_color_t()

        self.get_all_channel_data(color)

        for row in range(self.OPT_MATRIX_ROWS):
            x += color.red * self.cie_matrix[row][0]
            y += color.green * self.cie_matrix[row][1]
            z += color.blue * self.cie_matrix[row][2]

        if (x + y + z) == 0:
            return 0

        CIEx = x / (x + y + z)
        CIEy = y / (x + y + z)

        # Calculate the correlated color temperature, all of the
        # math required to do this is in the datasheet.
        n = (CIEx - 0.3320) / (0.1858 - CIEy)

        CCT = 432 * n**3 + 3601 * n**2 + 6861 * n + 5517

        return CCT
