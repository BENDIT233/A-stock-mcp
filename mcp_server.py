# Main MCP server file
import logging
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Import the interface and the concrete implementation
from src.data_source_interface import FinancialDataSource
from src.baostock_data_source import BaostockDataSource
from src.utils import setup_logging

# 导入各模块工具的注册函数
from src.tools.stock_market import register_stock_market_tools
from src.tools.financial_reports import register_financial_report_tools
from src.tools.indices import register_index_tools
from src.tools.market_overview import register_market_overview_tools
from src.tools.macroeconomic import register_macroeconomic_tools
from src.tools.date_utils import register_date_utils_tools
from src.tools.analysis import register_analysis_tools

# --- Logging Setup ---
# Call the setup function from utils
# You can control the default level here (e.g., logging.DEBUG for more verbose logs)
setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Dependency Injection ---
# Instantiate the data source - easy to swap later if needed
active_data_source: FinancialDataSource = BaostockDataSource()

# --- Get current date for system prompt ---
current_date = datetime.now().strftime("%Y-%m-%d")

# --- FastMCP App Initialization ---
app = FastMCP(
    name="a_share_data_provider"
)

# --- Authentication Middleware for HTTP Mode ---
@app.middleware("http")
async def auth_middleware(request, call_next):
    """
    认证中间件，用于HTTP模式下验证apiKey
    """
    # 获取请求头中的apiKey
    api_key = request.headers.get("x-api-key") or request.headers.get("authorization")
    
    # 如果提供了apiKey，进行验证（这里使用简单的验证逻辑）
    if api_key:
        # 移除可能的Bearer前缀
        if api_key.startswith("Bearer "):
            api_key = api_key[7:]
        
        # 简单的apiKey验证逻辑 - 在实际应用中应该使用更安全的验证方式
        if api_key == "sk-example123":  # 与smithery.yaml中的exampleConfig匹配
            response = await call_next(request)
            return response
        else:
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"}
            )
    
    # 如果没有提供apiKey，也允许访问（为了Smithery扫描工具能够正常工作）
    response = await call_next(request)
    return response

# --- 注册各模块的工具 ---
register_stock_market_tools(app, active_data_source)
register_financial_report_tools(app, active_data_source)
register_index_tools(app, active_data_source)
register_market_overview_tools(app, active_data_source)
register_macroeconomic_tools(app, active_data_source)
register_date_utils_tools(app, active_data_source)
register_analysis_tools(app, active_data_source)

# --- Main Execution Block ---
if __name__ == "__main__":
    import os
    import uvicorn
    
    # Check if running in HTTP mode (for Smithery deployment)
    if os.environ.get("PORT"):
        port = int(os.environ.get("PORT"))
        logger.info(f"Starting A-Share MCP Server on port {port}... Today is {current_date}")
        # Run the server using HTTP transport for Smithery deployment
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        logger.info(f"Starting A-Share MCP Server via stdio... Today is {current_date}")
        # Run the server using stdio transport, suitable for MCP Hosts like Claude Desktop
        app.run(transport='stdio')
