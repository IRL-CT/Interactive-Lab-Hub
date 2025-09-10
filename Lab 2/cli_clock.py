from time import strftime, sleep
while True:
    print (strftime("%m/%d/%Y %H:%M:%S"), end="", flush=True)
    print("\r", end="", flush=True)
    sleep(1)
