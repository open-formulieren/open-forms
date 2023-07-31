from openforms.pre_requests.clients import PreRequestZGWClient


def free_address_search(client: PreRequestZGWClient, query: str):
    # using retrieve rather than list so we can provide the URL explicitly -
    # we don't have much guarantees about the operationId
    return client.retrieve(
        resource="free",
        url="v3_1/free",
        request_kwargs={"params": {"q": query}},
    )
