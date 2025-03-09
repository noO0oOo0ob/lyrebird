# Lyrebird Agent

## 环境配置

### 安装依赖
```bash
pip install -r requirements.txt
```

### OpenAI API Key 配置
在运行示例代码之前，请确保设置了 OpenAI API Key。你可以通过以下两种方式之一进行配置：

1. 环境变量（推荐）
```bash
export OPENAI_API_KEY="your-api-key-here"
```

2. 代码中直接配置
```python
from agent.examples import FlowAnalyzer

analyzer = FlowAnalyzer({
    'openai_api_key': 'your-api-key-here'
})
```

## 示例运行
配置完成后，你可以运行示例代码：

```bash
python -m agent.examples
```