
import anthropic
from config import ANTHROPIC_API_KEY, USE_OPENAI, MODEL_NAME
from Tools import calculator_tool, get_current_time, web_search
import json

def main():
    # Initializing the Anthropic client
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not found. Please check your config.py or .env file.")
        return
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    print("Tool-Calling Bot Started!")
    print("I can help you with:")
    print("• Mathematical calculations")
    print("• Current time in different timezones")
    print("• Web searches")
    print("\nType 'quit' to exit\n")
    
    
    messages = []
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
                
            if not user_input:
                continue
            
            # Adding memory
            messages.append({"role": "user", "content": user_input})
            
            # Get response from Claude with tools
            response = get_claude_response(client, messages)
            
            if response:
                print(f"Bot: {response}\n")
                # Add assistant's response to history
                messages.append({"role": "assistant", "content": response})
            else:
                print("Sorry, I encountered an error. Please try again.\n")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.\n")

def get_claude_response(client, messages):
    """
    Get response from Claude, handling tool calls if needed
    """
    try:
        # Define tool schemas
        tools = [
            {
                "name": "calculator_tool",
                "description": "Perform mathematical calculations and evaluate expressions",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', '15% of 847')"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "get_current_time",
                "description": "Get current time in a specified timezone",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Timezone string like 'UTC', 'US/Eastern', 'Asia/Tokyo', 'Europe/London'"
                        }
                    },
                    "required": ["timezone"]
                }
            },
            {
                "name": "web_search",
                "description": "Search the web for information and return relevant results",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search terms or question to search for"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (1-5, default is 3)"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        
        # Making initial request for tools
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1000,
            messages=messages,
            tools=tools
        )
        
        # Checking if Claude wants to use tools
        if response.stop_reason == "tool_use":
            return handle_tool_calls(client, messages, response, tools)
        else:
            
            return response.content[0].text
            
    except Exception as e:
        print(f"Error communicating with Claude: {e}")
        return None

def handle_tool_calls(client, messages, response, tools):
    """
    Handle tool calls from Claude
    """
    try:
        
        messages.append({
            "role": "assistant", 
            "content": response.content
        })
        
        # for Processing each tool call
        tool_results = []
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input
                tool_use_id = content_block.id
                
                print(f"Using tool: {tool_name}")
                
                # Logic to Call the right tool
                if tool_name == "calculator_tool":
                    result = calculator_tool(tool_input["expression"])
                elif tool_name == "get_current_time":
                    timezone = tool_input.get("timezone", "UTC")
                    result = get_current_time(timezone)
                elif tool_name == "web_search":
                    query = tool_input["query"]
                    num_results = tool_input.get("num_results", 3)
                    print(f"Searching for: '{query}'")
                    result = web_search(query, num_results)
                    print(f"Search completed. Result length: {len(result)} characters")
                else:
                    result = f"Error: Unknown tool '{tool_name}'"
                
                # Add tool result
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result
                })
        
        # Add the tool results to conversation
        messages.append({
            "role": "user",
            "content": tool_results
        })

        
        # Get  response from Claude
        final_response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1500,
            messages=messages,
            tools=tools
        )
        
        # Handle tool calls
        if final_response.stop_reason == "tool_use":
            print("Claude wants to use additional tools...")
            return handle_tool_calls(client, messages, final_response, tools)
        else:
            # Return the final response
            if final_response.content and len(final_response.content) > 0:
                return final_response.content[0].text
            else:
                return "I received the search results but couldn't generate a proper response."
        
    except Exception as e:
        print(f"Error handling tool calls: {e}")
        return "Sorry, I encountered an error while processing the tool results."

def test_tools_individually():
    """
    Test each tool individually to verify they work
    """
    print("Testing tools individually...\n")
    
    # To test calculator
    print("Testing Calculator")
    calc_result = calculator_tool("2 + 3 * 4")
    print(f"Calculator result: {calc_result}")
    
    # Test test Time
    print("\nTesting Time")
    time_result = get_current_time("UTC")
    print(f"Time result: {time_result}")
    
    # Test test Search
    print("\nTesting Search")
    search_result = web_search("Python programming", 2)
    print(f"Search result: {search_result[:200]}...")
    
    print("\nTool testing complete!")

if __name__ == "__main__":
    
    # Run the main chat bot
    main()