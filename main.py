from langchain_community.utilities import SQLDatabase
from typing_extensions import TypedDict
from langchain import hub
from typing_extensions import Annotated
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage


healthcare_db = SQLDatabase.from_uri("mysql://root:@127.0.0.1/presco_widget_data")  

llm = ChatOllama(model="llama3.3", num_predict=3000, verbose=True)

query_prompt_template = hub.pull("langchain-ai/sql-query-system-prompt")

class QueryOutput(TypedDict):
    query: Annotated[str, ..., "Syntactically valid SQL query."]

def write_query(question):
    print("question: ", question)
    # prompt = query_prompt_template.invoke(
    #     {
    #         "dialect": healthcare_db.dialect,
    #         "top_k": 1,
    #         "table_info": healthcare_db.get_table_info(),
    #         "input": question,
    #     }
    # )
    # prompt = f"Write syntactically valid SQL query for this question.\n\n qeustion: {question}"
    with open("prompt.txt", "r") as file:
        prompt = file.read()
    # print(llm.invoke([HumanMessage(content=prompt)]))
    structured_llm = llm.with_structured_output(QueryOutput)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print(structured_llm.invoke(prompt))

if __name__ == "__main__":
    question = "how many patients are there?"
    write_query(question)
    


    
    