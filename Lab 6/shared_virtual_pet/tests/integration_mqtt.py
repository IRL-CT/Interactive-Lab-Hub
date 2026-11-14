"""Real local TCP MQTT integration, isolated from course broker. About one minute."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]

port, web_port = free_port(), free_port()
os.environ.update(MQTT_BROKER='127.0.0.1', MQTT_PORT=str(port), MQTT_USERNAME='', MQTT_PASSWORD='',
                  MQTT_PREFIX='test/sharedpet/' + uuid.uuid4().hex, MQTT_TLS='0')
from station import Station
from events import make_event

processes = []
log = tempfile.TemporaryFile(mode='w+')

def launch(*args):
    proc = subprocess.Popen([sys.executable,*args],cwd=ROOT,env=os.environ.copy(),stdout=log,stderr=log)
    processes.append(proc)
    return proc

def wait_for(predicate, timeout=20):
    until = time.monotonic() + timeout
    while time.monotonic() < until:
        if predicate(): return
        time.sleep(.1)
    raise AssertionError('Timed out waiting for expected condition')

def stop(proc):
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)
        try: proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait()

def cli(*args):
    subprocess.run([sys.executable,'simulate.py',*args],cwd=ROOT,check=True,timeout=25,stdout=log,stderr=log)

clients=[]
try:
    broker = launch('tests/local_broker.py','--port',str(port))
    engine = launch('pet_engine.py','--allow-simulation')
    launch('dashboard.py','--port',str(web_port))
    c = Station('integration'); clients.append(c); c.mqtt.start(); c.wait_ready(20)
    assert c.state['fullness'] == 40
    print('PASS initial state and broker connection',flush=True)
    # Actual single-command simulators, including sensor-free station flag.
    cli('--role','feed')
    wait_for(lambda:c.state['fullness']==60)
    subprocess.run([sys.executable,'sensor_client.py','--role','play','--simulate','--no-display'],
                   cwd=ROOT,check=True,timeout=25,stdout=log,stderr=log)
    wait_for(lambda:c.state['happiness']==60)
    cli('--role','rest'); wait_for(lambda:c.state['energy']==60)
    print('PASS all three role CLIs',flush=True)
    time.sleep(3.1)
    e=make_event('feed','sim-feed',c.state['round_id'],True)
    c.mqtt.publish('event/feed',e,wait=True)
    wait_for(lambda:c.state['fullness']==80)
    c.mqtt.publish('event/feed',e,wait=True)
    time.sleep(.4)
    assert c.state['fullness']==80
    c.mqtt.publish('event/feed',{'event':'bogus'},wait=True)
    cli('--role','play'); cli('--role','rest')
    wait_for(lambda:c.state['mood']=='happy')
    wait_for(lambda:c.state['status']=='won',15)
    frozen=[c.state[k] for k in ('fullness','happiness','energy')]
    cli('--role','feed'); time.sleep(1.1)
    assert frozen==[c.state[k] for k in ('fullness','happiness','energy')]
    print('PASS duplicate rejection, malformed input, victory and frozen round',flush=True)
    late=Station('late-display'); clients.append(late); late.mqtt.start(); late.wait_ready()
    assert late.state['round_id']==c.state['round_id'] and late.state['status']=='won'
    with urllib.request.urlopen(f'http://127.0.0.1:{web_port}/api/state') as response:
        web=json.load(response)
    assert web['state']['status']=='won' and web['fresh']
    print('PASS late subscriber and Flask dashboard MQTT synchronization',flush=True)
    old_round=c.state['round_id']
    cli('--reset'); wait_for(lambda:c.state['round_id']!=old_round)
    assert c.state['fullness']==40
    wait_for(lambda:c.state['fullness']==39,18)
    print('PASS reset and actual 15-second decay',flush=True)
    stop(broker)
    wait_for(lambda:not c.mqtt.connected.is_set(),20)
    broker=launch('tests/local_broker.py','--port',str(port))
    wait_for(lambda:c.snapshot()['connected'] and c.snapshot()['fresh'],25)
    cli('--role','feed')
    wait_for(lambda:c.state['last_action']=='feed')
    print('PASS broker restart, automatic reconnect, resubscription and action after recovery',flush=True)
    duplicate=subprocess.run([sys.executable,'pet_engine.py'],cwd=ROOT,capture_output=True,text=True,timeout=5)
    assert duplicate.returncode==1 and 'already running' in duplicate.stderr
    print('PASS same-machine engine lock',flush=True)
    print('ALL MQTT INTEGRATION CHECKS PASSED',flush=True)
except Exception:
    log.seek(0)
    print(log.read()[-12000:])
    raise
finally:
    for client in clients: client.mqtt.close()
    for process in reversed(processes): stop(process)
    log.close()
