"""Flow Code Analyzer Module

This module combines flow analysis with code generation and execution capabilities.
"""

from typing import Dict, Any, List, Optional
from .flow import FlowTools
from .code_executor import CodeExecutor
from langchain.llms.base import BaseLLM
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import json

class FlowCodeAnalyzer:
    """结合流量分析和代码生成执行的分析器类"""
    
    def __init__(self, llm: BaseLLM, llm_config: Dict[str, Any] = None):
        """初始化分析器
        
        Args:
            llm: 用于代码生成的语言模型
            llm_config: LLM配置，用于embeddings
        """
        self.flow_tools = FlowTools()
        self.code_executor = CodeExecutor(llm=llm)
        self.code_executor.initialize()
        self.llm = llm
        
        if llm_config:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=llm_config['api_key'],
                openai_api_base=llm_config['api_base']
            )
            self.vector_store = None
        
    def _extract_flow_data(self, flow_id: str) -> Dict[str, Any]:
        """提取单个流量的详细数据
        
        Args:
            flow_id: 流量ID
            
        Returns:
            流量详细数据
        """
        detail = self.flow_tools.get_flow_detail(flow_id)
        return {
            'id': flow_id,
            'request': detail['data']['request'],
            'response': detail['data']['response']
        }
        
    def analyze_flows_with_code(self, query: str, limit = None) -> Dict[str, Any]:
        """使用代码分析流量数据
        
        Args:
            query: 用户查询内容，用于生成分析代码
            limit: 分析最近的流量数量
            
        Returns:
            分析结果
        """
        # 1. 获取流量数据
        flows = self.flow_tools.get_flow_list()
        recent_flows = flows[:]
        
        # 2. 提取流量详细信息
        flow_details = []
        for flow in recent_flows:
            flow_id = flow.get('id')
            if flow_id:
                flow_details.append(self._extract_flow_data(flow_id))
        
        print(query)
        
        # 3. 构建代码生成提示
        code_prompt = f"""
基于以下用户需求，生成Python代码来初步过滤流量数据：
用户需求: {query}

你将获得一个名为 flow_details 的列表，每个元素包含以下结构：
{{
    'id': '流量ID',
    'request': {{
        'method': 'HTTP方法',
        'path': '请求路径',
        'query': {{}},  # 查询参数
        'headers': {{}},  # 请求头
        'data': ''  # 请求体,可能为以下几种类型:空、字典、字符串、列表、base64编码字符串
    }},
    'response': {{
        'code': 状态码,
        'data': ''  # 响应体,可能为以下几种类型:空、字典、字符串、列表、base64编码字符串
    }}
}}

请注意:
1. flow_details中的数据可能为空，请先进行数据过滤。
2. data 部分可能为经过 json.dumps 处理过后的json 字符串，请先尝试进行 json 转换。

过滤策略说明：
1. 基础过滤：
   - 过滤掉路径以 .js、.css、.png、.jpg、.jpeg、.gif、.ico、.woff、.woff2、.ttf、.eot、.svg 等资源文件后缀结尾的请求
   - 过滤掉静态资源文件夹下的请求（如 /static/、/assets/、/images/ 等）
   - 过滤掉可测性上报请求（URL 中包含 'lyrebird.sankuai.com/api/report/testability' 的请求）

2. 关键词过滤：
   - 关键词提取规则：
     * 仅提取用户需求中被<<>>包裹的内容作为关键词
     * 例如："请帮我找出所有包含<<dealList>>的请求" -> 提取关键词 "dealList"
     * 例如："请帮我找出所有和餐厅相关的请求" -> 不提取任何关键词
   - 关键词使用规则：
     * 如果用户需求中没有<<>>包裹的内容，则不进行关键词过滤
     * 如果用户需求中有多个<<>>包裹的内容，则提取所有关键词并使用它们进行过滤
   - 代码实现要求：
     * 如果没有提取到任何关键词，则完全跳过关键词过滤步骤
     * 不要添加任何用户未通过<<>>明确指定的关键词

3. 数据特征过滤：
   - 如果用户查询涉及商品列表、店铺信息等数据，优先选择：
     * response.data 为 JSON 格式的请求
     * response.data 中包含较长的列表或复杂的字典结构
     * response.code 为 200 的请求
   - 如果用户未明确要求数据特征，则不应使用此过滤条件

4. 智能匹配：
   - 当没有关键词过滤时，应该基于以下特征进行智能匹配：
     * 分析请求路径中的语义特征（如 api、v1、list、detail 等）
     * 分析响应数据的结构特征（如是否包含列表、是否包含商品相关字段）
     * 响应数据中是否包含典型的业务字段（如 id、name、price、description 等）

5. 生成的函数名
    - 生成代码中入口函数应为 main

请生成代码来初步过滤这些数据。代码应该返回一个字典，包含以下结构：
{{
    'filtered_flows': [  # 过滤后的流量列表
        {{
            'id': '流量ID',
            'request_info': '请求概要信息',  # 包含方法、路径等关键信息
            'request_data': request_dict,  # 完整的请求数据
            'response_data': response_dict,  # 完整的响应数据
            'match_reason': '匹配原因'  # 说明该请求为什么被选中，例如：包含关键词"商品"，响应包含商品列表等
        }}
    ],
    'filter_summary': {{  # 过滤统计信息
        'total_requests': 0,  # 总请求数
        'filtered_count': 0,  # 过滤后的请求数
        'filter_criteria': []  # 使用的过滤条件列表
    }}
}}
"""
        
        # 4. 生成并执行过滤代码
        generated_code = self.code_executor.generate_and_execute(code_prompt)
        print("\n生成的过滤代码:")
        print(generated_code['result'][1:])

        
        # 5. 执行生成的代码
        analysis_code = f"""
flow_details = {flow_details}
user_request = "{query}"
{generated_code['result'][1:]}

# 添加实际调用代码
result = main(flow_details, user_request)
print(result)  # 打印结果用于调试
"""
        filtered_result = self.code_executor.execute_code(analysis_code)
        
        # 6. 使用 LLM 进行深度分析
        analysis_prompt = f"""
基于用户的查询需求：{query}

请分析以下经过初步过滤的流量数据，并提供详细的分析结果：
{filtered_result}

请重点关注：
1. 流量是否符合用户的查询需求
2. 请求和响应中的关键信息
3. 数据的业务含义
4. 可能存在的异常情况

请以结构化的方式返回分析结果，包括：
1. 符合条件的流量数量
2. 每个流量的关键信息分析
3. 总体结论
"""
        
        final_analysis = self.llm.predict(analysis_prompt)
        
        return {
            'filtered_data': filtered_result,
            'analysis': final_analysis
        }

def main():
    """使用示例"""
    from agent import llmapi
    
    # 创建分析器实例
    analyzer = FlowCodeAnalyzer(
        llm=llmapi.create_llm(llmapi.DEFAULT_CONFIG),
        llm_config=llmapi.DEFAULT_CONFIG
    )
    
    # 分析示例
    result = analyzer.analyze_flows_with_code(
        "帮我找到页面中所有请求"
    )
    print("\n分析结果:")
    print(result)

if __name__ == '__main__':
    main() 