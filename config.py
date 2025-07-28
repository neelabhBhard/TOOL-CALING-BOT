import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ATHROPIC_KEY")

USE_OPENAI = False
MODEL_NAME = "gpt-4" if USE_OPENAI else "claude-3-sonnet-20240229"

MAX_SEARCH_RESULTS = 5
