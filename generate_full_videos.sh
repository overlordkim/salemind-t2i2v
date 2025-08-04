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

echo "🎬 开始完整的图生视频流程，生成 $COUNT 个视频..."

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

# 确保static文件夹存在
mkdir -p static

# 生成时间戳用于文件夹命名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SESSION_DIR="static/session_$TIMESTAMP"
mkdir -p "$SESSION_DIR"

echo "📁 本次生成的文件将保存到: $SESSION_DIR"

# 生成视频
for ((i=1; i<=COUNT; i++)); do
    # 计算当前使用的prompt索引 (0-based)
    PROMPT_INDEX=$(((i-1) % PROMPT_COUNT))
    
    echo ""
    echo "==================== 第 $i/$COUNT 个视频 ===================="
    echo "🎯 使用prompt #$PROMPT_INDEX"
    
    # 获取当前prompt的image_prompt和video_prompt内容
    PROMPTS_DATA=$(python3 -c "
import sys
sys.path.append('config')
from prompts import prompts
prompt = prompts[$PROMPT_INDEX]
print(prompt['image_prompt'].strip())
print('---SEPARATOR---')
print(prompt['video_prompt'].strip())
")
    
    if [ $? -ne 0 ] || [ -z "$PROMPTS_DATA" ]; then
        echo "❌ 错误: 无法获取prompt #$PROMPT_INDEX 的内容"
        continue
    fi
    
    # 分离image_prompt和video_prompt
    IMAGE_PROMPT=$(echo "$PROMPTS_DATA" | sed '/---SEPARATOR---/q' | head -n -1)
    VIDEO_PROMPT=$(echo "$PROMPTS_DATA" | sed -n '/---SEPARATOR---/,$p' | tail -n +2)
    
    echo "🖼️  Image Prompt: ${IMAGE_PROMPT:0:100}..."
    echo "🎥 Video Prompt: ${VIDEO_PROMPT:0:100}..."
    
    # 文件命名
    FILE_PREFIX="video_$(printf "%03d" $i)_prompt_$(printf "%02d" $PROMPT_INDEX)"
    IMAGE_FILE="$SESSION_DIR/${FILE_PREFIX}.png"
    VIDEO_FILE="$SESSION_DIR/${FILE_PREFIX}.mp4"
    
    # 步骤1: 生成图片
    echo ""
    echo "🎨 步骤1: 生成图片..."
    IMAGE_URL=$(python3 liblib.py "$IMAGE_PROMPT")
    
    if [ $? -ne 0 ] || [ -z "$IMAGE_URL" ]; then
        echo "❌ 图片生成失败，跳过此视频"
        continue
    fi
    
    # 提取URL (liblib.py输出的最后一行应该包含URL)
    IMAGE_URL=$(echo "$IMAGE_URL" | grep -o 'https://[^[:space:]]*' | tail -1)
    
    if [ -z "$IMAGE_URL" ]; then
        echo "❌ 无法提取图片URL，跳过此视频"
        continue
    fi
    
    echo "📷 图片URL: $IMAGE_URL"
    
    # 步骤2: 下载图片
    echo "⬇️  下载图片到: $IMAGE_FILE"
    wget -q "$IMAGE_URL" -O "$IMAGE_FILE"
    
    if [ $? -ne 0 ] || [ ! -f "$IMAGE_FILE" ]; then
        echo "❌ 图片下载失败，跳过此视频"
        continue
    fi
    
    echo "✅ 图片下载完成"
    
    # 步骤3: 生成视频
    echo ""
    echo "🎬 步骤3: 生成视频..."
    VIDEO_OUTPUT=$(python3 kling.py "$IMAGE_FILE" "$VIDEO_PROMPT")
    
    if [ $? -ne 0 ]; then
        echo "❌ 视频生成失败"
        continue
    fi
    
    # 提取视频URL
    VIDEO_URL=$(echo "$VIDEO_OUTPUT" | grep -o 'https://[^[:space:]]*\.mp4' | tail -1)
    
    if [ -z "$VIDEO_URL" ]; then
        echo "❌ 无法提取视频URL"
        continue
    fi
    
    echo "🎥 视频URL: $VIDEO_URL"
    
    # 步骤4: 下载视频
    echo "⬇️  下载视频到: $VIDEO_FILE"
    wget -q "$VIDEO_URL" -O "$VIDEO_FILE"
    
    if [ $? -ne 0 ] || [ ! -f "$VIDEO_FILE" ]; then
        echo "❌ 视频下载失败"
        continue
    fi
    
    echo "✅ 视频下载完成"
    echo "📊 文件大小: $(du -h "$VIDEO_FILE" | cut -f1)"
    
    # 创建信息文件
    INFO_FILE="$SESSION_DIR/${FILE_PREFIX}_info.txt"
    cat > "$INFO_FILE" << EOF
生成时间: $(date)
Prompt索引: $PROMPT_INDEX
图片URL: $IMAGE_URL
视频URL: $VIDEO_URL

Image Prompt:
$IMAGE_PROMPT

Video Prompt:
$VIDEO_PROMPT
EOF
    
    echo "📄 信息文件已保存: $INFO_FILE"
    echo "🎉 第 $i 个视频完成！"
    
    # 如果不是最后一个视频，添加间隔
    if [ $i -lt $COUNT ]; then
        echo "⏳ 等待 10 秒后继续下一个..."
        sleep 10
    fi
done

echo ""
echo "🎉 所有视频生成完成！"
echo "📊 总计: $COUNT 个视频"
echo "📁 文件保存位置: $SESSION_DIR"
echo "📋 生成的文件:"
ls -la "$SESSION_DIR" | grep -E '\.(png|mp4|txt)$'