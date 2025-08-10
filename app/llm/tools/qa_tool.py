from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from app.llm.llm_loader import llm


class QATool(BaseTool):
    name: str = "qa_tool"
    description: str = "回答用户输入的问题"

    def _run(self, input_text: str) -> str:
        """回答用户的问题"""
        prompt = PromptTemplate(input_variables=["question"],
                                template="请简洁明了地回答下面的问题：{question}")
        qa_chain = LLMChain(llm=llm, prompt=prompt)
        return qa_chain.invoke({"question": input_text})
