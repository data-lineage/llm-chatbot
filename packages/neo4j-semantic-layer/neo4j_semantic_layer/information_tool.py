from typing import Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

# Import things that are needed generically
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

from neo4j_semantic_layer.utils import get_candidates, graph
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Owns stock relationship Used for Querying single Manager Node
description_query1 = """
MATCH (m:Manager)-[r:OWNS_STOCK_IN]->(t)
WHERE m.managerCik =  $candidate OR m.managerName =  $candidate
WITH m, r, t
WITH "Manager Name: " + coalesce(m.managerName, "") + "\nManager Address: " + coalesce(m.managerAddress, "") + "\nStocks: " + coalesce(r.desc, "") AS context
RETURN context LIMIT 25
"""

# Used for querying to fetch list of Managers present in a Company
description_query2 = """
MATCH (c:Company) - [r:OWNS_STOCK_IN] -(m:Manager)
WHERE c.companyName = $candidate
WITH c,r,m
WITH "Manager Name: " + coalesce(m.managerName, "") AS context
RETURN context LIMIT 25
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
    
    description_query = None
    if type.lower() == "manager":
        description_query = description_query1
    elif type.lower() == "company":
        description_query = description_query2
    else:
            return "Invalid entity type. Please provide either 'Manager' or 'Company'."

    try:
        # data = graph.query(
        #     description_query, params={"candidate": candidates[0]["candidate"]}
        # )
        # if not data:
        #     return "No detailed information was found for the specified Manager or Company"
        # return data[0]["context"]
        data = []
        for candidate in candidates:
            query_result = graph.query(description_query, params={"candidate": candidate["candidate"]})
            data.extend(query_result)
        if not data:
            return "No information found for the provided candidates."
    # Assuming context is a string field in the query results
        return "\n".join(result["context"] for result in data)
    except Exception as e:
        logger.error(f"Error querying the database: {e}")
        return "An error occurred while fetching the information."


class InformationInput(BaseModel):
    entity: str = Field(description="Manager or a Company mentioned in the question")
    entity_type: str = Field(
        description="type of the entity. Available options are 'Manager' or 'Company'"
    )


class InformationTool(BaseTool):
    name = "Information"
    description = (
        "useful for when you need to answer questions about various Manager or Company"
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