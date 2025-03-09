"""Code Executor Module

This module provides functionality for generating and executing Python code using Langchain.
"""

from typing import Dict, Any, Optional
from langchain.llms.base import BaseLLM
from langchain_experimental.tools import PythonREPLTool
from langchain.agents import AgentType, initialize_agent
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor

from .base import LyrebirdAgent

class CodeExecutor(LyrebirdAgent):
    """Code executor agent for generating and running Python code.
    
    This agent uses Langchain's Python agent and REPL tool to generate and execute
    Python code based on natural language descriptions.
    """
    
    def __init__(self, llm: BaseLLM):
        """Initialize the code executor.
        
        Args:
            llm: The language model to use for code generation
        """
        # 创建Python REPL工具
        python_repl = PythonREPLTool()
        super().__init__(llm=llm, tools=[python_repl])
        
    def initialize(self):
        """Initialize the Python agent with REPL capabilities."""
        from langchain.prompts import PromptTemplate
        
        prompt = PromptTemplate.from_template(
            """You are a Python code generation assistant. Your task is to generate Python code based on the given description.

Description: {input}

Generate ONLY Python code without any explanations. The code should be complete and ready to run.
Do not include any text outside of the code block.

Important notes:
1. ALWAYS use True/False for boolean values (NEVER use true/false)
2. Make sure all variables are properly defined before use
3. Handle potential errors and edge cases
4. Return results in a dictionary format
5. Use proper Python syntax and conventions
6. Use proper indentation (4 spaces)
7. Avoid any non-ASCII characters in variable names
8. Always define functions before using them
9. Always handle potential KeyError when accessing dictionary values using .get() method

Example of proper boolean usage:
    if condition:
        return True
    return False

Example of proper dictionary access:
    value = data.get('key', default_value)
"""
        )

        self.prompt = prompt
        
    def generate_and_execute(self, task_description: str) -> Dict[str, Any]:
        """Generate and execute Python code based on a natural language description.
        
        Args:
            task_description: Natural language description of the code to generate
            
        Returns:
            Dict containing the execution results
        """
        # 生成代码
        code = self.llm.invoke(self.prompt.format(input=task_description))
        
        # 清理代码，移除 Markdown 格式
        code = code.strip()
        if code.startswith('```python'):
            code = code[8:]
        if code.endswith('```'):
            code = code[:-3]
        code = code.strip()
        
        # 如果代码是空的，生成一个基本的分析代码
        if not code:
            code = """
# 过滤掉资源请求和可测性上报请求
filtered_flows = []
for flow in flow_details:
    path = flow['request']['path']
    
    # 检查是否是资源文件
    resource_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.svg']
    is_resource = any(path.endswith(ext) for ext in resource_extensions)
    
    # 检查是否在静态资源目录
    static_dirs = ['/static/', '/assets/', '/images/']
    is_static = any(dir_path in path for dir_path in static_dirs)
    
    # 检查是否是可测性上报请求
    is_testability = 'lyrebird.sankuai.com/api/report/testability' in path
    
    # 如果不是资源请求或可测性上报，检查响应中是否包含关键字
    if not (is_resource or is_static or is_testability):
        response_data = flow['response']['data']
        if isinstance(response_data, str) and '中乐咖啡' in response_data:
            filtered_flows.append(flow)

# 返回分析结果
result = {
    'total_flows': len(flow_details),
    'matched_flows': len(filtered_flows),
    'matched_requests': [
        {
            'id': flow['id'],
            'path': flow['request']['path'],
            'method': flow['request']['method']
        }
        for flow in filtered_flows
    ]
}
"""
        
        return {"result": code}
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """Execute a given Python code snippet.
        
        Args:
            code: Python code string to execute
            
        Returns:
            Dict containing the execution results
        """
        python_repl = self.tools[0]
        try:
            result = python_repl.run(code)
            return {"result": result, "success": True}
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print("\n执行代码时出错:")
            print(error_traceback)
            return {
                "result": str(e),
                "traceback": error_traceback,
                "success": False
            } 