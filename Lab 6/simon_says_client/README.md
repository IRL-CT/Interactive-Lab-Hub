# Simon Says Pi client

This is a client for the provided `game_server.py`. From this directory, activate the Python environment that runs `pixel_grid_publisher.py`, and run:

```sh
python3 game_client.py
```

The default player is **pi2**. The other Pi can use `python3 game_client.py --player pi1`; each player must use a different name. Start both clients and wait until they report that they connected before starting the server. Both Pi and server need broker access. The client prompts privately for the shared class MQTT broker password; enter it at the prompt. Alternatively, provide it in the `MQTT_PASSWORD` environment variable. Calibration and help do not ask for it. The server's MQTT broker, username, topics, and message formats are unchanged. Do not run the pixel grid publisher simultaneously if it is using the same display and sensor.

### Starting and restoring the display

On the Pi, press **Ctrl+C** in the terminal running `pixel_grid_publisher.py`, then stop the display service:

```sh
sudo systemctl stop piscreen.service
```

After updating your `Interactive-Lab-Hub-Lab6` worktree, activate its existing Lab 6 environment and run the client:

```sh
cd ~/Interactive-Lab-Hub-Lab6/"Lab 6"
source .venv/bin/activate
cd simon_says_client
python3 game_client.py
```

After the game, press **Ctrl+C** in the client terminal, then restore the service:

```sh
sudo systemctl start piscreen.service
```

The terminal prints all commands and results; the mini TFT also shows them. The display uses the same GPIO, SPI, offsets, rotation and baud rate as `Lab 6/pixel_grid_publisher.py`. If display initialization or drawing fails, the client continues with terminal output. The sensor is required and must be available on I2C. This code has not been tested on a physical Pi or against a live broker/server.

Keep the sensor clear between rounds. It must see a neutral reading before accepting the next action. Each round sends at most one action, including a wrong color or a movement in a fake-out; the server decides whether it was correct. A proximity reading above 200 takes priority over color, so a colored object too close to the sensor can register as `close`. The client ignores actions between the result and the next command. A 0.15-second buffer reduces (but cannot eliminate) the server's command/reset timing race; it delays the first event and can affect a close race. The protocol has no round ID or ready handshake, so exact timing, delivery, and recovery from disconnects cannot be guaranteed. If a client disconnects, it waits for a new command after reconnecting.

To inspect raw readings and the detected action without joining the game:

```sh
python3 game_client.py --calibrate
```

With hands and objects away, check that `action=None` appears consistently: the client needs a neutral reading to re-arm. If ambient light produces a color, try increasing `--clear` or `--margin`; if it produces `close`, increase `--proximity` above the idle reading. Then present each color and move a hand close to check that the intended actions still register; tune again if raising a threshold prevents recognition. Proximity takes priority over colors. The defaults match the supplied client: proximity `> 200`, clear channel `> 500`, and the winning color channel must exceed both others by more than 150. You can use the same tuning options with `--calibrate` and during play, for example:

```sh
python3 game_client.py --proximity 200 --clear 500 --margin 150
```

Run `python3 game_client.py --help` for options, including `--settle`. The existing Pi environment should include `paho-mqtt<2`, Adafruit Blinka, APDS9960, RGB Display, and Pillow. Stop with Ctrl+C. To run the hardware-independent tests from this folder:

```sh
python3 -m unittest discover -s tests -v
```
