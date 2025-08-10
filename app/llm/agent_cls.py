from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
import re

llm = ChatOpenAI(api_key="sk-e6b73aa5c03e4f0abae7c0d69ab7d3f5",
                 base_url="https://api.deepseek.com",
                 temperature=0,
                 model="deepseek-chat")

# 查询数据库a
# 定义一个函数，根据传入的主题返回对应的学习计划
def get_study_plan(topic: str) -> str:
    # 如果主题是python,返回对应的学习计划
    if topic == "python":
        return "学习计划：\n1. 学习Python基础语法\n2. 学习Python数据结构\n3. 学习Python函数和模块\n4. 学习Python面向对象编程\n5. 学习Python网络编程\n6. 学习Python数据库编程\n7. 学习Python爬虫编程"
    # 否则返回None
    return None

# 保存学习计划到数据库
def save_study_plan(topic: str, content: str):
    print("save_study_plan")

# 生成学习计划
def generate_study_plan(topic: str) -> str:
    prompt = f"请为主题“{topic}”生成一个为期一周的学习计划，包含每天的目标和建议。"
    return llm.predict(prompt)



def is_study_plan_request(text: str) -> bool:
    keywords = ["学习计划", "制定计划", "学习安排", "课程规划"]
    return any(word in text for word in keywords)


def extract_topic(text: str) -> str:
    # 使用正则表达式搜索文本中符合学习计划格式的字符串
    match = re.search(r'(?:学习|计划|关于)?(.*?)的?学习计划', text)
    # 如果匹配成功，返回匹配到的主题，否则返回通用主题
    return match.group(1).strip() if match else "通用主题"

def handle_request(text: str) -> str:
    if is_study_plan_request(text):
        topic = extract_topic(text)
        existing_plan = get_study_plan(topic)
        if existing_plan:
            return f"这是我们为“{topic}”找到的现有学习计划：\n\n{existing_plan}"
        else:
            new_plan = generate_study_plan(topic)
            save_study_plan(topic, new_plan)
            return f"为“{topic}”生成的新学习计划如下：\n\n{new_plan}"
    else:
        return llm.predict(text)

class RetrievePlan(BaseTool):
    name: str = "retrieve_plan"
    description: str = "查询某个学习主题的计划（如果存在）"
    
    def _run(self, topic: str) -> str:
        """根据用户输入判断是否需要生成学习计划或回答问题。"""
        qa_prompt = PromptTemplate(
            input_variables=["question"],
            template="""你是一个智能助手，擅长分析用户的提问目的。现在请根据用户的输入判断其意图属于以下两类之一：
                    1. 学习意图（Learning Intent）：用户希望系统地学习某个技能或知识，希望获取教程、学习路径、练习方法等。
                    2. 问题疑问（Questioning Intent）：用户对某个概念、现象或问题感到疑惑，期望你解释或解答。
                    请你只输出：
                    - “学习意图”
                    - 或
                    - “问题疑问”
                    用户输入：{question}
                    你的判断：
                """
        )
        qa_chain = LLMChain(llm=llm, prompt=qa_prompt)
        result = qa_chain.invoke({"question": input_text})
        return result["text"]  # 返回结果并去掉多余的空格

class GeneratePlan(BaseTool):
    name: str = "generate_plan"
    description: str = "生成某个学习主题的计划（如果不存在）"

    def _run(self, topic: str) -> str:
        """生成一个学习主题的学习计划（为期一周），并保存到数据库"""
        prompt = f"请为主题“{topic}”生成一个为期一周的中文学习计划，包含每天学习的内容和建议。"
        plan = llm.predict(prompt)
        save_study_plan(topic, plan)
        return plan

class AnswerQuestion(BaseTool):
    name: str = "answer_question"
    description: str = "回答用户的问题"
    def _run(self, question: str) -> str:
        """处理一般性问题，如知识问答或建议"""
        # 使用llm模型预测问题
        return llm.predict(question)

tools = [RetrievePlan(), GeneratePlan(), AnswerQuestion()]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # 适合用自然语言描述决策
    verbose=True
)

def run_agent(user_input: str):
    return agent.run(user_input)

if __name__ == '__main__':
    run_agent("如何用python将列表中的数字抽取出来")