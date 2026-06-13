#!/bin/bash
# 运行 MUNDO Agent 测试

set -e

echo "🧪 运行 MUNDO Agent 单元测试..."
echo ""

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 运行测试
python -m pytest tests/ -v --tb=short "$@"

echo ""
echo "✅ 测试完成！"