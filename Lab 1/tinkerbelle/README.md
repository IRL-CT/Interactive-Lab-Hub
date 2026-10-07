# Tinkerbelle - Enhanced UI with Keyboard Controls

> **✨ This is the enhanced `newnewUI` branch** featuring keyboard shortcuts, advanced sound options, customizable colors, and smooth easing transitions!

<img src="/imgs/KeyboardControl.png" alt="Keyboard Control Interface" width="400"/>

Tinkerbelle is a simple tool for prototyping interaction by using a phone as a web-controlled smart light. 

This enhanced version allows you to control the smart light using **keyboard shortcuts** and provides additional features for defining sounds, colors, and easing transitions. You can also control the smart light via the web interface or using any software that can connect to a websocket.

<img src="/imgs/Snapshot.PNG" alt="system diagram" width="300"/>

## Enhanced Features in this Branch

- 🎹 **Keyboard Shortcuts**: Control colors and effects directly from your keyboard
- 🎵 **Advanced Sound Options**: Define and trigger custom sounds
- 🎨 **Customizable Colors**: Enhanced color palette and controls  
- ✨ **Easing Transitions**: Smooth animations between color changes
- 🖥️ **Dual Server Options**: Choose between Python Flask or Node.js implementations

## Branch Information

This repository has multiple versions:
- **`main` branch**: Standard Python Flask implementation
- **`newnewUI` branch**: Enhanced version with both Python and Node.js options plus improved UI

To switch between branches:
```bash
# Switch to the standard version
git checkout main

# Switch to this enhanced version
git checkout newnewUI
```

## Installation Options

This branch provides two server implementations:

## Installation Options

This branch provides two server implementations:

### Option 1: Python Flask Server (Recommended for beginners)

This project uses a python web-server called Flask. 
You should have [Python3 installed](https://realpython.com/installing-python/).

**Python Version Compatibility**: This project works with Python 3.7 and newer. If you encounter installation issues with specific package versions, try using a more recent version of Python (3.9+ recommended).

<!--To install flask in a virtual environment:
```
$ sudo pip3 install virtualenv
$ virtualenv tinkerbelle
$ cd tinkerbelle
$ source bin/activate
```-->

Now clone this repo to download the python code that serves up the Flask page by typing the following commands in your laptop/computer terminal.
(You can check out more details [here](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository-from-github/cloning-a-repository) for how to clone github repository to a local machine.)

```bash
$ cd (set the directory you want to clone the repo to)
$ git clone https://github.com/FAR-Lab/tinkerbelle.git
$ cd tinkerbelle
$ git checkout newnewUI  # Switch to this enhanced branch
$ pip3 install -r requirements.txt
```

### Option 2: Node.js Server (Alternative implementation)

If you prefer Node.js or want to try the alternative implementation:

1. Make sure you have [Node.js installed](https://nodejs.org/)
2. Install dependencies:
```bash
$ npm install
```

### Troubleshooting Installation
If you encounter issues installing the Python requirements:
1. **For older Python versions (3.7-3.8)**: Some packages may need specific versions. Try: `pip3 install Flask==2.2.2 Flask-SocketIO==5.3.0`
2. **For newer Python versions (3.11+)**: The flexible requirements should work. If not, try installing packages individually: `pip3 install Flask Flask-SocketIO`
3. **General issues**: Consider using a virtual environment or updating pip: `pip3 install --upgrade pip`

## Getting started

### Using Python Flask Server
Run the tinker.py code, which serves up a webpage

```bash
$ python3 tinker.py
 * Restarting with stat
access at http://localhost:5000
 * Debugger is active!
 * Debugger PIN: ***-***-***
```

### Using Node.js Server (Alternative)
Run the Node.js server:

```bash
$ npm start
# or for development with auto-restart:
$ npm run dev
```

If your get the following error message: `ModuleNotFoundError: No module named 'flask_socketio'`, try typing the following command to install the module:
`$ pip3 install flask-socketio`.


### On a mobile device - acting as the web-controlled smart light
Make sure you are connected to the **same WiFi network** as the computer you are running the web-server. In your phone settings, turn your brightness and volume to full and set the screen to never shut off or lock. On the phone browser, navigate to the [WiFi IPv4 address](https://smallbusiness.chron.com/ip-address-wifi-52888.html) of your laptop/computer you are using to run the web-server with port=5000. In this case, that would be `http://[yourWiFiIPv4address]:5000`.

There should be two buttons. Selecting Tinkerbelle should full-screen the webpage and fade out the buttons. (Note: Unfortunately, the full-screen function does not work on iPhones in case you are using one.)

![mobile screen](/imgs/phone1.png)


### On a computer - acting as the controller
Navigate to the WiFi IPv4 address `http://[yourWiFiIPv4address]:5000` or if using the same computer as the web-server `http://localhost:5000`.

Select [Jane Wren](https://en.wikipedia.org/wiki/Tinker_Bell#On_stage) for the controller. 

![control interface](/imgs/controller.png)

Here changing the color on the color selector will change the background for both the control interface and the tinker-belle device.


### Moving Further

You can change the swatches shown at the bottom of the color selector by editing lines 39 to 54 in `static/index.js` and restarting the web-server.

```
swatches: [
        'rgba(255, 255, 255, 1)',
        'rgba(244, 67, 54, 1)',
        'rgba(233, 30, 99, 1)',
        'rgba(156, 39, 176, 1)',
        'rgba(103, 58, 183, 1)',
        'rgba(63, 81, 181, 1)',
        'rgba(33, 150, 243, 1)',
        'rgba(3, 169, 244, 1)',
        'rgba(0, 188, 212, 1)',
        'rgba(0, 150, 136, 1)',
        'rgba(76, 175, 80, 1)',
        'rgba(139, 195, 74, 1)',
        'rgba(205, 220, 57, 1)',
        'rgba(255, 235, 59, 1)',
        'rgba(255, 193, 7, 1)',
        'rgba(0, 0, 0, 1)',
      ],
```

Typing a description in the Audio input box will play the first result from [https://freesound.org/](https://freesound.org/). The stop button stops playback. Try typing `gong` or `barking`.
