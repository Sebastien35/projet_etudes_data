class LLMInterface:
    def __init__(self, model_name, api_key):
        self.model_name = model_name
        self.api_key = api_key
        self.model = None
        self.api = None

    def send_message(self, message):
        pass
