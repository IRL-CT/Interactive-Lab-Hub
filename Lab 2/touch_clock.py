#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
touch_time.py
MPR121 触摸 → 通过系统默认音频设备播报时间（推荐蓝牙音箱）。
依赖：
  - pip(venv): adafruit-circuitpython-mpr121
  - apt: espeak, alsa-utils(含 aplay)
硬件：
  - MPR121 (默认 I2C 地址 0x5A) 通过 Qwiic/STEMMA QT 接到 Pi 的 I2C (SDA/SCL)

运行前小检查：
  - sudo raspi-config → Interface Options → I2C: Enable
  - bluetoothctl 已 connect，且已把蓝牙音箱设为默认输出（pactl set-default-sink ...）
"""

import time
from datetime import datetime
import os
import shutil
import subprocess

import board
import busio
import adafruit_mpr121


# ============== 可调参数 ==============
I2C_ADDR = 0x5A          # MPR121 默认地址
TOUCH_CHANNELS = range(12)  # 0..11
COOLDOWN_SEC = 0.8       # 触发后冷却，避免连发
DEBOUNCE_SEC = 0.04      # 去抖采样间隔
TIME_FORMAT = "Now it is %I:%M %p"  # 12小时制；想用24小时制可改为 "%H:%M"
VOICE_CMD = "espeak"     # 或 "espeak-ng"（如果你装的是 espeak-ng）
APLAY_CMD = "aplay"      # ALSA 播放器
FALLBACK_BEEP = True     # 若未安装 espeak/aplay，则用 beep 占位(用 speaker-test)
# =====================================


def have_cmd(cmd: str) -> bool:
    """检查系统里是否存在某命令"""
    return shutil.which(cmd) is not None


def say_time():
    """播报当前时间；若 espeak/aplay 不可用，使用 beep 占位"""
    now = datetime.now()
    text = now.strftime(TIME_FORMAT)

    if have_cmd(VOICE_CMD) and have_cmd(APLAY_CMD):
        # 用 espeak 合成并通过 aplay 播放到默认输出（蓝牙音箱）
        # 使用 shell 管道最简单；若担心引号问题，可替换为生成临时 wav 再 aplay。
        safe_text = text.replace('"', r'\"')  # 简单转义
        cmd = f'{VOICE_CMD} "{safe_text}" --stdout | {APLAY_CMD}'
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[WARN] 语音播放失败（{e}），尝试 fallback beep …")
            if FALLBACK_BEEP:
                beep_once()
    else:
        print("[WARN] 未检测到 espeak/aplay，使用 fallback beep。")
        if FALLBACK_BEEP:
            beep_once()


def beep_once():
    """简易占位：发出一声短 beep（440Hz）"""
    if have_cmd("speaker-test"):
        # -t sine: 正弦波；-f 880: 频率；-l 1: 播放一段后退出
        subprocess.run("speaker-test -t sine -f 880 -l 1 >/dev/null 2>&1", shell=True)
    else:
        # 退而求其次：打印一行
        print("[BEEP] (speaker-test 未安装，控制台占位提示)")


def main():
    # 初始化 I2C & MPR121
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        mpr = adafruit_mpr121.MPR121(i2c, address=I2C_ADDR)
    except Exception as e:
        print("[ERROR] 无法初始化 MPR121。请检查：")
        print("  - I2C 是否在 raspi-config 中启用")
        print("  - Qwiic 线是否插牢，地址是否为 0x5A（或已修改）")
        print(f"  - 具体异常：{e}")
        return

    print("✅ 就绪：触摸任意电极（0-11）将播报当前时间。按 Ctrl+C 退出。")

    # 记录上一次触发时间，做全局冷却
    last_trigger_ts = 0.0

    # 为每个通道做简单“按下沿”检测，避免按住时连发
    prev_state = [False] * 12

    try:
        while True:
            # 周期性扫描
            for ch in TOUCH_CHANNELS:
                pressed = mpr[ch].value  # True = 正在触摸
                if pressed and not prev_state[ch]:
                    # 检测到“刚刚按下”
                    now_ts = time.time()
                    if now_ts - last_trigger_ts >= COOLDOWN_SEC:
                        print(f"[INFO] Touch on channel {ch} → announce time")
                        say_time()
                        last_trigger_ts = now_ts
                prev_state[ch] = pressed

            time.sleep(DEBOUNCE_SEC)
    except KeyboardInterrupt:
        print("\n👋 已退出。")


if __name__ == "__main__":
    main()
