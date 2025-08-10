import json
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langchain.chains.llm import LLMChain
from langchain_core.output_parsers import JsonOutputParser
from app.llm.llm_loader import llm
from app.llm.prompts.judge_plan_input_prompt import JudgePlagInputPrompt


class ExtInputKeyTool(BaseTool):
    name: str = "ext_input_key_tool"
    description: str = "判断用户是否输入了足够的信息。如果是，则提取出重要信息。如果不是，则提示用户重新输入"

    def _run(self, input_text: str) -> str:

        prompt = ChatPromptTemplate.from_template(JudgePlagInputPrompt.PROMPT)
        parser = JsonOutputParser()
        # Create a chain
        chain = LLMChain(
            llm=llm,
            prompt=prompt,
            output_parser=parser
        )
        response = chain.invoke({
            "user_input": input_text
        })

        return json.dumps(response["text"])
