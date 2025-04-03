# coding=utf-8
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import httpx
import json
from pathlib import Path

app = FastAPI()


# --- 数据模型 ---
class MCPRequest(BaseModel):
    module: str
    params: Dict[str, Any]


class MCPResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


# --- 加载配置文件 ---
def load_config() -> Dict[str, Any]:
    config_path = Path(__file__).parent / "config" / "ms_modules.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config: {str(e)}")


# --- 调用微服务 ---
async def call_microservice(
        url: str,
        method: str,
        params: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "POST":
                response = await client.post(url, json=params)
            else:
                response = await client.get(url, params=params)

            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise ValueError(f"Microservice error: {e.response.text}")
    except Exception as e:
        raise ValueError(f"Request failed: {str(e)}")


# --- 主API接口 ---
@app.post("/api/execute", response_model=MCPResponse)
async def execute_module(request: MCPRequest):
    # 1. 读取配置
    config = load_config()

    # 2. 检查模块是否存在
    if request.module not in config:
        return MCPResponse(
            success=False,
            error=f"Module '{request.module}' not found. Available: {list(config.keys())}"
        )

    # 3. 调用微服务
    try:
        service_config = config[request.module]

        result = await call_microservice(
            url=service_config["url"],
            method=service_config["method"],
            params=request.params
        )

        return MCPResponse(success=True, result=result)
        #return MCPResponse(success=True, result=service_config["url"])

    except ValueError as e:
        return MCPResponse(success=False, error=str(e))
    except Exception as e:
        return MCPResponse(success=False, error=f"Internal error: {str(e)}")

# 定义请求数据模型
class AddRequest(BaseModel):
    num1: float
    num2: float

# 定义请求数据模型
class MultiplyRequest(BaseModel):
    num1: float
    num2: float

@app.post("/add")
async def add_numbers(request: AddRequest):
    result = request.num1 + request.num2
    return {"result": result}
@app.post("/multiply")
async def add_numbers(request: MultiplyRequest):
    result = request.num1 * request.num2
    return {"result": result}


# --- 启动服务 ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)