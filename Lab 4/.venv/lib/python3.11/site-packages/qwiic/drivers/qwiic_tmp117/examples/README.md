# Sparkfun TMP117 Examples Reference
Below is a brief summary of each of the example programs included in this repository. To report a bug in any of these examples or to request a new feature or example [submit an issue in our GitHub issues.](https://github.com/sparkfun/qwiic_tmp117_py/issues). 

NOTE: Any numbering of examples is to retain consistency with the Arduino library from which this was ported. 

## Qwiic Tmp117 Ex1 Basic
This script configures the TMP117 temperature sensor and prints the
 temperature in degrees celsius and fahrenheit with a 500ms delay for
 easier readings.

## Qwiic Tmp117 Ex2 Alert Statuses
This script sets the TMP117 temperature sensor's high limit,
 low limit, and alert function mode. Once set, we read the 
 temperature in C and checks alert status. If we are outside
 of the boundary, we will output a message indicating
 that we are beyond the limit.

## Qwiic Tmp117 Ex3 Set Offset Temp
This sketch configures the TMP117 temperature sensor and allows the user to
 set the offset temperature for System Correction.

## Qwiic Tmp117 Ex4 Set Conv Mode
This script can get and set the conversion mode to
 Continuous Conversion, Shutdown, or One-Shot

## Qwiic Tmp117 Ex5 Set Alert Limits
This script can set and get the Alert Function Mode, Low Temperature 
 Limit, and High Temperature Limit for the sensor. These limits can
 be set within +/- 256°C. When the temperature goes above/below the 
 specified temperature limits, it will cause the alert pins to go
 high. To access these registers, please reference Example 2: Alert Statuses.

## Qwiic Tmp117 Ex6 Set Conv Cycle
This script can set and get the Conversion Times in Continuous Conversion mode
 for the Sensor. A chart for the averaging modes and the conversion times can
 be found in the table below or in the Datasheet on page 27 table 7.

## Qwiic Tmp117 Ex7 Set Address
This script allows the user to change the address of the device and to
 change the Wire port for I2C Communications. The address can be physically
 changed with an external jumper on the back of the sensor. 
 
 See the "Address Select" section in the hookup guide for more information:
 https://learn.sparkfun.com/tutorials/qwiic-tmp117-high-precision-digital-temperature-sensor-hookup-guide


