import os
from dotenv import load_dotenv

load_dotenv()

# API 설정
API_URL = os.getenv("API_URL", "https://artify-content-api.onrender.com")
API_KEY = os.getenv("API_KEY", "")

# 앱 설정
APP_NAME = "Artify Content Platform"
VERSION = "1.0.0"
