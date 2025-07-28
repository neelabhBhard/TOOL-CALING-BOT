import math
import ast
import operator
from datetime import datetime
import pytz
import requests
import json
from config import MAX_SEARCH_RESULTS

def calculator_tool(expression: str) -> str:
    """
    Safely evaluate mathematical expressions.
    
    Args:
        expression: Math expression like "2 + 3 * 4" or "sqrt(16)"
    
    Returns:
        String with the calculation result
    """
    try:
        # This is used to strip off the white spaces
        expression = expression.strip()
        
        if not expression:
            return "Error: Empty expression provided."
        
        # Handle percentage calculations - this is the fix!
        if '%' in expression:
            # Convert "15% of 847" to "15/100 * 847"
            expression = expression.replace('%', '/100')
            expression = expression.replace(' of ', ' * ')
            # Also handle "15% * 847" format
            expression = expression.replace('/100 * ', '/100 * ')
        
        # Helps the code understand math expression
        expression = expression.replace('sqrt', 'math.sqrt')
        expression = expression.replace('sin', 'math.sin')
        expression = expression.replace('cos', 'math.cos')
        expression = expression.replace('tan', 'math.tan')
        expression = expression.replace('log', 'math.log')
        
        # This will not let the user access dangerous builtin files like eval for security purpose.
        secure_dict = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max
        }
        
        result = eval(expression, secure_dict)
        
        # Round the result if it's a float with many decimal places
        if isinstance(result, float):
            result = round(result, 6)  # Round to 6 decimal places
        
        return f"Result: {result}"
        
    except ZeroDivisionError:
        return "Error: Division by zero is not allowed."
    except ValueError as e:
        return f"Error: Invalid value in expression. {str(e)}"
    except SyntaxError:
        return "Error: Invalid syntax in mathematical expression."
    except Exception as e:
        return f"Error: Invalid mathematical expression. Details: {str(e)}"
    
def get_current_time(timezone: str = "EST") -> str:
    """
    Get current time in specified timezone.
    
    Args:
        timezone: Timezone string like "UTC", "US/Eastern", "Asia/Tokyo"
    
    Returns:
        Formatted time string with timezone info
    """
    try:
        # Get the timezone object
        tz = pytz.timezone(timezone)
        
        # Get current time in that timezone
        current_time = datetime.now(tz)
        
        # Format the time in a readable way
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return f"Current time in {timezone}: {formatted_time}"
        
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Error: Unknown timezone '{timezone}'. Please use valid timezones like 'UTC', 'US/Eastern', 'Asia/Tokyo', etc."
    except Exception as e:
        return f"Error: Unable to get time for timezone '{timezone}'. {str(e)}"

from urllib.parse import quote

def web_search(query: str, num_results: int = 3) -> str:
    """
    Search the web and return top results.
    
    Args:
        query: Search terms
        num_results: Number of results to return (1-5)
    
    Returns:
        Formatted string with search results
    """
    if not query or not query.strip():
        return "Error: Empty search query provided"
    
    # Validate num_results
    if not isinstance(num_results, int) or num_results < 1 or num_results > 5:
        num_results = 3
    
    try:
        # Use DuckDuckGo Instant Answer API with proper encoding
        encoded_query = quote(query.strip())
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        
        # Add User-Agent header to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        # Check for instant answer
        if data.get('Answer') and data['Answer'].strip():
            results.append(f" Answer: {data['Answer']}")
            if data.get('AnswerType'):
                results.append(f"  Type: {data['AnswerType']}")
        
        # Check for abstract (Wikipedia-style results)
        if data.get('Abstract') and data['Abstract'].strip():
            abstract = data['Abstract'][:300] + "..." if len(data['Abstract']) > 300 else data['Abstract']
            results.append(f" Summary: {abstract}")
            if data.get('AbstractSource'):
                results.append(f"  Source: {data['AbstractSource']}")
            if data.get('AbstractURL'):
                results.append(f"  URL: {data['AbstractURL']}")
        
        # Check for definition
        if data.get('Definition') and data['Definition'].strip():
            definition = data['Definition'][:200] + "..." if len(data['Definition']) > 200 else data['Definition']
            results.append(f"Definition: {definition}")
            if data.get('DefinitionSource'):
                results.append(f"   Source: {data['DefinitionSource']}")
            if data.get('DefinitionURL'):
                results.append(f"    URL: {data['DefinitionURL']}")
        
        # Check for related topics
        if data.get('RelatedTopics') and isinstance(data['RelatedTopics'], list):
            added_topics = 0
            for topic in data['RelatedTopics']:
                if added_topics >= num_results:
                    break
                    
                if isinstance(topic, dict) and topic.get('Text'):
                    text = topic['Text'].strip()
                    if text:
                        # Limit text length and clean it up
                        clean_text = text[:150] + "..." if len(text) > 150 else text
                        results.append(f"🔍 Related: {clean_text}")
                        if topic.get('FirstURL'):
                            results.append(f"    URL: {topic['FirstURL']}")
                        added_topics += 1
        
        # Format final results
        if results:
            header = f"Search results for '{query}':\n"
            return header + "\n".join(results)
        else:
            return f"No results found for '{query}'. DuckDuckGo's API may not have information on this topic. Try:\n• More specific search terms\n• General topics instead of recent news\n• Company or product names"
            
    except requests.exceptions.Timeout:
        return "Error: Search request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Error: Network error during search - {str(e)}"
    except Exception as e:
        return f"Error searching for '{query}': {str(e)}"