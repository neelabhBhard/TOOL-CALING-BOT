# main.py
import anthropic
from config import ANTHROPIC_API_KEY, USE_OPENAI, MODEL_NAME
from Tools import calculator_tool, get_current_time, web_search
import json

def main():
    # Initialize the Anthropic client
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
    
    # Store conversation history
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
            
            # Add user message to history
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
        # Define tool schemas for Claude
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
        
        # Make initial request to Claude with tools
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1000,
            messages=messages,
            tools=tools
        )
        
        # Check if Claude wants to use tools
        if response.stop_reason == "tool_use":
            return handle_tool_calls(client, messages, response, tools)
        else:
            # No tools needed, return regular response
            return response.content[0].text
            
    except Exception as e:
        print(f"Error communicating with Claude: {e}")
        return None

def handle_tool_calls(client, messages, response, tools):
    """
    Handle tool calls from Claude
    """
    try:
        # Add Claude's response (with tool calls) to conversation
        messages.append({
            "role": "assistant", 
            "content": response.content
        })
        
        # Process each tool call
        tool_results = []
        
        for content_block in response.content:
            if content_block.type == "tool_use":
                tool_name = content_block.name
                tool_input = content_block.input
                tool_use_id = content_block.id
                
                print(f"🔧 Using tool: {tool_name}")
                
                # Execute the appropriate tool
                if tool_name == "calculator_tool":
                    result = calculator_tool(tool_input["expression"])
                elif tool_name == "get_current_time":
                    timezone = tool_input.get("timezone", "UTC")
                    result = get_current_time(timezone)
                elif tool_name == "web_search":
                    query = tool_input["query"]
                    num_results = tool_input.get("num_results", 3)
                    result = web_search(query, num_results)
                else:
                    result = f"Error: Unknown tool '{tool_name}'"
                
                # Add tool result
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result
                })
        
        # Add tool results to conversation
        messages.append({
            "role": "user",
            "content": tool_results
        })
        
        # Get final response from Claude
        final_response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=1000,
            messages=messages,
            tools=tools
        )
        
        return final_response.content[0].text
        
    except Exception as e:
        print(f"Error handling tool calls: {e}")
        return "Sorry, I encountered an error while using tools."

def test_bot():
    """
    Test function to verify all tools work correctly
    """
    print("🧪 Testing all tools...\n")
    
    # Test Calculator
    print("=== Testing Calculator Tool ===")
    test_expressions = [
        "2 + 3 * 4",
        "sqrt(144)",
        "15% of 847",
        "sin(0)",
        "2 / 0"  # Test error handling
    ]
    
    for expr in test_expressions:
        result = calculator_tool(expr)
        print(f"calculator_tool('{expr}') -> {result}")
    
    print("\n=== Testing Time Tool ===")
    test_timezones = [
        "UTC",
        "US/Eastern", 
        "Asia/Tokyo",
        "Europe/London",
        "InvalidZone"  # Test error handling
    ]
    
    for tz in test_timezones:
        result = get_current_time(tz)
        print(f"get_current_time('{tz}') -> {result}")
    
    print("\n=== Testing Search Tool ===")
    test_queries = [
        ("Python programming", 2),
        ("artificial intelligence news", 3),
        ("", 2)  # Test error handling
    ]
    
    for query, num in test_queries:
        result = web_search(query, num)
        print(f"web_search('{query}', {num}) -> {result[:100]}...")
    
    print("\nTool testing complete!\n")

if __name__ == "__main__":
    # Uncomment the line below to run tests
    # test_bot()
    
    # Run the main chat bot
    main()