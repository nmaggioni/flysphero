# flysphero

A python script for Raspberry Pi that reads a Sphero's sensors
(using [spheropy](https://github.com/darin-costello/spheropy)) and outputs a PPM signal to an FrSky radio's trainer port (using [pigpio](http://abyz.me.uk/rpi/pigpio/python.html)).

> ###### This project was inspired by [`jsa/flystick`](https://github.com/jsa/flystick).

## Examples

_Check the `docs` folder in the repo for pictures and videos._

## Setup (on Raspberry Pi)

### Installation

1. `sudo apt install -y git python3 python3-pip && pip3 install --user bluez pigpio python3-pigpio python3-numpy`

2. http://abyz.me.uk/rpi/pigpio/download.html
	+ Follow Method 1, 2 or 3 to re-install the library: this gets you the latest version but still uses system facilities installed in _Step 1_ above.

3. [Install spheropy](https://github.com/darin-costello/spheropy#unofficial-python-sdk-for-sphero)

4. `git clone https://github.com/nmaggioni/flysphero.git ~/flysphero`

### Configuration

1. Edit `config.ini` to set your Sphero's name and MAC address (you should easily be able to get them with your smartphone).
	+ You can optionally also change the pin that will output the PPM signal, by default it is GPIO24 (pin #18).

4. Enable & start `pigpiod`
	+ `sudo systemctl enable pygpiod && sudo systemctl start pigpiod`

5. Copy the SystemD service unit in its place (edit it if your user is not named `pi`) and enable it.
	+ `sudo cp flysphero.service /etc/systemd/system/`
	+ `sudo systemctl daemon-reload && sudo systemctl enable flysphero`
	+ **Note:** the service won't run if a Bluetooth adapter is not available.

### Starting

1. Either reboot or manually start the service.
	+ `sudo systemctl start flysphero`

---

### Trainer jack wiring

+ Mono
	+ Tip &rarr; PPM pin _(default is GPIO24)_
	+ Sleeve &rarr; GND _(any GND pin)_
+ Stereo
	+ Tip &rarr; PPM pin _(default is GPIO24)_
	+ Sleeve 1 &rarr; GND _(any GND pin)_
	+ Sleeve 2 &rarr; GND _(any GND pin)_

## Usage

The control script will log its startup phases, they should be self explanatory. In case they aren't:

> 1. Connect the jack to your radio's trainer port.
> 2. Turn on the Sphero.
> 3. Turn on the RPi.
> 4. Wait for the Sphero to connect and flash red-green-blue.
> 5. Rotate the Sphero the way you want it while it flashes white.
> 6. Sphero's motors will lock into place and PPM signal generation will begin.