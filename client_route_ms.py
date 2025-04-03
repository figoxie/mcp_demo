# coding=utf-8
import httpx
import json
import requests
from typing import Dict, Any
from pathlib import Path

# 客户端配置
SERVER_URL = "http://localhost:5001/api/execute"


async def call_mcp_server(module: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """调用 MCP 服务器接口"""
    try:
        async with httpx.AsyncClient(headers={"User-Agent": "python-requests/2.26.0"}) as client:
            response = await client.post(
                "http://localhost:8000/api/execute",
                json={"module": module, "params": params},
                headers={"Content-Type": "application/json"}  # 明确指定头部
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP Error: {e.response.text}"}
    except Exception as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}


async def main():
    print("可用模块示例: add, multiply (根据服务端配置)")
    module = input("请输入模块名: ")

    # 输入参数（JSON 格式）
    params_str = input("请输入参数 (JSON 格式，如 {\"a\": 5, \"b\": 3}): ") #示例：{"num1": 5, "num2": 3}
    try:
        params = json.loads(params_str)
    except json.JSONDecodeError:
        print("错误: 参数必须是有效的 JSON 格式")
        return

    # 调用服务器
    result = await call_mcp_server(module, params)

    # 打印结果
    if result.get("success"):
        print(f"\n结果: {result['result']}")
    else:
        print(f"\n错误: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())