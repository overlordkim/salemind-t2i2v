#!/bin/bash

# 检查参数
if [ $# -ne 1 ]; then
    echo "用法: $0 <生成视频数量>"
    echo "示例: $0 10"
    exit 1
fi

# 获取生成数量
COUNT=$1

# 检查参数是否为正整数
if ! [[ "$COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "❌ 错误: 生成数量必须为正整数"
    exit 1
fi

echo "🎬 开始生成 $COUNT 个视频..."

# 获取prompts总数
PROMPT_COUNT=$(python3 -c "
import sys
sys.path.append('config')
from prompts import prompts
print(len(prompts))
")

if [ $? -ne 0 ] || [ -z "$PROMPT_COUNT" ]; then
    echo "❌ 错误: 无法读取prompts.py文件"
    exit 1
fi

echo "📝 发现 $PROMPT_COUNT 个prompt配置"

# 默认图片路径
IMAGE_PATH="/home/kim/salemind/static/test.png"

# 检查图片是否存在
if [ ! -f "$IMAGE_PATH" ]; then
    echo "❌ 错误: 图片文件不存在: $IMAGE_PATH"
    exit 1
fi

# 生成视频
for ((i=1; i<=COUNT; i++)); do
    # 计算当前使用的prompt索引 (0-based)
    PROMPT_INDEX=$(((i-1) % PROMPT_COUNT))
    
    echo ""
    echo "🎥 正在生成第 $i/$COUNT 个视频 (使用prompt #$PROMPT_INDEX)..."
    
    # 获取当前prompt的video_prompt内容
    VIDEO_PROMPT=$(python3 -c "
import sys
sys.path.append('config')
from prompts import prompts
print(prompts[$PROMPT_INDEX]['video_prompt'].strip())
")
    
    if [ $? -ne 0 ] || [ -z "$VIDEO_PROMPT" ]; then
        echo "❌ 错误: 无法获取prompt #$PROMPT_INDEX 的内容"
        continue
    fi
    
    echo "📄 Prompt: $VIDEO_PROMPT"
    
    # 调用kling.py生成视频
    python3 kling.py "$IMAGE_PATH" "$VIDEO_PROMPT"
    
    if [ $? -eq 0 ]; then
        echo "✅ 第 $i 个视频生成完成"
    else
        echo "❌ 第 $i 个视频生成失败"
    fi
    
    # 如果不是最后一个视频，添加间隔
    if [ $i -lt $COUNT ]; then
        echo "⏳ 等待 5 秒后继续..."
        sleep 5
    fi
done

echo ""
echo "🎉 所有视频生成任务完成！"
echo "📊 总计: $COUNT 个视频"