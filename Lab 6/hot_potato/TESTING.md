# Hot Potato: test checklist

Work down the list. Each step adds one more real piece, so when something breaks you know which piece did it.

## Step 1. Laptop only (no MQTT needed)

```powershell
cd "C:\Users\Craft\Documents\Interactive-Lab-Hub\Lab 6"
.venv\Scripts\activate
cd hot_potato
python server.py
```

(First time only, before `cd hot_potato`: `pip install -r requirements-server.txt`.)
Stop the server with **Ctrl+C** and start it again after you change `server.py` or the HTML.

Open **http://localhost:5000/viktor**, then:

- [ ] Green dot next to the title, and a yellow banner saying "viktor" isn't in the game yet
- [ ] Press **J**: banner disappears, viktor is at the bottom, labelled "(you)"
- [ ] Click **🤖 Bots**, then **Start**: the 30 s round timer counts down in the middle
- [ ] When the potato flies at you, your circle flashes blue with **CATCH!** Press **↓** (or **C**) and it turns green with **got it!**
- [ ] Don't press anything on the next throw: BOOM, "viktor dropped it"
- [ ] When you hold it (🥔 in your circle), **← ↑ →** throw left / across / right, and it lands where you expect
- [ ] Hold it until the red ring fills: BOOM, "held it too long"
- [ ] Let the round reach 0 (timer turns red for the last 5 s): whoever has it explodes with "time's up"
- [ ] Press **C** when nothing is coming: "butterfingers", and your catch is locked for 1 s
- [ ] Click the names in the top bar (or press **1**–**4**): the diamond rotates so that player is at the bottom

## Step 2. Laptop through the real class broker

You must be on Cornell Wi-Fi. The server terminal should show:

```
[MQTT] connected to farlab.infosci.cornell.edu:1883, listening on IDD/hotpotato/player/+/action
```

- [ ] Open a **second terminal** (activate the venv, `cd hot_potato`), run `python test_player.py ana --seat 3`
- [ ] "ana" appears across from you on the page
- [ ] Start a game. When the test player prints `INCOMING ... press c to CATCH!`, type `c` quickly. When it prints `HOLDING`, type `l` / `f` / `r`.
- [ ] Open **http://localhost:5000/ana**: same game, but now ana is at the bottom
- [ ] Watch the raw traffic at **http://farlab.infosci.cornell.edu:5001**

## Step 3. One real Pi

On your Pi (the Lab 6 venv already has `paho-mqtt`), copy over `test_player.py` and run:

```bash
python test_player.py viktor --seat 1
```

- [ ] viktor joins on the laptop page, and throws/catches typed on the Pi show up on the laptop
- [ ] Then swap in your real script (touch sensor + PiTFT) and check the screen goes waiting → incoming (lights up) → holding (getting redder) → boom
- [ ] Time a few catches: is 1.5 s enough with your sensor? If not, raise `FLIGHT_TIME` in `server.py`.

## Step 4. Whole team

- [ ] Each Pi uses its own name and seat (1 touch, 2 joystick, 3 encoder, 4 IMU), and **only one laptop** runs `server.py`
- [ ] Teammates open `http://<laptop-ip>:5000/<their name>` (the server prints the IP). If Windows asks about the firewall, allow Python on **private networks**.
- [ ] Turn bots **off** once all 4 Pis have joined
- [ ] Kill one Pi's script mid-game: its seat goes empty and the game keeps going (needs `will_set` in the Pi script, see PROTOCOL.md)

## If something doesn't work

| Symptom | Likely cause / fix |
|---|---|
| "This site can't be reached" | Server isn't running, or it crashed. Look at its terminal. |
| Page loads but the dot is red | Server stopped. Restart `python server.py`. |
| Old behaviour after updating files | Restart the server (Ctrl+C, then run it again) and refresh the page |
| No `[MQTT] connected` line | Not on Cornell Wi-Fi, or a VPN/firewall is blocking port 1883 |
| `[MQTT] connection refused` | Wrong user/password |
| Pi actions do nothing | The server terminal prints `REJECTED: <reason>` for every message. No line at all = wrong topic/name (check `IDD/hotpotato/player/<name>/action`). |
| "nobody sits left of you" | That seat is empty (that player hasn't joined) |
| Catch never works on the Pi | Only send catch while `mode == "incoming"`. Pressing earlier = butterfingers lockout. |
| Pi screen frozen on an old picture | `piscreen.service` still running (`sudo systemctl stop piscreen.service`) or not subscribed to `.../player/<name>/state` |
| Teammates can't open the laptop IP | See **Friends can't open the link** below |
| `WARNING: another Hot Potato server` | Someone else is also running `server.py`. Stop one, or set `POTATO_TOPIC`. |

## Friends can't open the link

The Pis talk through the class broker, so they keep working. This is only about the **browser view** that friends load from your laptop (`http://<laptop-ip>:5000/<name>`). Try these in order:

**1. Use the right address.** Run `ipconfig` on the laptop and use the **Wi-Fi IPv4 address** (the server also prints all of them). Turn off the Cisco/Cornell VPN, since it changes the address and blocks local traffic. Type `http://` in full: some browsers quietly switch to `https://`, which won't work here.

**2. Open the Windows firewall for port 5000** (most common fix on eduroam, which Windows treats as a *Public* network). Open **PowerShell as Administrator** (Start → type PowerShell → right-click → Run as administrator):
```powershell
New-NetFirewallRule -DisplayName "Hot Potato 5000" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow -Profile Any
```
To undo it after the demo: `Remove-NetFirewallRule -DisplayName "Hot Potato 5000"`

**3. Mac browsers need "Local Network" permission** (macOS 15+): System Settings → Privacy & Security → **Local Network** → turn on Chrome (or whichever browser). Or just try **Safari**.

**4. Still nothing? The Wi-Fi blocks device-to-device traffic.** Use a free Cloudflare tunnel, which gives the game a public link that works from any network (no account needed):
```powershell
winget install --id Cloudflare.cloudflared
# open a NEW terminal, keep server.py running in the other one
cloudflared tunnel --url http://localhost:5000
```
It prints a link like `https://some-random-words.trycloudflare.com`. Friends open `https://some-random-words.trycloudflare.com/<their name>`. The link changes each time you start the tunnel, and it stops working when you close that terminal.

## User testing (lab deliverable: 2+ people not on your team)

Before they play: "What do you think this does?" While they play: note when they hesitate or ask questions. After:
- Was it clear when the potato was coming to you? When you had it?
- Was 1.5 s enough time to catch? Did the round timer add pressure?
- Did the red build-up make you feel rushed?
- Which input felt best / worst to throw and catch with?
- What would you change?
