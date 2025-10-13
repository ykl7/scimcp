#Server.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastmcp import FastMCP
from Tools.General_tools import general_tools_manager
from Tools.Mat_Sci_tools import Mat_sci_ToolManager
from Tools.Material_Project_tool import mp_manager

mcp = FastMCP("Scifi_Agent")
general_tools_manager(mcp)
materials_Toolmanager = Mat_sci_ToolManager(mcp) 
mp_manager(mcp)


if __name__ == "__main__":
    mcp.run()
