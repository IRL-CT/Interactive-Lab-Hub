# Simulated voter for a teammate whose Pi was not working.
# It waits until someone else votes, then joins a few seconds later.
import random, threading, time
import paho.mqtt.client as mqtt

TEAM = "IDD/huadiweilao"
NAME = "simone"
DELAY = (5, 12)   # seconds to wait after a human votes

voted = False
thinking = False

def vote_later(client):
    global voted, thinking
    time.sleep(random.uniform(*DELAY))
    client.publish(f"{TEAM}/vote/{NAME}", "1")
    voted = True
    thinking = False

def on_message(client, userdata, msg):
    global voted, thinking
    text = msg.payload.decode()
    if text == "BREAK TIME!":
        voted = False   # new round after the break
        return
    if text.split("/")[0].isdigit():   # status like "1/4 want a break: yan"
        count = int(text.split("/")[0])
        if count >= 1 and not voted and not thinking and NAME not in text:
            thinking = True
            threading.Thread(target=vote_later, args=(client,), daemon=True).start()

client = mqtt.Client(); client.username_pw_set("idd", "device@theFarm")
client.on_message = on_message
client.connect("farlab.infosci.cornell.edu", 1883)
client.subscribe(f"{TEAM}/status")
client.loop_forever()
