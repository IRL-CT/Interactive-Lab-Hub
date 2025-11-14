import paho.mqtt.client as mqtt
import time
from adafruit_apds9960.apds9960 import APDS9960
import board

# --- 感測器設定 ---
i2c = board.I2C()
apds = APDS9960(i2c)
apds.enable_color = True

# --- MQTT 設定 ---
BROKER = "farlab.infosci.cornell.edu"
PORT = 1883
USER = "idd"
PASS = "device@theFarm"
PLAYER_NAME = "Pi_1_Ariel" # !! 每個 Pi 都要改成自己的名字 !!
CLIENT_ID = f"player_{PLAYER_NAME}"

# --- 訂閱的 Topics ---
MASTER_TOPIC = "IDD/game/hunt/master"
WINNER_TOPIC = "IDD/game/hunt/winner"
# --- 發布的 Topic ---
PLAYER_TOPIC = "IDD/game/hunt/player_found"

# --- 遊戲狀態變數 ---
current_target_color = None
i_have_won_this_round = False

# --- 顏色判斷邏輯 ---
def check_color_match(r, g, b, target_color):
    if target_color is None:
        return False
    
    # 簡易的顏色判斷 (你們可以調整閾值)
    if target_color == "RED" and r > 150 and g < 60 and b < 60:
        return True
    if target_color == "GREEN" and g > 150 and r < 60 and b < 60:
        return True
    if target_color == "BLUE" and b > 150 and r < 60 and g < 60:
        return True
    return False

# --- MQTT 回調 (Callback) ---
def on_connect(client, userdata, flags, rc):
    print(f"Connected as {PLAYER_NAME} with code {rc}")
    # 訂閱遊戲主持人的指令
    client.subscribe(MASTER_TOPIC)
    client.subscribe(WINNER_TOPIC)

def on_message(client, userdata, msg):
    global current_target_color, i_have_won_this_round
    
    payload = msg.payload.decode()
    
    if msg.topic == MASTER_TOPIC:
        # 收到新回合的目標
        current_target_color = payload
        i_have_won_this_round = False # 重置狀態
        print(f"*** New Target: Find [{current_target_color}]! ***")
        # 可以在這裡更新 Pi 的螢幕
        
    elif msg.topic == WINNER_TOPIC:
        # 收到勝利者廣播
        print(f"*** Game Status: {payload} ***")
        current_target_color = None # 停止感測，直到下一輪

# --- 主程式 ---
client = mqtt.Client(CLIENT_ID)
client.username_pw_set(USER, PASS)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start()

print(f"Player {PLAYER_NAME} is ready...")

try:
    while True:
        # 只有在有目標顏色，且我還沒贏的時候，才進行感測
        if current_target_color is not None and not i_have_won_this_round:
            
            # 讀取顏色
            r, g, b, c = apds.color_data
            # print(f"Sensing: R={r}, G={g}, B={b}") # Debug 用
            
            # 檢查是否匹配
            if check_color_match(r, g, b, current_target_color):
                print(f"MATCH FOUND! I see {current_target_color}!")
                
                # 標記我已經贏了，避免重複發送
                i_have_won_this_round = True 
                
                # 發送搶答訊息！
                client.publish(PLAYER_TOPIC, PLAYER_NAME)
        
        time.sleep(0.1) # 避免過於頻繁

except KeyboardInterrupt:
    print("Player shutting down...")
    client.loop_stop()
    client.disconnect()