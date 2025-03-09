"""Base Agent Module

This module contains the base agent class for Lyrebird automation.
"""

from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor
from langchain.agents.agent import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish
from langchain.prompts import StringPromptTemplate
from langchain.tools import BaseTool
from langchain.llms.base import BaseLLM

class LyrebirdAgent:
    """Base class for Lyrebird automation agents.
    
    This class provides the foundation for building specialized agents that can
    automate various Lyrebird operations and help with extension development.
    """
    
    def __init__(self, llm: BaseLLM, tools: List[BaseTool]):
        """Initialize the Lyrebird agent.
        
        Args:
            llm: The language model to use for the agent
            tools: List of tools available to the agent
        """
        self.llm = llm
        self.tools = tools
        self.agent_executor = None
        
    def initialize(self):
        """Initialize the agent with necessary components.
        
        This method should be called after instantiation to set up the agent's
        components like prompt templates, output parsers, and the executor.
        """
        raise NotImplementedError("Subclasses must implement initialize()")
        
    def run(self, input_text: str) -> Dict[str, Any]:
        """Execute the agent with the given input.
        
        Args:
            input_text: The user's input text/command
            
        Returns:
            Dict containing the agent's response and any relevant output
        """
        if not self.agent_executor:
            raise RuntimeError("Agent not initialized. Call initialize() first.")
            
        result = self.agent_executor.invoke({"input": input_text})
        return result["output"] if isinstance(result, dict) else result
    
    def add_tool(self, tool: BaseTool):
        """Add a new tool to the agent's toolkit.
        
        Args:
            tool: The tool to add
        """
        self.tools.append(tool)
        
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent's toolkit.
        
        Args:
            tool_name: Name of the tool to remove
        """
        self.tools = [t for t in self.tools if t.name != tool_name]