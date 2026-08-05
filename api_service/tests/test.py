# POST形式
import requests

# 配置参数
base_url = "http://127.0.0.1:8000/v1"  # Open‑WebUI 默认端口3000，接口前缀 /api/v1
api_key = "da_6m2iFz9F_w9NUl3xRZmKelZtokAd5Ee0VzVWzpBKegw"
model_name = "deep-agents"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": model_name,
    "messages": [
        {"role": "user", "content": "把以下项目会议纪要整理成待办事项：1. 李明本周五前完成登录页面。2. 王芳下周一前确认支付接口方案。3. 测试环境暂定周三部署，负责人待确认。"}
    ],
    "stream": False
}

# 发起请求
resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload)

# 打印返回结果
print(resp.status_code)
print(resp.json())