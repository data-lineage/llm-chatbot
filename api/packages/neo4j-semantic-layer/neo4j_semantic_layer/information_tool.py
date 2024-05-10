from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

# Import things that are needed generically
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

from neo4j_semantic_layer.utils import get_candidates, graph

description_query = """
MATCH (m:Manager)-[r:OWNS_STOCK_IN]->(t)
WHERE m.managerCik =  $candidate OR m.managerName =  $candidate
WITH m, r, t
WITH "Manager Name: " + coalesce(m.managerName, "") + "\nManager Address: " + coalesce(m.managerAddress, "") + "\nStocks: " + coalesce(r.desc, "") AS context
RETURN context LIMIT 1
"""

# # Case insensitive
# description_query = """
# MATCH (m:Manager)
# WHERE m.managerCik = $candidate OR m.managerName = $candidate
# MATCH (m)-[r:OWNS_STOCK_IN]-(t)
# WITH m, type(r) as type, collect(coalesce(t.companyName, t.cusipId)) as names
# WITH m, type+": "+reduce(s="", n IN names | s + n + ", ") as types
# WITH m, collect(types) as contexts
# WITH m, "type:" + labels(m)[0] + "\nManager Name: "+ coalesce(m.managerName)+"\nManager Address"+ coalesce(m.managerAddress) as context
# RETURN context LIMIT 1
# """

#  manager address
# description_query = """
# MATCH (m:Manager)
# WHERE toLower(m.managerCik) = toLower($candidate) OR toLower(m.managerName) = toLower($candidate)
# MATCH (m)-[r:OWNS_STOCK_IN]-(t)
# WITH m, type(r) as type, collect(coalesce(t.companyName, t.cusipId)) as names
# WITH m, type+": "+reduce(s="", n IN names | s + n + ", ") as types
# WITH m, collect(types) as contexts
# WITH m, "type:" + labels(m)[0] + "\nManager Name: "+ coalesce(m.managerName) + "\nManager Address: " + coalesce(m.managerAddress) as context
# RETURN context LIMIT 1
# """

# # Owns stock relationship
# description_query = """
# MATCH (m:Manager)
# WHERE m.managerCik = $candidate OR m.managerName = $candidate
# MATCH (m)-[r:OWNS_STOCK_IN]-(t)
# WITH m, type(r) as type, collect(coalesce(t.companyName, t.cusipId)) as stocks
# WITH m, type+": "+reduce(s="", n IN stocks | s + n + ", ") as types
# WITH m, collect(types) as contexts
# WITH m, "type:" + labels(m)[0] + "\nManager Name: "+ coalesce(m.managerName)+"\nManager Address"+ coalesce(m.managerAddress) + "\nStocks: " + types as context
# RETURN context LIMIT 1
# """

# Filed form relationships
# description_query1 = """
# MATCH (c:Company)
# WHERE c.companyName = $candidate OR c.cusipId = $candidate
# MATCH (c)-[r:FILED]-(t)
# WITH c, type(r) as type, collect(coalesce(t.names, t.source)) as names
# WITH c, type+": "+reduce(s="", n IN names | s + n + ", ") as types
# WITH c, collect(types) as contexts
# RETURN "Type: " + labels(c)[0] + "\nCompany Name: " + coalesce(c.companyName, "") + "\nForm Source: " + contexts[0] LIMIT 1
# """

def get_information(entity: str, type: str) -> str:
    candidates = get_candidates(entity, type)
    if not candidates:
        return "No information was found about the movie or person in the database"
    elif len(candidates) > 1:
        newline = "\n"
        return (
            "Need additional information, which of these "
            f"did you mean: {newline + newline.join(str(d) for d in candidates)}"
        )
    data = graph.query(
        # description_query1,
        description_query, params={"candidate": candidates[0]["candidate"]}
    )
    return data[0]["context"]


class InformationInput(BaseModel):
    entity: str = Field(description="movie or a person mentioned in the question")
    entity_type: str = Field(
        description="type of the entity. Available options are 'movie' or 'person'"
    )


class InformationTool(BaseTool):
    name = "Information"
    description = (
        "useful for when you need to answer questions about various actors or movies"
    )
    args_schema: Type[BaseModel] = InformationInput

    def _run(
        self,
        entity: str,
        entity_type: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        return get_information(entity, entity_type)

    async def _arun(
        self,
        entity: str,
        entity_type: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        return get_information(entity, entity_type)

# Provide me the Address of manager Royal from the database where entity type is Manager

# What is the investment done by the Manager Quantitative Investment Management, LLC in a company NETAPP INC. where entity type Manager from database