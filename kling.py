#!/usr/bin/env python3
import requests
import json
import argparse
import os
import sys
import time
import base64
import hmac
import hashlib
import json as json_module


def load_config(config_file):
    """加载配置文件"""
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        sys.exit(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        sys.exit(1)


def encode_jwt_token(access_key, secret_key):
    """生成JWT token - 手动实现不依赖外部库"""
    
    # Header
    header = {
        "alg": "HS256",
        "typ": "JWT"
    }
    header_encoded = base64.urlsafe_b64encode(
        json_module.dumps(header, separators=(',', ':')).encode()
    ).decode().rstrip('=')
    
    # Payload
    payload = {
        "iss": access_key,
        "exp": int(time.time()) + 1800,  # 有效时间，当前时间+1800s(30min)
        "nbf": int(time.time()) - 5  # 开始生效的时间，当前时间-5秒
    }
    payload_encoded = base64.urlsafe_b64encode(
        json_module.dumps(payload, separators=(',', ':')).encode()
    ).decode().rstrip('=')
    
    # Signature
    message = f"{header_encoded}.{payload_encoded}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    signature_encoded = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    # JWT Token
    token = f"{header_encoded}.{payload_encoded}.{signature_encoded}"
    return token


def encode_image_to_base64(image_path):
    """将本地图片编码为base64"""
    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        sys.exit(1)
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        print(f"❌ 读取图片文件失败: {e}")
        sys.exit(1)


def submit_video_task(image_path, prompt, api_config, kling_config, custom_options=None):
    """提交视频生成任务"""
    # 编码图片为base64
    image_base64 = encode_image_to_base64(image_path)
    
    # 构建请求参数
    params = {
        "model_name": kling_config["kling_model_name"],
        "mode": kling_config["kling_mode"],
        "duration": kling_config["kling_duration"],
        "image": image_base64,
        "prompt": prompt,
        "cfg_scale": kling_config["kling_cfg_scale"]
    }
    
    # 如果有自定义参数，合并到默认参数中
    if custom_options:
        params.update(custom_options)
    
    # 生成JWT token
    jwt_token = encode_jwt_token(api_config['kling_access_key'], api_config['kling_secret_key'])
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}"
    }
    
    url = "https://api-beijing.klingai.com/v1/videos/image2video"
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(params))
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data["data"]["task_id"]
            else:
                print(f"❌ 提交失败，错误码: {data.get('code')}, 信息: {data.get('message')}")
        else:
            print(f"❌ HTTP错误: {resp.status_code}")
            print(f"响应内容: {resp.text}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None


def get_video_result(task_id, api_config, max_wait_time=600, interval=10):
    """获取视频生成结果"""
    start_time = time.time()
    
    url = f"https://api-beijing.klingai.com/v1/videos/image2video/{task_id}"
    
    while time.time() - start_time < max_wait_time:
        # 每次查询都生成新的JWT token（避免过期）
        jwt_token = encode_jwt_token(api_config['kling_access_key'], api_config['kling_secret_key'])
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}"
        }
        
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 0:
                    task_status = result["data"]["task_status"]
                    
                    if task_status == "succeed":
                        videos = result["data"]["task_result"]["videos"]
                        if videos:
                            print("✅ 视频生成成功！")
                            return videos[0]["url"]
                    elif task_status == "failed":
                        print(f"❌ 生成失败: {result['data'].get('task_status_msg', '未知错误')}")
                        return None
                    else:
                        print(f"⏳ 视频生成中...状态: {task_status}")
                else:
                    print(f"❌ 查询失败，错误码: {result.get('code')}, 信息: {result.get('message')}")
                    return None
            else:
                print(f"❌ HTTP错误: {resp.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            
        time.sleep(interval)
    
    print("❌ 超时: 视频生成超过最大等待时间")
    return None


def generate_video(image_path, prompt, api_config, kling_config, wait_for_result=True, custom_options=None):
    """一站式函数：提交任务并等待结果"""
    task_id = submit_video_task(image_path, prompt, api_config, kling_config, custom_options)
    if not task_id:
        print("❌ 提交任务失败")
        return None
    
    print(f"📌 任务已提交，ID: {task_id}")
    
    if wait_for_result:
        return get_video_result(task_id, api_config)
    else:
        return task_id


def main():
    parser = argparse.ArgumentParser(description='Kling AI 视频生成工具')
    parser.add_argument('image_path', help='输入图片路径')
    parser.add_argument('prompt', help='视频生成提示词')
    parser.add_argument('--api-config', default='config/api_config.json', help='API配置文件路径 (默认: config/api_config.json)')
    parser.add_argument('--kling-config', default='config/kling_config.json', help='Kling配置文件路径 (默认: config/kling_config.json)')
    parser.add_argument('--model-name', help='模型名称 (kling-v1, kling-v1-5, kling-v1-6, kling-v2-master, kling-v2-1, kling-v2-1-master)')
    parser.add_argument('--mode', choices=['std', 'pro'], help='生成模式 (std: 标准, pro: 专家)')
    parser.add_argument('--duration', choices=['5', '10'], help='视频时长 (5s 或 10s)')
    parser.add_argument('--cfg-scale', type=float, help='自由度 (0-1, 值越大与提示词相关性越强)')
    parser.add_argument('--no-wait', action='store_true', help='不等待结果，只返回任务ID')
    
    args = parser.parse_args()
    
    api_config = load_config(args.api_config)
    kling_config = load_config(args.kling_config)
    
    custom_options = {}
    if args.model_name:
        custom_options['model_name'] = args.model_name
    if args.mode:
        custom_options['mode'] = args.mode
    if args.duration:
        custom_options['duration'] = args.duration
    if args.cfg_scale is not None:
        custom_options['cfg_scale'] = args.cfg_scale
    
    wait_for_result = not args.no_wait
    
    result = generate_video(args.image_path, args.prompt, api_config, kling_config, wait_for_result, custom_options)
    
    if result:
        if wait_for_result:
            print(f"🎉 视频生成成功! 视频URL: {result}")
        else:
            print(f"📌 任务ID: {result}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()