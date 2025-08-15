import json

from typing import Annotated, Any, List
from datetime import datetime, timedelta

from autogen import ConversableAgent
from autogen.agentchat.group import (ContextVariables, 
                                     AgentNameTarget, 
                                     RevertToUserTarget,
                                     ReplyResult)

# Define tool functions

def classify_query(
    query: Annotated[str, "The user query to classify"],
    context_variables: ContextVariables
) -> ReplyResult:
    """Classify a user query and route to the appropriate agent."""
    # Update query count
    context_variables["query_count"] += 1

    # Simple classification logic
    toolList:List[str] = []
    agent_tools:dict = context_variables["agent_tool_list"]
    for agentName in agent_tools.keys():
        anAgent = agent_tools.get(agentName)
        for tool in anAgent.toolkit.tools:
            toolList.append(tool.name)
            if any(keyword in query.lower() for keyword in toolList):
                return ReplyResult(
                    message=f"This appears to be a {agentName} Tool",
                    target=AgentNameTarget(agentName),
                    context_variables=context_variables
                )
            else:
                return ReplyResult(
                    message="This doesn't seem to be a valid tool.",
                    target=RevertToUserTarget(),
                    context_variables=context_variables
        )

def check_repeat_issue(
    description: Annotated[str, "User's description of the continuing issue"],
    context_variables: ContextVariables
) -> ReplyResult:
    """Check if this is a repeat of an issue that wasn't resolved."""
    # Mark this as a repeat issue in the context
    context_variables["repeat_issue"] = True
    context_variables["continuing_issue"] = description

    return ReplyResult(
        message="I understand that your issue wasn't resolved. Let me connect you with our advanced troubleshooting specialist.",
        target=AgentNameTarget("advanced_troubleshooting_agent"),
        context_variables=context_variables
    )

# Define tools that use context variables
def classify_and_log_query(
    query: Annotated[str, "The user query to classify"],
    context_variables: ContextVariables
) -> ReplyResult:
    """Classify a user query as technical or general and log it in the context."""

    # Printing the context variables
    print(f"{context_variables.to_dict()=}")

    # Record this query in history
    query_history = context_variables.get("query_history", [])
    query_record = {
        "timestamp": datetime.now().isoformat(),
        "query": query
    }
    query_history.append(query_record)
    context_variables["query_history"] = query_history
    context_variables["last_query"] = query
    context_variables["query_count"] = len(query_history)

    # Basic classification logic
    technical_keywords = ["error", "bug", "broken", "crash", "not working", "shutting down"]
    is_technical = any(keyword in query.lower() for keyword in technical_keywords)

    # Update context with classification
    if is_technical:
        target_agent = AgentNameTarget("tech_agent")
        context_variables["query_type"] = "technical"
        message = "This appears to be a technical issue. Routing to technical support..."
    else:
        target_agent = AgentNameTarget("general_agent")
        context_variables["query_type"] = "general"
        message = "This appears to be a general question. Routing to general support..."

    # Printing the context variables
    print(f"{context_variables.to_dict()=}")

    return ReplyResult(
        message=message,
        target=target_agent,
        context_variables=context_variables
    )

def provide_technical_solution(
    solution: Annotated[str, "Technical solution to provide"],
    context_variables: ContextVariables
) -> ReplyResult:
    """Provide a technical solution and record it in the context."""

    # Printing the context variables
    print(f"{context_variables.to_dict()=}")

    # Record the solution
    last_query = context_variables.get("last_query", "your issue")
    solutions_provided = context_variables.get("solutions_provided", [])

    solution_record = {
        "timestamp": datetime.now().isoformat(),
        "query": last_query,
        "solution": solution
    }
    solutions_provided.append(solution_record)

    # Update context
    context_variables["solutions_provided"] = solutions_provided
    context_variables["last_solution"] = solution
    context_variables["solution_count"] = len(solutions_provided)

    # Printing the context variables
    print(f"{context_variables.to_dict()=}")

    return ReplyResult(
        message=solution,
        context_variables=context_variables
    )

def get_user_context(context_variables: ContextVariables) -> str:
    """Get information about the current user and session."""
    user_name = context_variables.get("user_name", "User")
    query_count = context_variables.get("query_count", 0)
    session_start = context_variables.get("session_start", "Unknown")

    return f"""Current session information:
    - Session started: {session_start}
    - Total queries: {query_count}
    - Last query: {context_variables.get("last_query", "None")}
    - Query type: {context_variables.get("query_type", "Unknown")}"""



# Mock database of previous transactions
def get_previous_transactions() -> list[dict[str, Any]]:
    today = datetime.now()
    return [
        {
            "vendor": "Staples",
            "amount": 500,
            "date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),  # 3 days ago
            "memo": "Quarterly supplies",
        },
        {
            "vendor": "Acme Corp",
            "amount": 1500,
            "date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),  # 10 days ago
            "memo": "NDA services",
        },
        {
            "vendor": "Globex",
            "amount": 12000,
            "date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),  # 5 days ago
            "memo": "Confidential",
        },
    ]

def check_duplicate_payment(
    vendor: Annotated[str, "The vendor name"],
    amount: Annotated[float, "The transaction amount"],
    memo: Annotated[str, "The transaction memo"]
) -> dict[str, Any]:
    """Check if a transaction appears to be a duplicate of a recent payment"""
    previous_transactions = get_previous_transactions()

    today = datetime.now()

    for tx in previous_transactions:
        tx_date = datetime.strptime(tx["date"], "%Y-%m-%d")
        date_diff = (today - tx_date).days

        # If vendor, memo and amount match, and transaction is within 7 days
        if (
            tx["vendor"] == vendor and
            tx["memo"] == memo and
            tx["amount"] == amount and
            date_diff <= 7
        ):
            return {
                "is_duplicate": True,
                "reason": f"Duplicate payment to {vendor} for ${amount} on {tx['date']}"
            }

    return {
        "is_duplicate": False,
        "reason": "No recent duplicates found"
    }

def is_termination_msg(x: dict[str, Any]) -> bool:
    content = x.get("content", "")
    try:
        # Try to parse the content as JSON (structured output)
        data = json.loads(content)
        return isinstance(data, dict) and "summary_generated_time" in data
    except:
        # If not JSON, check for text marker (fallback)
        return (content is not None) and "==== SUMMARY GENERATED ====" in content