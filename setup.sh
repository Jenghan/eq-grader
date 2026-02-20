#!/bin/bash
set -e

echo "========================================="
echo "  EQ改作業小幫手 - 安裝設定"
echo "========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 Python3，請先安裝："
    echo "   brew install python3"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "❌ 找不到 Ollama，請先安裝："
    echo "   brew install ollama"
    echo "   或到 https://ollama.ai 下載"
    exit 1
fi
echo "✅ Ollama: $(ollama --version)"

# Create virtual environment
echo ""
echo "📦 建立 Python 虛擬環境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   建立完成"
else
    echo "   已存在，跳過"
fi

# Activate and install dependencies
echo ""
echo "📦 安裝 Python 套件..."
source venv/bin/activate
pip install -q -r requirements.txt
echo "   安裝完成"

# Check if Ollama is running
echo ""
echo "🔍 檢查 Ollama 服務..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama 服務已啟動"
else
    echo "⚠️  Ollama 服務未啟動，正在啟動..."
    ollama serve &
    sleep 3
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama 服務已啟動"
    else
        echo "❌ Ollama 啟動失敗，請手動執行: ollama serve"
        exit 1
    fi
fi

# Pull required model
echo ""
echo "🤖 檢查 AI 模型 (首次下載需要一些時間)..."
if ollama list | grep -q "qwen2.5:14b"; then
    echo "✅ qwen2.5:14b 模型已存在"
else
    echo "📥 正在下載 qwen2.5:14b 模型 (~8GB)..."
    echo "   這可能需要 10-30 分鐘，取決於網路速度"
    ollama pull qwen2.5:14b
    echo "✅ 模型下載完成"
fi

echo ""
echo "========================================="
echo "  ✅ 安裝完成！"
echo "========================================="
echo ""
echo "啟動方式："
echo "  source venv/bin/activate"
echo "  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "然後開啟瀏覽器前往："
echo "  學生頁面: http://localhost:8000/"
echo "  老師頁面: http://localhost:8000/teacher"
echo ""
