import json
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.output_parsers import StructuredOutputParser
from langchain_core.output_parsers import StrOutputParser
from app.llm.llm_loader import llm
from app.llm.prompts.gen_plan_prompt import GenPlanPrompt


class GeneratePlanTool(BaseTool):
    name: str = "generate_plan_tool"
    description: str = "根据用户输入的内容生成学习计划"

    def _run(self, input_text: str) -> str:
        parser = StructuredOutputParser.from_response_schemas([
            {"name": "plan_content", "description": "计划的内容"},

        ])
        prompt = PromptTemplate(
            template=GenPlanPrompt.SYS_PROMPT,
            input_variables=["subject", "total_days",
                             "difficulty_level", "prior_knowledge", "specific_goals"],
            partial_variables={
                "format_instructions": parser.get_format_instructions()}
        )
        qa_chain = LLMChain(llm=llm,
                            prompt=prompt,
                            output_parser=StrOutputParser()
                            )
        input_data = json.loads(input_text)
        result = qa_chain.invoke({"subject": input_data["subject"],
                                  "total_days": input_data["total_days"],
                                  "difficulty_level": input_data["difficulty_level"],
                                  "prior_knowledge": input_data["prior_knowledge"],
                                  "specific_goals": input_data["specific_goals"],
                                  "total_days": input_data["total_days"]})
        return json.dumps(result["text"], ensure_ascii=False)
