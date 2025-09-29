#Server.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastmcp import FastMCP
from Tools.General_tools import general_tools_manager
from Tools.Mat_Sci_tools import Mat_sci_ToolManager

mcp = FastMCP("Scifi_Agent")
general_tools_manager(mcp)
Mat_sci_ToolManager(mcp)

if __name__ == "__main__":
    mcp.run()
