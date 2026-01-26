import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Dict, Any, Optional

from langchain_core.tools import StructuredTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.tools.rag_tool import rag_tool
from app.tools.sql_analytics_tool import sql_analytics_tool
from app.tools.balance_query_tool import balance_tool
from app.utils.category_normalizer import validate_category


env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv()


# Load orchestration prompts
with open('app/llm/prompts/orchestration.json', 'r') as f:
    orchestration_prompts = json.load(f)
    RAG_PROMPT = orchestration_prompts['rag_prompt']
    SPENDING_PROMPT = orchestration_prompts['spending_prompt']
    BALANCE_PROMPT = orchestration_prompts['balance_prompt']


class AgentState(TypedDict):
    """State for the agent"""
    messages: Annotated[List, lambda x, y: x + y] # Accumulates messages
    user_id: int
    query: str
    tool_results: Dict[str, Any]    # Store results from tool calls



class Orchestrator:
    """
    Main orchestrator that:
    1. Receives user query
    2. Uses LLM to determine the intent
    3. Selects appropriate tool(s) based on the intent
    4. Calls tool with extracted parameters
    5. Formats response
    """

    def __init__(self, model: str = None):

        if model is None:
            self.model = 'gemini-2.5-flash-lite'
        else:
            self.model = model

        self.llm = ChatGoogleGenerativeAI(
            model = self.model,
            temperature = 0.25,
            streaming = True,
            api_key = os.getenv('GOOGLE_API_KEY'),
        )

        # self.tools = {
        #     "rag": rag_tool,
        #     "sql_analytics": sql_analytics_tool(),
        #     "balance_query": balance_query_tool(),
        # }

        self.tools = self._create_langchain_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.memory = MemorySaver()
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer = self.memory)

    def _create_langchain_tools(self) -> List[StructuredTool]:
        """Wrap current tools in LangChain StructuredTool format"""

        async def rag_search(query: str) -> str:
            context = await rag_tool.get_policy_context(query)
            return context
        
        async def analyze_spending(
            user_id: int,
            category: Optional[str] = None,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            group_by: str = "category",
            account_id: Optional[int] = None,
            account_type: Optional[str] = None
        ) -> str:

            # Normalize category before calling the tool
            normalized_category = None
            if category:
                _, normalized_category = validate_category(category)


            start_dt = None
            end_dt = None
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass

            result = await sql_analytics_tool.analyze_spending(
                user_id = user_id,
                category = normalized_category,
                start_date = start_dt,
                end_date = end_dt,
                group_by = group_by,
                account_id = account_id,
                account_type = account_type
            )
            
            summary = result.get('summary', {})
            results = result.get('results', [])

            response = f"Spending Analysis:\n"
            response += f"Total Spending: ${summary.get('total_spending', 0):.2f}\n"
            response += f"Total Transactions: {summary.get('total_transactions', 0)}\n\n"

            if results:
                response += "Breakdown:\n"
                for item in results[:10]:  # Limit to top 10
                    if group_by == "category":
                        response += f"  {item.get('group_value', 'N/A')}: ${item.get('total_spending', 0):.2f}\n"
                    elif group_by == "month":
                        month = item.get('month', 'N/A')
                        response += f"  {month}: ${item.get('total_spending', 0):.2f}\n"
                    else:
                        response += f"  {item}: ${item.get('total_spending', 0):.2f}\n"
            
            return response

        async def get_balance(
            user_id: int,
            account_id: Optional[int] = None,
            account_type: Optional[str] = None
        ) -> str:

            result = await balance_tool.get_balance(
                user_id = user_id,
                account_id = account_id,
                account_type = account_type
            )

            accounts = result.get('results', [])
            if not accounts:
                return "No accounts found."

            response = "Account Balances:\n"

            total = 0
            for account in accounts:
                acc_type = account.get('type', 'N/A')
                acc_id = account.get('account_id', 'N/A')
                balance = account.get('balance', 0)
                total += balance
                response += f"  {acc_type.capitalize()} Account #{acc_id}: ${balance:,.2f}\n"

            response += f"\nTotal Balance: ${total:,.2f}\n"

            return response
        
        # Force LLM to yield structured JSON responses
        return [
            StructuredTool.from_function(
                func = rag_search,
                name = "search_policy_documents",
                description = RAG_PROMPT
            ),
            StructuredTool.from_function(
                func = analyze_spending,
                name = "analyze_spending",
                description = SPENDING_PROMPT
            ),
            StructuredTool.from_function(
                func = get_balance,
                name = "get_account_balances",
                description = BALANCE_PROMPT
            )
        ]

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine"""

        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("router", self._route_query)
        graph.add_node("tools", self._execute_tools)
        graph.add_node("respond", self._format_response)

        # Add edges
        graph.add_edge(START, "router")

        # Conditional edge: after routing, check if tools need to be called
        graph.add_conditional_edges(
            "router",
            self._should_call_tools,
            {
                "tools": "tools",
                "respond": "respond"
            }
        )
        
        # After tools execute, alwaus format response
        graph.add_edge("tools", "respond")
        graph.add_edge("respond", END)

        return graph

    
    async def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute tools asynchronously"""

        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        if not last_message or not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return {"messages": []}

        # Store tool metadate for frontend display
        tool_metadata = []

        # Helper function to execute a single tool call
        async def execute_single_tool(tool_call):
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_call_id = tool_call.get("id")
            
            # Tools that require user_id
            tools_requiring_user_id = ['analyze_spending', 'get_account_balances']
            
            # Inject user_id from state if tool needs it and it's not in args
            if tool_name in tools_requiring_user_id and 'user_id' not in tool_args:
                state_user_id = state.get('user_id')
                if state_user_id:
                    tool_args['user_id'] = state_user_id
            
            # Remove user_id from tools that don't need it (like RAG tool)
            if tool_name not in tools_requiring_user_id and 'user_id' in tool_args:
                tool_args.pop('user_id', None)

            # Find the tool
            tool = None
            for t in self.tools:
                if t.name == tool_name:
                    tool = t
                    break
            
            if not tool:
                return ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found.",
                    tool_call_id=tool_call_id
                )

            try:
                # Capture metadata based on tool type
                metadata = {"tool_name": tool_name, "tool_args": tool_args}

                if tool_name == "analyze_spending":
                    # NOTE: Need to modify spending_service.py to return actual SQL query
                    # For now, just capture the parameters
                    metadata["sql_params"] = tool_args

                if tool_name == "search_policy_documents":
                    from app.tools.rag_tool import rag_tool
                    rag_results = await rag_tool.search_policy_documents(tool_args.get("query", ""))
                    metadata["rag_results"] = rag_results.get("results", [])[:3]    # Top 3

                if tool_name == "get_account_balances":
                    from app.tools.balance_tool import balance_tool
                    balance_results = await balance_tool.get_account_balances(tool_args.get("user_id", None))
                    metadata["balance_results"] = balance_results


                # Call the underlying async function directly
                # StructuredTool wraps async functions, so we need to await the function itself
                if asyncio.iscoroutinefunction(tool.func):
                    result = await tool.func(**tool_args)
                else:
                    # For sync functions, use invoke
                    result = tool.invoke(tool_args)

                # Store metadata
                tool_metadata.append(metadata)
                
                return ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id
                )
            except Exception as e:
                # Log the full error for debugging
                import traceback
                error_trace = traceback.format_exc()
                print(f"ERROR in {tool_name}: {str(e)}")
                print(f"Tool args: {tool_args}")
                print(f"Traceback: {error_trace}")
                
                return ToolMessage(
                    content=f"Error executing {tool_name}: {str(e)}",
                    tool_call_id=tool_call_id
                )

        # Execute all tool calls in parallel
        tool_messages = await asyncio.gather(*[
            execute_single_tool(tool_call)
            for tool_call in last_message.tool_calls
        ])
        
        # Store metadata in state for later retrieval
        state["tool_metadata"] = tool_metadata

        return {"messages": list(tool_messages), "tool_metadata": tool_metadata}
                


    async def _route_query(self, state: AgentState) -> AgentState:
        """Route the query using LLM to determine which tools to call"""

        messages = state.get("messages", [])
        user_id = state.get("user_id")

        # Check if we need to add system message (only if it's not already there)
        has_system_message = any(isinstance(msg, SystemMessage) for msg in messages)
        
        if not messages:
            # Build messages with system context about user_id
            system_messages = []
            if user_id:
                # Add system message to inform LLM about available user_id
                system_messages.append(
                    SystemMessage(content=f"The user's ID is {user_id}. Use this user_id when calling tools that require it (like get_account_balances or analyze_spending).")
                )
            
            # Add the user's query
            messages = system_messages + [HumanMessage(content=state["query"])]
        elif not has_system_message and user_id:
            # Prepend system message if it doesn't exist and we have user_id
            system_msg = SystemMessage(content=f"The user's ID is {user_id}. Use this user_id when calling tools that require it (like get_account_balances or analyze_spending).")
            messages = [system_msg] + messages
        
        # Get LLM response with potential tool calls
        response = await self.llm_with_tools.ainvoke(messages)

        return {
            "messages": [response],
            "tool_results": {}
        }

    
    def _should_call_tools(self, state: AgentState) -> str:
        """Determine if tools need to be called"""
        messages = state.get("messages", [])
        if not messages:
            return "respond"
        
        last_message = messages[-1]
        
        # Check if the last message has tool calls
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        return "respond"

    async def _format_response(self, state: AgentState) -> AgentState:
        """Format the final response after tool execution"""

        messages = state.get("messages", [])

        # Get the last AI message
        tool_calls = []
        for msg in reversed(messages):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tool_calls = msg.tool_calls
                break

        # If there were tool calls, fetch the results and ask LLM to format response
        if tool_calls:
            tool_results = []
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    tool_results.append(msg)
            
            response_messages = messages + tool_results

            final_response = await self.llm.ainvoke(response_messages)

            return {
                "messages": [final_response],
            }

    
    async def process_query(
        self,
        query: str,
        user_id: int,
        thread_id: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """Process a user query with streaming response"""

        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content = query)],
            "user_id": user_id,
            "query": query,
            "tool_results": {}
        }

        # Configure for streaming response
        if config is None:
            config = {
                "configurable": {
                    "thread_id": thread_id or f"user_{user_id}_{datetime.now().timestamp()}"
                }
            }

        # Stream the graph execution
        async for event in self.app.astream(initial_state, config = config):
            # Yield events as they happen
            for node_name, node_output in event.items():
                # Check if node_output is None -> Avoid attribute errors later
                if node_output is None:
                    continue

                if node_name == "router":
                    # LLM thinking/routing
                    messages = node_output.get("messages", [])

                    if messages:
                        last_msg = messages[-1]

                        if hasattr(last_msg, 'content') and last_msg.content:
                            yield {
                                "type": "thinking",
                                "content": last_msg.content
                            }
                        
                        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                            yield {
                                "type": "tool_call",
                                "tools": [tc.get("name") for tc in last_msg.tool_calls]
                            }
                
                elif node_name == "tools":
                    # Tools are executing - include metadata
                    tool_metadata = node_output.get("tool_metadata", [])
                    
                    yield {
                        "type": "tool_execution",
                        "status": "executing"
                        "metadata": tool_metadata  # Include SQL queries, RAG results etc.
                    }

                elif node_name == "respond":
                    # Final response
                    messages = node_output.get("messages", [])
                    if messages:
                        last_msg = messages[-1]
                        if hasattr(last_msg, 'content'):
                            # Stream content chunk by chunk
                            content = last_msg.content
                            if content:
                                chunk_size = 50
                                for i in range(0, len(content), chunk_size):
                                    chunk = content[i:i+chunk_size]
                                    yield {
                                        "type": "response",
                                        "content": chunk
                                    }


# create singleton instance
orchestrator = Orchestrator(model = 'gemini-2.5-flash-lite')


if __name__ == "__main__":
    async def main():
        # Test with user_id 6 as mentioned in query
        query = "What is the monthly maintenance fee? Also, how much did I spend on coffee on November 2025?"
        user_id = 6  # Match the user_id from the query
        async for event in orchestrator.process_query(query, user_id):
            print(event)
    
    asyncio.run(main())