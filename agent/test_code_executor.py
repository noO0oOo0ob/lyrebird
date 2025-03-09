from agent.code_executor import CodeExecutor
from agent import llmapi

def test_simple_code_generation(test_numbers):
    """测试简单的代码生成和执行
    
    Args:
        test_numbers (list): 用于测试的数字列表
    """
    # 创建代码执行器实例
    executor = CodeExecutor(llm=llmapi.create_llm(llmapi.DEFAULT_CONFIG))
    executor.initialize()
    
    # 测试代码生成
    test_prompt = """
    生成一个简单的Python函数，实现以下功能：
    1. 接收一个数字列表作为输入
    2. 返回列表中所有偶数的和
    函数名为 sum_even_numbers
    """
    
    # 生成代码
    generated_code = executor.generate_and_execute(test_prompt)
    print("\n生成的代码:")
    print(generated_code['result'])
    
    # 构造执行代码
    execution_code = generated_code['result'][1:] + f"\n\nresult = sum_even_numbers({test_numbers})\nprint(result)"
    
    # 执行代码
    execution_result = executor.execute_code(execution_code)
    print("\n执行结果:")
    print(execution_result)

if __name__ == '__main__':
    test_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # 默认测试用例
    test_simple_code_generation(test_numbers) 