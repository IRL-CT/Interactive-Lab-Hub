import paho.mqtt.client as mqtt
import time
import random

# --- MQTT 設定 ---
BROKER = "farlab.infosci.cornell.edu"
PORT = 1883
USER = "idd"
PASS = "device@theFarm"
CLIENT_ID = "game_master_server"

# --- 遊戲設定 ---
TARGET_COLORS = ["RED", "GREEN", "BLUE"]
PLAYER_TOPIC = "IDD/game/hunt/player_found"
MASTER_TOPIC = "IDD/game/hunt/master"
WINNER_TOPIC = "IDD/game/hunt/winner"

# --- 遊戲狀態變數 ---
current_target_color = None
round_winner = None 

# --- MQTT 回調 (Callback) ---
def on_connect(client, userdata, flags, rc):
    print(f"Connected to broker with result code {rc}")
    # 訂閱玩家的「搶答」頻道
    client.subscribe(PLAYER_TOPIC)

def on_message(client, userdata, msg):
    global round_winner
    
    # 檢查是否已經有勝利者 (避免多人同時獲勝)
    if round_winner is None:
        player_name = msg.payload.decode()
        print(f"WINNER DETECTED: {player_name}")
        
        # 設置勝利者
        round_winner = player_name
        
        # 廣播勝利者
        winner_message = f"{player_name} wins this round!"
        client.publish(WINNER_TOPIC, winner_message)

# --- 主程式 ---
client = mqtt.Client(CLIENT_ID)
client.username_pw_set(USER, PASS)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start() # 在背景線程中處理 MQTT

print("Game Master is running...")

try:
    while True:
        # 1. 重置回合狀態
        round_winner = None
        
        # 2. 選擇並發布新顏色
        current_target_color = random.choice(TARGET_COLORS)
        print(f"\n--- NEW ROUND ---")
        print(f"Telling players to find: {current_target_color}")
        client.publish(MASTER_TOPIC, current_target_color)
        
        # 3. 等待勝利者出現 (on_message 會處理)
        # 這裡我們給玩家 10 秒鐘時間
        start_time = time.time()
        while round_winner is None and (time.time() - start_time) < 10:
            time.sleep(0.1)
            
        # 4. 如果 10 秒後沒人獲勝
        if round_winner is None:
            print("Time's up! No winner this round.")
            client.publish(WINNER_TOPIC, "Time's up! No winner.")

        # 5. 等待 3 秒進入下一輪
        print("Next round in 3 seconds...")
        time.sleep(3)

except KeyboardInterrupt:
    print("Game shutting down...")
    client.loop_stop()
    client.disconnect()
