#Server.py
from fastmcp import FastMCP
from General_tools import general_tools_manager
from Mat_Sci_tools import Mat_sci_ToolManager

mcp = FastMCP("Scifi_Agent")
general_tools_manager(mcp)
Mat_sci_ToolManager(mcp)

if __name__ == "__main__":
    mcp.run()
