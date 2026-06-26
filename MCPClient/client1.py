import asyncio
import json

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, ToolMessage

load_dotenv()


SERVERS = {
    "expense": {
        "transport": "stdio",
        "command": r"F:\Projects\AI-Project\MCP-Server\myenv\Scripts\python.exe",
        "args": [
            r"F:\Projects\AI-Project\MCP-Server\LocalMCPServer\main.py"
        ]
    }
}


async def main():

    print("=" * 70)
    print("Expense Tracker MCP Client (Gemini + LangChain + FastMCP)")
    print("=" * 70)

    client = MultiServerMCPClient(SERVERS)

    tools = await client.get_tools()

    tool_map = {
        tool.name: tool
        for tool in tools
    }

    print("\nAvailable Tools:")
    print("-" * 70)

    for tool in tools:
        print(f"• {tool.name}")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )

    llm_with_tools = llm.bind_tools(tools)

    print("\nType your query.")
    print("Type 'exit' to quit.\n")

    while True:

        prompt = input("You : ").strip()

        if prompt.lower() in ["exit", "quit", "q"]:
            print("\nGoodbye!")
            break

        try:

            response = await llm_with_tools.ainvoke(
                [HumanMessage(content=prompt)]
            )

            if not response.tool_calls:

                print("\nGemini:")
                print(response.content)
                print()
                continue

            tool_messages = []

            for call in response.tool_calls:

                tool_name = call["name"]
                tool_args = call["args"]

                print("\n" + "=" * 70)
                print(f"Tool Selected : {tool_name}")
                print("=" * 70)

                print("\nArguments:")
                print(json.dumps(tool_args, indent=4))

                result = await tool_map[tool_name].ainvoke(tool_args)

                print("\nTool Output:")
                print(result)

                tool_messages.append(
                    ToolMessage(
                        tool_call_id=call["id"],
                        content=json.dumps(result)
                    )
                )

            final_response = await llm_with_tools.ainvoke(
                [
                    HumanMessage(content=prompt),
                    response,
                    *tool_messages
                ]
            )

            print("\nGemini:")
            print(final_response.content)
            print()

        except Exception as e:
            print("\nERROR:")
            print(e)
            print()


if __name__ == "__main__":
    asyncio.run(main())