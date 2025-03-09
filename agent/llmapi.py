from typing import List, Dict, Any, Optional, Sequence
from openai import OpenAI
from abc import ABC, abstractmethod
from langchain.llms.base import BaseLLM
from langchain_core.outputs import Generation, LLMResult


class LyrebirdLLM(BaseLLM):
    """Lyrebird LLM base class that implements the BaseLLM interface"""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from the LLM"""
        pass


class OpenAIAdapter(BaseLLM):
    def __init__(self, api_key: str, api_base: str, model: str = "gpt-4o"):
        super().__init__()
        self._client = OpenAI(api_key=api_key, base_url=api_base)
        self._model = model

    @property
    def _llm_type(self) -> str:
        return "openai"

    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> LLMResult:
        if not prompts:
            return LLMResult(generations=[[]])
        
        generations = []
        for prompt in prompts:
            try:
                completion = self._client.chat.completions.create(
                    model=self._model,
                    stream=False,
                    messages=[{"role": "user", "content": prompt}],
                    stop=stop
                )
                text = completion.choices[0].message.content
                gen = Generation(text=text)
                generations.append([gen])
            except Exception as e:
                gen = Generation(text=f"Error: {str(e)}")
                generations.append([gen])
        
        return LLMResult(generations=generations)

    def generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> LLMResult:
        """Generate text from the LLM"""
        return self._generate(prompts, stop=stop, **kwargs)

# 默认配置
DEFAULT_CONFIG = {
    "api_key": "sk-bjbY291LrdCy7NlpFdF6s9CUU5pH2SgCj9b5TrRAe8POViut",
    "api_base": "https://sg.uiuiapi.com/v1",
    # "model": "gpt-4o-mini"
    "model": "claude-3-5-sonnet"
    # "model": "gpt-4o"
}

def create_llm(config: Optional[Dict[str, Any]] = None) -> BaseLLM:
    """
    创建 LLM 实例的工厂函数
    """
    if config is None:
        config = DEFAULT_CONFIG
    return OpenAIAdapter(
        api_key=config.get("api_key", DEFAULT_CONFIG["api_key"]),
        api_base=config.get("api_base", DEFAULT_CONFIG["api_base"]),
        model=config.get("model", DEFAULT_CONFIG["model"])
    )

if __name__ == "__main__":
    llm = create_llm()
    response = llm.generate("""
Return only the Python code (without any explanations) for a bubble sort implementation that:
- Uses a function named 'bubble_sort'
- Takes a list as input
- Sorts in ascending order
- Includes basic comments
- Shows a usage example
- Only give me python code, no other text, that is most important
    """)
    print(response)