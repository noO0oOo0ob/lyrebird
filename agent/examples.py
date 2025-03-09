from typing import List, Dict, Any
from agent import llmapi
from agent.flow import FlowTools
import json
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

class FlowAnalyzer:
    """使用 LLM 分析 Lyrebird 流量的示例类"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        """初始化分析器
        
        Args:
            llm_config: LLM 配置，如果为 None 则使用默认配置
        """
        if llm_config is None:
            llm_config = llmapi.DEFAULT_CONFIG
        self.llm = llmapi.create_llm(llm_config)
        self.flow_tools = FlowTools()
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=llm_config['api_key'],
            openai_api_base=llm_config['api_base']
        )
        self.vector_store = None
        self._cache = {}
        self._flow_cache = {}
    
    def _extract_flow_data(self, request_data: Dict[str, Any], response_data: Dict[str, Any], query: str) -> str:
        """根据查询内容提取相关的流量数据
        
        Args:
            request_data: 请求数据
            response_data: 响应数据
            query: 用户查询内容
            
        Returns:
            提取的流量数据文本
        """
        # 默认只包含基本 URL 信息
        content = [
            f"Method: {request_data.get('method', 'N/A')}",
            f"Path: {request_data.get('path', 'N/A')}"
        ]
        
        # 根据查询内容动态添加其他字段
        query = query.lower()
        
        # 检查是否需要请求参数信息
        if any(word in query for word in ['参数', 'params', 'parameters', 'query']):
            params = request_data.get('query', {})
            content.append(f"Params: {self._truncate_json(params)}")
        
        # 检查是否需要请求头信息
        if any(word in query for word in ['header', 'headers', '请求头']):
            headers = request_data.get('headers', {})
            content.append(f"Headers: {self._truncate_json(headers)}")
        
        # 检查是否需要请求体信息
        if any(word in query for word in ['body', 'data', '请求体', '数据']):
            body = request_data.get('data', {})
            content.append(f"Body: {self._truncate_json(body)}")
        
        # 检查是否需要响应状态信息
        if any(word in query for word in ['status', 'code', '状态', '响应']):
            content.append(f"Status: {response_data.get('code', 'N/A')}")
        
        # 检查是否需要响应体信息
        if any(word in query for word in ['response', 'result', '响应体', '结果']):
            response_body = response_data.get('data', {})
            content.append(f"Response: {self._truncate_json(response_body)}")
        
        return '\n'.join(content)
    
    def _truncate_json(self, data: Any, max_length: int = 200) -> str:
        """截断 JSON 数据
        
        Args:
            data: 要截断的数据
            max_length: 最大长度
            
        Returns:
            截断后的 JSON 字符串
        """
        if not data:
            return '{}'
        json_str = json.dumps(data, ensure_ascii=False)
        if len(json_str) > max_length:
            return json_str[:max_length] + '...'
        return json_str
    
    def _create_vector_store(self, flows: List[Dict[str, Any]], query: str):
        """创建向量存储
        
        Args:
            flows: 流量数据列表
            query: 用户查询内容
        """
        documents = []
        for flow in flows:
            flow_id = flow.get('id')
            if flow_id:
                detail = self.flow_tools.get_flow_detail(flow_id)
                request_data = detail['data']['request']
                response_data = detail['data']['response']
                
                content = self._extract_flow_data(request_data, response_data, query)
                doc = Document(page_content=content, metadata={'flow_id': flow_id})
                documents.append(doc)
        
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
    
    def analyze_recent_flows(self, limit: int = 5, query: str = None) -> str:
        """分析最近的流量数据
        
        Args:
            limit: 分析最近的流量数量
            query: 用户查询内容，用于确定需要分析的数据范围
            
        Returns:
            LLM 生成的分析报告
        """
        if query is None:
            query = "分析 HTTP 流量的基本信息"
            
        # 检查缓存
        cache_key = f"recent_flows_{limit}_{hash(query)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 获取流量列表
        flows = self.flow_tools.get_flow_list()
        recent_flows = flows[:limit]
        
        # 检查流量数据是否有变化
        flow_ids = [flow.get('id') for flow in recent_flows]
        flow_cache_key = '_'.join(flow_ids + [str(hash(query))])
        if flow_cache_key in self._flow_cache:
            self.vector_store = self._flow_cache[flow_cache_key]
        else:
            self._create_vector_store(recent_flows, query)
            self._flow_cache[flow_cache_key] = self.vector_store
        
        # 使用向量检索获取相关文档
        relevant_docs = self.vector_store.similarity_search(query, k=3)
        
        # 构建提示
        prompt = f"基于以下流量数据，{query}：\n\n"
        for doc in relevant_docs:
            prompt += f"{doc.page_content}\n---\n"
        
        # 生成报告并缓存结果
        report = self.llm.generate(prompt)
        self._cache[cache_key] = report
        return report


def main():
    """使用示例"""
    # 创建分析器实例
    analyzer = FlowAnalyzer()
    
    # 分析最近的 3 个请求
    report = analyzer.analyze_recent_flows(20)
    print("\n流量分析报告:")
    print(report)

if __name__ == '__main__':
    main()