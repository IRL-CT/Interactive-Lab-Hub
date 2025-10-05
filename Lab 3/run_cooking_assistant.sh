#!/bin/bash

echo "启动烹饪助手..."
echo "请确保："
echo "1. Ollama服务正在运行 (ollama serve)"
echo "2. tinyllama模型已下载 (ollama pull tinyllama)"
echo "3. 树莓派按钮已正确连接"
echo ""

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "已激活虚拟环境"
fi

# 运行烹饪助手
python3 cooking_assistant.py
