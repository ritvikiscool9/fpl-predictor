import requests 

import requests
import pandas as pd
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.football-data.org/v4/"

if API_KEY is None:
    raise ValueError("API Key not found. Ensure you have a .env file.")


