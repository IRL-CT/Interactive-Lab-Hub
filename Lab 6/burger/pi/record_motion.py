"""
Record motion data from the pan (LSM6DS3TR-C 6-DoF + APDS-9960) to a CSV,
so we can pick thresholds for poses (pan / knife / on the table) and
gestures (flip / chop / toss) from real data.

Run on the Pi:
    ~/venv/bin/python record_motion.py
    ~/venv/bin/python record_motion.py --only pan_flip knife_chop   # redo some steps

Each step waits for Enter, counts down, then records. The CSV goes to
recordings/motion_<time>.csv with one row per sample:
    t, step, ax, ay, az (m/s^2), gx, gy, gz (rad/s), prox
"""

import argparse
import csv
import math
import os
import sys
import time

import board
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_lsm6ds import AccelRange, GyroRange, Rate
from adafruit_lsm6ds.lsm6ds3trc import LSM6DS3TRC

RATE_HZ = 100

# (name, seconds, what to do)
STEPS = [
    ('pan_still',    4,  '拿成「鍋子」的樣子，靜止不動'),
    ('pan_flip',     12, '拿成鍋子，翻鍋 5 次（每次之間停一下）'),
    ('pan_toss',     12, '拿成鍋子，往前甩 5 次（把東西丟給隊友的動作）'),
    ('pan_wander',   10, '拿成鍋子隨便走動、晃一晃，但「不要」翻也不要甩（用來找誤判）'),
    ('knife_still',  4,  '拿成「菜刀」的樣子，靜止不動'),
    ('knife_chop',   12, '拿成菜刀，往下剁 5 次（每次之間停一下）'),
    ('knife_wander', 10, '拿成菜刀隨便晃一晃，但「不要」剁'),
    ('table',        6,  '放在桌上（組裝台的姿勢），放好就不要碰'),
    ('table_cards',  10, '放在桌上，拿卡片在感測器上方晃幾下（看放卡片會不會讓它以為被移動）'),
    ('switch',       15, '依序切換：鍋子 → 菜刀 → 放桌上 → 拿起來當鍋子，每個姿勢停 2 秒'),
]


def setup_sensors():
    i2c = board.I2C()
    imu = LSM6DS3TRC(i2c)
    # Flips and chops are violent: widen the ranges so they don't clip.
    imu.accelerometer_range = AccelRange.RANGE_16G
    imu.gyro_range = GyroRange.RANGE_2000_DPS
    imu.accelerometer_data_rate = Rate.RATE_208_HZ
    imu.gyro_data_rate = Rate.RATE_208_HZ
    apds = APDS9960(i2c)
    apds.enable_proximity = True
    return imu, apds


def record(imu, apds, step, seconds, writer, t0):
    period = 1.0 / RATE_HZ
    end = time.monotonic() + seconds
    next_t = time.monotonic()
    n = 0
    max_a = max_g = 0.0
    while time.monotonic() < end:
        ax, ay, az = imu.acceleration
        gx, gy, gz = imu.gyro
        prox = apds.proximity
        now = time.monotonic()
        writer.writerow([f'{now - t0:.3f}', step, f'{ax:.3f}', f'{ay:.3f}', f'{az:.3f}',
                         f'{gx:.3f}', f'{gy:.3f}', f'{gz:.3f}', prox])
        n += 1
        max_a = max(max_a, math.sqrt(ax * ax + ay * ay + az * az))
        max_g = max(max_g, math.sqrt(gx * gx + gy * gy + gz * gz))
        left = int(end - now) + 1
        sys.stdout.write(f'\r  錄製中… 剩 {left:2d} 秒   |a| {max_a:5.1f}   |g| {max_g:5.1f}  ')
        sys.stdout.flush()
        next_t += period
        delay = next_t - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        else:
            next_t = time.monotonic()
    rate = n / seconds
    print(f'\r  完成：{n} 筆（{rate:.0f} Hz），最大加速度 {max_a:.1f} m/s²，最大轉速 {max_g:.1f} rad/s   ')


def main():
    # ssh sessions on the Pi may not have a UTF-8 locale; print Chinese anyway.
    sys.stdout.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*', help='只錄這幾個步驟：' + ' '.join(s[0] for s in STEPS))
    args = ap.parse_args()

    steps = [s for s in STEPS if not args.only or s[0] in args.only]
    if not steps:
        sys.exit('沒有符合的步驟')

    imu, apds = setup_sensors()
    os.makedirs('recordings', exist_ok=True)
    path = os.path.join('recordings', time.strftime('motion_%Y%m%d_%H%M%S.csv'))

    print(f'會錄 {len(steps)} 個步驟，存到 {path}')
    print('每一步：看說明 → 擺好姿勢 → 按 Enter → 倒數 3 秒後開始錄\n')

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['t', 'step', 'ax', 'ay', 'az', 'gx', 'gy', 'gz', 'prox'])
        t0 = time.monotonic()
        for i, (name, seconds, what) in enumerate(steps, 1):
            print(f'[{i}/{len(steps)}] {name}（{seconds} 秒）：{what}')
            try:
                answer = input('  準備好按 Enter（輸入 s 再按 Enter 跳過）… ')
            except EOFError:
                return
            if answer.strip().lower() == 's':
                print('  跳過\n')
                continue
            for c in (3, 2, 1):
                sys.stdout.write(f'\r  {c}… ')
                sys.stdout.flush()
                time.sleep(1)
            record(imu, apds, name, seconds, writer, t0)
            f.flush()
            print()

    print(f'全部完成！檔案：{os.path.abspath(path)}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n中斷了，已錄的部分有存起來。')
