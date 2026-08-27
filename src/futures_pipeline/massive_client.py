from massive import RESTClient
def create_massive_client(massive_api_key: str) -> RESTClient:
    return RESTClient(api_key=massive_api_key, verbose=True, retries=3)
