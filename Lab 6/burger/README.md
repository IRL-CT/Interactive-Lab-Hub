# Pan Burger：筆電伺服器 + 大螢幕

## 執行

```bash
cd "Lab 6"
python3 -m venv .venv
.venv/bin/pip install -r burger/requirements.txt
.venv/bin/python burger/server.py               # 接 farlab MQTT
.venv/bin/python burger/server.py --no-mqtt     # 只用鍵盤模擬器
```

打開 http://localhost:5050 ，選單人或雙人、選關卡，按「開店！」。
按 <kbd>`</kbd> 打開模擬器面板。

| | 模式 | 翻／切 | 丟給隊友 | 丟掉 | 卡片：麵包 起司 菜 肉 |
|---|---|---|---|---|---|
| P1 | Q | W | E | R | 1 2 3 4 |
| P2 | U | I | O | P | 6 7 8 9 |

## 鍋子 Pi 要送的 MQTT 訊息

Broker `farlab.infosci.cornell.edu:1883`，帳號 `idd`／`device@theFarm`。
Topic 前綴 `IDD/panburger/burger/`（可用 `--team` 改），`<pid>` 是 `p1` 或 `p2`。
內容可以是 JSON，也可以只送一個字。

| Topic | 內容 | 意思 |
|---|---|---|
| `<pid>/button` | `A` / `B` | A＝切換模式（煎鍋→砧板→組裝台），B＝丟掉目前工作站的東西 |
| `<pid>/mode` | `grill` / `board` / `assembly` | 直接指定模式 |
| `<pid>/card` | `bun` / `cheese` / `lettuce` / `meat` | 顏色感測器讀到的卡片（沒有盤子卡，切到組裝台會自動擺盤） |
| `<pid>/gesture` | `flip` / `chop` / `toss` | 往上甩／往桌上剁／往前甩 |

伺服器會回傳：

- `<pid>/feedback`：`{"sound": "ding", "msg": "肉煎好了！", "mode": "grill"}`，Pi 可以依 `sound` 播音效，依 `mode` 改螢幕顏色
- `game`（retained）：關卡、狀態、分數、剩餘時間

測試範例：

```bash
mosquitto_pub -h farlab.infosci.cornell.edu -u idd -P 'device@theFarm' \
  -t 'IDD/panburger/burger/p1/card' -m meat
```

## 鍋子（Pi）：`pi/pan.py`

硬體：APDS-9960（0x39）＋ 6 DoF LSM6DS3TR-C（0x6a），Qwiic 串接；Mini PiTFT 顯示模式顏色。

```bash
scp "Lab 6/burger/pi/pan.py" mypi:~/burger/          # 從筆電複製過去
sudo systemctl stop piscreen.service                 # 讓出螢幕
~/venv/bin/python ~/burger/pan.py --calibrate        # 第一次：校準 4 張食材卡，存成 cards.json
~/venv/bin/python ~/burger/pan.py --player p1        # 第二支鍋子用 --player p2
```

鍋子一直平拿。用 Mini PiTFT 的按鈕切換：**A 鍵＝上一個模式，B 鍵＝下一個模式，長按 B 一秒＝丟掉目前工作站的東西**，
順序是 煎鍋 → 砧板 → 組裝台 → 煎鍋。
（加 `--tilt` 可改回往右翻／往左翻切換；左右相反的話改 `pan.py` 的 `TILT_RIGHT_IS_NEGATIVE_Y`。）

| 模式 | 螢幕 | 動作 |
|---|---|---|
| 煎鍋 `grill` | 紅色 PAN | 往上甩＝翻面，往前甩＝丟給隊友 |
| 砧板 `board` | 綠色 KNIFE | 用力往下剁＝切 |
| 組裝台 `assembly` | 藍色 PLATE | 自動擺盤，拿卡片在感測器前 2–4 cm 掃 |

只重新校準某幾張卡：`pan.py --calibrate meat`（其他卡保留）。
看即時顏色讀數：`pan.py --watch-cards`。

選項：`--debug` 印出每個動作的數值，`--no-mqtt` 只印不送，`--no-display` 不用螢幕，`--team` 要和伺服器一致。

門檻值來自 `pi/recordings/motion_20261103_193039.csv`（用 `pi/record_motion.py` 錄的）。
在筆電上可以用 `python pi/replay.py pi/recordings/<檔案>.csv` 重播錄音，檢查判斷結果。
感測器換了安裝方向的話，重錄一次並調整 `pan.py` 最上面的 `AXES` 和門檻值。

## 規則

- 漢堡由下往上：麵包 → 配料（照客人的順序）→ 麵包。盤子不用卡片：鍋子放上桌（組裝台）就自動擺好
- 肉：煎鍋放肉卡，朝下那面熟了（60）就翻面，兩面都熟會自動進「煮好的」；朝下那面到 100 就燒焦（-3）
- 菜：砧板放菜卡，剁 5 下
- 起司：直接放
- 組裝時掃肉卡／菜卡，會用掉「煮好的」裡的一份；疊錯順序會被拒絕，不會用掉材料
- 疊完上麵包就自動出餐給訂單相同的顧客；客人等太久會生氣離開（-5）
- 單人模式：客人比較少、比較有耐心，不能丟給隊友
