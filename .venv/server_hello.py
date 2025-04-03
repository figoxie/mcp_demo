# coding=utf-8
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator, ValidationError
from typing import Dict, Any, List, Optional
import importlib
from functools import lru_cache
import mcp_handlers

# 创建 FastAPI 应用
app = FastAPI()

# --- MCP 核心协议 ---
class MCPModule(BaseModel):
    name: str
    description: str
    handler_path: str  # 格式: "module.submodule:function_name"

class MCPRequest(BaseModel):
    module: str
    params: Dict[str, Any]  # 动态参数（JSON 兼容格式）

    # Pydantic V2 参数校验 (替换旧的 @validator)
    @field_validator('params')
    @classmethod
    def validate_params(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(v, dict):
            raise ValueError("Params must be a dictionary")

        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError(f"Key '{key}' must be a string")
            if not isinstance(value, (int, float, str, bool, type(None))):
                raise ValueError(f"Value for key '{key}' has unsupported type: {type(value)}")
        return v

class MCPResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None

# --- 安全模块加载器 ---
@lru_cache(maxsize=None)
def load_handler(handler_path: str) -> callable:
    """安全加载预定义的函数"""
    try:
        module_path, func_name = handler_path.split(":")
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    except (ImportError, AttributeError,ValueError) as e:
        raise ValueError(f"Handler load failed: {str(e)}")

# --- 模块注册表（安全预定义） ---
MODULE_REGISTRY: Dict[str, MCPModule] = {
    "add": MCPModule(
        name="add",
        description="Sum two numbers",
        handler_path="mcp_handlers.basic_math:add"
    ),
    "multiply": MCPModule(
        name="multiply",
        description="Multiply two numbers",
        handler_path="mcp_handlers.basic_math:multiply"
    )
}

# --- MCP 协议接口 ---
@app.post("/mcp/execute", response_model=MCPResponse)
async def execute_module(request_data: Dict[str, Any]):
    try:
        # 校验请求数据是否符合词典
        request = MCPRequest.model_validate(request_data)  # Pydantic V2 语法
    except ValidationError as e:
        error_details = [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
        return MCPResponse(
            success=False,
            result="parse error",
            error=f"Invalid request: {'; '.join(error_details)}"
        )

    if request.module not in MODULE_REGISTRY:
        return MCPResponse(success=False,error="Module not found")
    try:
        handler = load_handler(MODULE_REGISTRY[request.module].handler_path)
        result = handler(**request.params)  # 安全调用预定义函数
        return MCPResponse(success=True, result=result)
    except Exception as e:
        return MCPResponse(success=False, error=str(e))


@app.get("/mcp/modules", response_model=List[MCPModule])
async def list_modules():
    return list(MODULE_REGISTRY.values())

# 运行服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000)