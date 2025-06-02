from dotenv import load_dotenv
import os
import json

load_dotenv()
URL = os.getenv('url')
if URL.endswith('/'):
    URL = URL[:-1]




