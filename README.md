## FlyRT
A simple real-time tracker for Drosophilia behavior experiments

![](https://i.imgur.com/ZECicNf.jpg "Screengrab")

## Usage
To launch GUI:
`>> python FlyRT/FlyRT_UI.py`
Both real-time and post-hoc analysis modes are supported.

## Installation & Requirements
It is recommended to create an Anaconda3 environment using the provided .yml file in the env directory

System tested on Windows 10 64-bit using:

* Cython = 0.29
* numpy = 1.15.2
* cv2 = 3.3.1.11
* __Python 3.5 is necessary for real-time analysis using Point Grey FLIR cameras. If only post-hoc analysis will be used, other > 3.5x versions can be used__

## PyCapture2 Libraries
To use FLIR Machine Vision cameras with this module, follow the following steps to integrate the proprietary Point Grey libaries and drivers.

* Install the most recent version of Point Grey FlyCapture2 SDK from the following link: https://www.ptgrey.com/support/downloads. This requires making an account with Point Grey. On Windows, these should be moved to `C:\Program Files` directory if not installed there automatically.
* Install PyCapture2 2.11.425 (also from https://www.ptgrey.com/support/downloads) to the Python root directory. This will be a .msi installer. Run the installer and specify the root direcory. For example, if using the Anaconda distribution with FlyRT environment, the install location would be `../Anaconda3/envs/FlyRT`. 
