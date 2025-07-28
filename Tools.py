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
        
        # Helps the code understand math expression
        expression = expression.replace('sqrt', 'math.sqrt')
        expression = expression.replace('sin', 'math.sin')
        expression = expression.replace('cos', 'math.cos')
        expression = expression.replace('tan', 'math.tan')
        expression = expression.replace('log', 'math.log')
        
        # This will not let the user access dangeroud builtin files like eval for security purpose.
        secure_dict = {
            "__builtins__": {},
            "math": math
        }
        
        result = eval(expression, secure_dict)
        
        return f"Result: {result}"
        
    except ZeroDivisionError:
        return "Error: Division by zero is not allowed."
    except ValueError as e:
        return f"Error: Invalid value in expression. {str(e)}"
    except Exception as e:
        return f"Error: Invalid mathematical expression. Please check your syntax."
    
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
