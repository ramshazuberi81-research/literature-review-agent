GROQ_API_KEY="gsk_40gW1MWy**********************************"
from langchain_core.tools import tool
from ddgs import DDGS


@tool
def search_tool(query: str) -> str:
    """ Useful for answering questions about current events or information not in your training data. Input should be a search query."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))
    if not results:
        return "No results found."
    return "\n".join(f"{r['title']}: {r['body']}" for r in results)