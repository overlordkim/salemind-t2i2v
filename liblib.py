#!/usr/bin/env python3
import hmac
from hashlib import sha1
import base64
import time
import uuid
import requests
import json
import argparse
import os
import sys


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




def generate_signature(uri, secret_key):
    """生成API调用所需的签名"""
    timestamp = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    content = f"{uri}&{timestamp}&{nonce}"
    digest = hmac.new(secret_key.encode(), content.encode(), sha1).digest()
    sign = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
    return {"signature": sign, "timestamp": timestamp, "signature_nonce": nonce}


def submit_image_task(prompt, api_config, model_config, custom_options=None):
    """提交图像生成任务"""
    params = {
        "templateUuid": model_config["liblib_template_uuid"],
        "generateParams": {
            "checkPointId": model_config["liblib_checkpoint_id"],
            "vaeId": model_config["liblib_vae_id"],
            "prompt": prompt,
            "clipSkip": model_config["liblib_clip_skip"],
            "steps": model_config["liblib_steps"],
            "width": model_config["liblib_width"],
            "height": model_config["liblib_height"],
            "imgCount": model_config["liblib_img_count"],
            "seed": model_config["liblib_seed"],
            "restoreFaces": model_config["liblib_restore_faces"],
            "additionalNetwork": model_config["liblib_additional_networks"]
        }
    }
    
    if custom_options:
        params["generateParams"].update(custom_options)
    
    uri = "/api/generate/webui/text2img"
    sign = generate_signature(uri, api_config["liblib_secret_key"])
    
    url_params = f"?AccessKey={api_config['liblib_access_key']}&Signature={sign['signature']}&Timestamp={sign['timestamp']}&SignatureNonce={sign['signature_nonce']}"
    url = "https://openapi.liblibai.cloud/api/generate/webui/text2img" + url_params
    
    headers = {"Content-Type": "application/json"}
    
    try:
        resp = requests.post(url, headers=headers, data=json.dumps(params))
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                return data["data"]["generateUuid"]
            else:
                print(f"❌ 提交失败，错误码: {data.get('code')}, 信息: {data.get('msg')}")
        else:
            print(f"❌ HTTP错误: {resp.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None


def get_image_result(uuid_, api_config, max_wait_time=180, interval=5):
    """获取图像生成结果"""
    uri = "/api/generate/webui/status"
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        sign = generate_signature(uri, api_config["liblib_secret_key"])
        url_params = f"?AccessKey={api_config['liblib_access_key']}&Signature={sign['signature']}&Timestamp={sign['timestamp']}&SignatureNonce={sign['signature_nonce']}"
        url = "https://openapi.liblibai.cloud/api/generate/webui/status" + url_params
        
        headers = {"Content-Type": "application/json"}
        
        try:
            resp = requests.post(url, headers=headers, json={"generateUuid": uuid_})
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 0:
                    status = result["data"]["generateStatus"]
                    images = result["data"].get("images", [])
                    
                    if images and images[0].get("auditStatus") == 3:
                        print("✅ 图片生成成功并通过审核！")
                        return images[0]["imageUrl"]
                    elif images:
                        print("⚠️ 图片未通过审核。")
                        return None
                    elif status in [4, 5]:
                        print("❌ 生成失败或被拦截")
                        return None
                    else:
                        print(f"⏳ 图片生成中...状态: {status}")
            else:
                print(f"❌ HTTP错误: {resp.status_code}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
            
        time.sleep(interval)
    
    print("❌ 超时: 图片生成超过最大等待时间")
    return None


def generate_image(prompt, api_config, model_config, wait_for_result=True, custom_options=None):
    """一站式函数：提交任务并等待结果"""
    task_id = submit_image_task(prompt, api_config, model_config, custom_options)
    if not task_id:
        print("❌ 提交任务失败")
        return None
    
    print(f"📌 任务已提交，ID: {task_id}")
    
    if wait_for_result:
        return get_image_result(task_id, api_config)
    else:
        return task_id


def main():
    parser = argparse.ArgumentParser(description='LibLib AI 图像生成工具')
    parser.add_argument('prompt', help='图像生成提示词')
    parser.add_argument('--api-config', default='config/api_config.json', help='API配置文件路径 (默认: config/api_config.json)')
    parser.add_argument('--model-config', default='config/model_config.json', help='模型配置文件路径 (默认: config/model_config.json)')
    parser.add_argument('--width', type=int, help='图像宽度')
    parser.add_argument('--height', type=int, help='图像高度')
    parser.add_argument('--steps', type=int, help='生成步数')
    parser.add_argument('--seed', type=int, help='随机种子')
    parser.add_argument('--no-wait', action='store_true', help='不等待结果，只返回任务ID')
    
    args = parser.parse_args()
    
    api_config = load_config(args.api_config)
    model_config = load_config(args.model_config)
    
    custom_options = {}
    if args.width:
        custom_options['width'] = args.width
    if args.height:
        custom_options['height'] = args.height
    if args.steps:
        custom_options['steps'] = args.steps
    if args.seed is not None:
        custom_options['seed'] = args.seed
    
    wait_for_result = not args.no_wait
    
    result = generate_image(args.prompt, api_config, model_config, wait_for_result, custom_options)
    
    if result:
        if wait_for_result:
            print(f"🎉 图像生成成功! 图像URL: {result}")
        else:
            print(f"📌 任务ID: {result}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()