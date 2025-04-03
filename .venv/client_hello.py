# coding=utf-8

import requests
import json

def main():
    # 查询可用模块
    print("Available modules:")
    modules = requests.get("http://localhost:5000/mcp/modules").json()
    for module in modules:
        print(f"- {module['name']}: {module['description']}")

    # 用户输入
    module_name = input("Enter module name: ")
    params = json.loads(input("Enter params (JSON): "))  # 例如: {"a": 5, "b": 3}

    # 发送 MCP 请求test
    responseRaw = (requests.post(
        "http://localhost:5000/mcp/execute",
        json={"module": module_name, "params": params}
    ))
    #print(responseRaw.text)
    response=responseRaw.json()

    # 处理响应
    if response["success"]:
        print(f"Result: {response['result']}")
    else:
        print(f"Error: {response['error']}")

if __name__ == "__main__":
    main()