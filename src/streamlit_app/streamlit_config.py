import os


class StreamlitConfig:
    def __init__(self):
        self.title = "NLP Fake News Detector"
        self.description = "M1 Class project"
        self.api_url = os.getenv("API_URL", "http://localhost:8080/")
