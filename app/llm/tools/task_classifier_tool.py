from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from app.llm.llm_loader import llm
from app.llm.prompts.task_classifler_prompt import TaskClassiflerPrompt


class TaskClassiflerTool(BaseTool):
    name: str = "task_classifier_tool"
    description: str = "根据用户输入判断是否需要生成学习计划或回答问题"

    def _run(self, topic: str) -> str:
        """根据用户输入判断是否需要生成学习计划或回答问题。"""
        prompt = PromptTemplate(
            input_variables=["question"],
            template=TaskClassiflerPrompt.PROMPT
        )
        qa_chain = LLMChain(llm=llm, prompt=prompt)
        result = qa_chain.invoke({"question": topic})
        return result["text"]  # 返回结果并去掉多余的空格
