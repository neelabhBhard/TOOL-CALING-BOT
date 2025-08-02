import math
import ast
import operator
from datetime import datetime
import pytz
import requests
import json
from config import MAX_SEARCH_RESULTS


import requests
from urllib.parse import quote

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
        
        # Handle percentage calculations
        if '%' in expression:
            expression = expression.replace('%', '/100')
            expression = expression.replace(' of ', ' * ')
            expression = expression.replace('/100 * ', '/100 * ')
        
        #Error handling to make sure code understands what to execute after user inputs
        expression = expression.replace('sqrt', 'math.sqrt')
        expression = expression.replace('sin', 'math.sin')
        expression = expression.replace('cos', 'math.cos')
        expression = expression.replace('tan', 'math.tan')
        expression = expression.replace('log', 'math.log')
        
        # To not let user use dangerous functions like "eval".
        secure_dict = {
            "__builtins__": {},
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max
        }
        
        result = eval(expression, secure_dict)
        
        # Rounding the result if it's a float with many decimal places
        if isinstance(result, float):
            result = round(result, 6) 
        
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
        # Getting the timezone object
        tz = pytz.timezone(timezone)
        
        # Getting current time in that timezone
        current_time = datetime.now(tz)
        
        # Formating the time in a readable way
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        
        return f"Current time in {timezone}: {formatted_time}"
        
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Error: Unknown timezone '{timezone}'. Please use valid timezones like 'UTC', 'US/Eastern', 'Asia/Tokyo', etc."
    except Exception as e:
        return f"Error: Unable to get time for timezone '{timezone}'. {str(e)}"

def web_search(query: str, num_results: int = 3) -> str:
    """
    Search the web and return top results.
   
    Args:
        query: Search terms
        num_results: Number of results to return (1-5)
   
    Returns:
         str: Formatted search results or error message.
    """
 
    # This is Input validation
    if not query or not query.strip():
        return "Error: Empty search query provided"
   
    # Validating and normalizing num_results parameters
    if not isinstance(num_results, int) or num_results < 1 or num_results > 5:
        num_results = 3
   
    # Clean and prepare query
    clean_query = query.strip()
   
    try:
        # This is to Try multiple query variations for better results
        queries_to_try = [
            clean_query,
            clean_query.replace("What is", "").replace("what is", "").strip(),
            "artificial intelligence" if "ai" in clean_query.lower() else clean_query
        ]
        
        for current_query in queries_to_try:
            # Skip empty queries
            if not current_query.strip():
                continue
                
            # Encode query for URL safety
            encoded_query = quote(current_query)
           
            # DuckDuckGo Instant Answer API endpoint
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
           
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
           
            # Making the API request
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
           
            # To parse the Json Response.
            data = response.json()
            results = []
           
            # Extracting from Answer field
            if data.get('Answer') and data.get('Answer').strip():
                results.append(f"Answer: {data['Answer']}")
                if data.get('AnswerType'):
                    results.append(f"   Source: {data.get('AnswerType', 'DuckDuckGo')}")
           
            # Extracting from Abstract field
            if data.get('Abstract') and data.get('Abstract').strip():
                if not (".ai is the Internet country code" in data['Abstract'] or "Anguilla" in data['Abstract']):
                    results.append(f"Summary: {data['Abstract']}")
                    if data.get('AbstractSource'):
                        results.append(f"   Source: {data['AbstractSource']}")
                        if data.get('AbstractURL'):
                            results.append(f"   URL: {data['AbstractURL']}")
            
            # Extracting from the AbstractText field
            if data.get('AbstractText') and data.get('AbstractText').strip():
                if not (".ai is" in data['AbstractText'] or "Anguilla" in data['AbstractText']):
                    results.append(f"Info: {data['AbstractText']}")
           
            # Extracting from the Definition field
            if data.get('Definition') and data.get('Definition').strip():
                results.append(f"Definition: {data['Definition']}")
                if data.get('DefinitionSource'):
                    results.append(f"   Source: {data['DefinitionSource']}")
            
            # Extracting from the Infobox
            if data.get('Infobox') and isinstance(data['Infobox'], dict):
                for key, value in data['Infobox'].items():
                    if value and str(value).strip() and len(str(value)) > 10:
                        results.append(f"{key}: {value}")
            
            # Extract from Array of results
            if data.get('Results') and isinstance(data['Results'], list):
                for i, result in enumerate(data['Results'][:num_results]):
                    if isinstance(result, dict):
                        if result.get('Text'):
                            results.append(f"Result {i+1}: {result['Text']}")
                        if result.get('FirstURL'):
                            results.append(f"   URL: {result['FirstURL']}")
           
            # Extracting data from related topic as search query
            if data.get('RelatedTopics') and len(results) < 3:
                topics_added = 0
                for topic in data['RelatedTopics']:
                    if topics_added >= 2:
                        break
                    if isinstance(topic, dict) and topic.get('Text'):
                        topic_text = topic['Text']
                        if not any(skip_word in topic_text.lower() for skip_word in ["anguilla", "country code", "domain", ".ai"]):
                            if len(topic_text) > 200:
                                topic_text = topic_text[:200] + "..."
                            results.append(f"Related: {topic_text}")
                            if topic.get('FirstURL'):
                                results.append(f"   URL: {topic['FirstURL']}")
                            topics_added += 1
            
        
            if results:
                header = f"Search results for '{clean_query}':\n"
                return header + "\n".join(results)
        
        # If all the search fails print the below
        return f"No results found for '{clean_query}'. DuckDuckGo's API did not return information for this topic. Try rephrasing your search with more specific terms."
           
    except requests.exceptions.Timeout:
        return "Error: Search request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Error: Network error during search - {str(e)}"
    except Exception as e:
        return f"Error searching for '{clean_query}': {str(e)}"