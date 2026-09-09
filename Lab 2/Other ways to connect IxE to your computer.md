
## Connect IxE to your computer via the computer Ethernet port

(based off of instructions from [Nikmart's IxE Git](https://github.com/nikmart/interaction-engine/wiki/Connect-IxE-to-your-computer-via-Ethernet-port))

## Connecting to The HOUSE Wifi

1. Register the MAC address of your Raspberry Pi on The House network at https://selfcare.boingohotspot.net/login using Add a Device.
1. Edit the `/etc/wpa_supplicant/wpa_supplicant.conf` file with `nano` OR on the `\boot` volume that you see when the SD card is plugged into your computer, is a file called:  `wpa_supplicant.conf.bak`. Duplicate the file and rename the duplicate to `wpa_supplicant.conf`. Now edit the duplicated file (`wpa_supplicant.conf`) and add the house wifi to the list of networks to connect to as shown below. Then safely eject the sd card, plug it back into the Pi and power it back up.
1. The section you need to add is
```shell
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="The House"
    key_mgmt=NONE
}
```


Afterward, your file should look something like the following.

```shell
update_config=1
country=US

ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="The House"
    key_mgmt=NONE
}

ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="DeviceFarm"
    psk="device@theFarm"
    key_mgmt=WPA-PSK
}

```
3. Try logging into your device using ssh from a terminal.
4. If you need to see what device your IxE is on, use `iwconfig` or find it in this list [here](https://interactivedevice18.slack.com/files/U90LA9TLH/F92HXB020/ixe_ip_mac_hostname.xlsx):

```shell
pi@ixe42:~ $ iwconfig wlan0
wlan0     IEEE 802.11  ESSID:"The House"  
          Mode:Managed  Frequency:2.462 GHz  Access Point: 24:79:2A:21:58:C8   
          Bit Rate=72.2 Mb/s   Tx-Power=31 dBm   
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:on
          Link Quality=67/70  Signal level=-43 dBm  
          Rx invalid nwid:0  Rx invalid crypt:0  Rx invalid frag:0
          Tx excessive retries:0  Invalid misc:0   Missed beacon:0
```









### Instructions for Mac

1. Plug an ethernet cable from your Mac to the Raspberry Pi (note you may need to use a Thunderbolt to Ethernet or USB to Ethernet adapter if your Mac does not have a built-in Ethernet port).

2. Check that the IxE are getting a self-assigned IP in System Preferences -> Network. It should have an orange color.

3. To get Internet on your Pi, use Internet Sharing and share your Wifi with your Ethernet. (Note: This will not work on 802.11X like eduroam. If you are trying to do this on campus, connect to Cornell Visitor and then share your wifi)

3. Try pinging your IxE with the .local extension: ping ixe05.local

If the ping work, you can ssh in just like normal.

### Instructions for PC

[someone with a pc, please update this...]

## Connect IxE to your computer via a separate WiFI card

You can share a WiFi connection to the wider internet from your laptop if you can bring up a separate Wifi interface on your computer (for example by using a USB Wifi adapter).

### Instructions for Mac

1. Bring up the new WiFi interface. This will likely involve installing the drivers for the device, registering the new interface (for example, by using http://mycomputers.cit.cornell.edu at Cornell), and getting it online.

1. Go to the Sharing control panel to enable Internet sharing from your newly installed interface to the WiFi network which you will share locally. Go to WiFi Options to configure your network to be named DeviceFarm, and the WPA2 password to be the the DeviceFarm password. Finally, check Internet Sharing to turn the sharing on.

1. Power up your IxE. It should come up on your local network, and you should be able to access it via ssh like you would on the class network.

[someone with a pc, please update this...]

## Connect your IxE to your own WiFi

Based on instructions found here: [https://howchoo.com/g/ndy1zte2yjn/how-to-set-up-wifi-on-your-raspberry-pi-without-ethernet](https://howchoo.com/g/ndy1zte2yjn/how-to-set-up-wifi-on-your-raspberry-pi-without-ethernet)

If you have a WiFi router at home that you control, you can connect to it by setting the wifi configuration of your Pi. To do this:

1. Use a text editor on your computer to create a file called `wpa_supplicant.conf` with the following text in it:

```shell
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="DeviceFarm"
    psk="device@theFarm"
    key_mgmt=WPA-PSK
}

ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="YOUR WIFI NAME HERE"
    psk="YOUR WIFI PASSWORD HERE"
    key_mgmt=WPA-PSK
}
```
2. Plug the SD card with the IxE image on it into your computer.
You should see a disk drive called `boot` mount to your computer.

3. Open `boot` and copy the `wpa_supplicant.conf` file into the directory.

4. Safely eject the SD card from your computer.

5. Plug the SD card back into your IxE, then plug it into USB power.

When the Pi boots up, it will copy the `wpa_supplicant.conf` file into the WiFi settings directory in `/etc/wpa_wupplicant/`. This will update your WiFi setting and should get the Pi on your home wifi.



## Connecting to RedRover
You can get your Pi working on Cornell's `RedRover` network by:

### Registering your Pi's MAC address to your Cornell account at: [https://dnsdb.cit.cornell.edu/dnsdb-cgi/mycomputers.cgi](https://dnsdb.cit.cornell.edu/dnsdb-cgi/mycomputers.cgi)

You can find your MAC address using the spreadsheet (IXE_IP_MAC_HOSTNAME) we provided on the class Slack. The MAC address is associated with you ixe hostname in the form ixe[00] where [00] are your numbers.

Register your MAC address as one of your devices. We recommend you name is ixe[00] so you know which registration this is for.

### Adding a python script to your machine to email the ixe's IP to you

1. While you are logged into you Pi (from DeviceFarm, The House, or through ethernet), create a new file for the `python` script that will email the IP to you

```shell
nano startup_mailer.py
```

2. Copy and paste this python code into the editor

```python
import subprocess
import smtplib
import socket
from email.mime.text import MIMEText
import datetime

# Change to your own account information
to = 'YOUREMAIL@DOMAIN.com'
gmail_user = 'interactiveDeviceDesign@gmail.com'
gmail_password = 'device@theFarm'
smtpserver = smtplib.SMTP('smtp.gmail.com', 587)
smtpserver.ehlo()
smtpserver.starttls()
smtpserver.ehlo
smtpserver.login(gmail_user, gmail_password)
today = datetime.date.today()

# Very Linux Specific
arg='ip route list'
p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
data = p.communicate()
split_data = data[0].split()
ipaddr = split_data[split_data.index('src')+1]
my_ip = 'ixe[00] ip is %s' %  ipaddr
msg = MIMEText(my_ip)
msg['Subject'] = 'IP for ixe58 on %s' % today.strftime('%b %d %Y')
msg['From'] = gmail_user
msg['To'] = to
smtpserver.sendmail(gmail_user, [to], msg.as_string())
smtpserver.quit()
```

This script is setup with our class GMail account, `interactiveDeviceDesign@gmail.com`. We recommend you use this so that you do not need to store your own GMail password in clear text.

3. Look for the line `to = 'YOUREMAIL@DOMAIN.com'` and replace the email address with your email. Any email like your GMail or Cornell Email should work fine.

4. Put your ixe's number in the lines `my_ip = 'ixe[00] ip is %s' %  ipaddr` and `msg['Subject'] = 'IP For ixe58 on %s' % today.strftime('%b %d %Y')` replacing the `[00]` with your number.

4. Save the file and exit `nano` (using Ctrl+X, then choosing `yes`, then saving to `startup_mailer.py'

5. Test the python code by running `python /home/pi/startup_mailer.py`. You should get an email with your IP address in about a minute.

The email should look like this:

```text
From: interactivedevicedesign@gmail.com
To: YOUREMAIL@DOMAIN.com

ixe[00] ip is xxx.xxx.xxx.xxx <-- this will be your ixe number and the IP it has currently
```

**NOTE: A RedRover IP will be on 10.xxx.xxx.xxx. If you get something like 192.xxx.xxx.xxx then you are probably connected to `DeviceFarm`**
 
6. Tell your Pi to run the `startup_mailer.py` code when your pi reboots using `cron` (a [cool Unix tool](https://en.wikipedia.org/wiki/Cron) that allows you to automate things on your machine)

```shell
crontab -e
``` 

If `cron` asks you to choose an editor, we recommend choosing option `2 - nano`

Once you are in `nano` you will edit the `crontab` file which lets you schedule when to run certain things

```
# Edit this file to introduce tasks to be run by cron.
#
# Each task to run has to be defined through a single line
# indicating with different fields when the task will be run
# and what command to run for the task
#
# To define the time you can provide concrete values for
# minute (m), hour (h), day of month (dom), month (mon),
# and day of week (dow) or use '*' in these fields (for 'any').#
# Notice that tasks will be started based on the cron's system
# daemon's notion of time and timezones.
#
# Output of the crontab jobs (including errors) is sent through
# email to the user the crontab file belongs to (unless redirected).
#
# For example, you can run a backup of all your user accounts
# at 5 a.m every week with:
# 0 5 * * 1 tar -zcf /var/backups/home.tgz /home/
#
# For more information see the manual pages of crontab(5) and cron(8)
#
# m h  dom mon dow   command
```

Add the following line to the bottom of the file (make sure there is no `#` symbol as this makes the line a comment)

```
@reboot sleep 30 && python /home/pi/startup_mailer.py
```

This line tells your Pi to run `python /home/pi/startup_mailer.py` when your machine reboots. The `sleep 30` is there to give your Pi 30 seconds to wake up and load all the system resources before it emails you your IP (we have found that not having the sleep delay means the script does not send an email, probably because the Pi doesn't have an IP).

Save and exit `nano` (using `Ctrl+X`, `yes`)

7. Edit your `wpa_supplicant.conf` WiFi settings

```shell
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```

Add the following lines to the top of the file, above the `DeviceFarm` settings if you would prefer it to use `RedRover` before using `DeviceFarm`

```text
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
network={
    ssid="RedRover"
    key_mgmt=NONE
}
```

You can also comment out `DeviceFarm` settings so that you only connect to `RedRover`. Put `#` before all the lines for the `DeviceFarm` config settings.

```text
#ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
#network={
#    ssid="DeviceFarm"
#    psk="device@theFarm"
#    key_mgmt=WPA-PSK
#}
```

(If something goes wrong, you can always reset your WiFi settings using the `wpa_supplicant.conf.bak` file in the `boot` directory.)

Save and exit `nano` (`Ctrl+X`, `yes`)

8. Reboot your Pi using `sudo reboot`. If everything is configured correctly, you should get an email with your IP within a minute or two.

### Connecting to your Pi using the IP it has with your laptop on `RedRover` or `eduroam`
1. Once you receive the email from you Pi, copy the IP address.

**NOTE: A RedRover IP will be on 10.xxx.xxx.xxx. If you get something like 192.xxx.xxx.xxx then you are probably connected to `DeviceFarm`**

2. Make sure your laptop is connected to `RedRover` or `eduroam` (`Cornell Visitor` will not work)

#### On Mac/Linux
Open your Terminal (on Mac/Linux) or PuTTY (on Windows) and ssh using the IP address from the email

```shell
ssh pi@xx.xx.xx.xx
```

#### On Windows
Use the IP from the email as as the location instead of `ixe[00]`. Make sure the `Port` is set to `22`

3. You can access the webpage running on port `8000` (in our examples like `helloYou`) by going to the IP address then port 8000 iun your browser window

`ex: 10.148.131.xxx:8000`
