from datetime import datetime
from typing import List

class Source:
    id: None
    name: str

    def __init__(self, id: None, name: str) -> None:
        self.id = id
        self.name = name


class Article:
    source: Source
    author: str
    title: str
    description: str
    url: str
    url_to_image: str
    published_at: datetime
    content: str

    def __init__(self, source: Source, author: str, title: str, description: str, url: str, url_to_image: str, published_at: datetime, content: str) -> None:
        self.source = source
        self.author = author
        self.title = title
        self.description = description
        self.url = url
        self.url_to_image = url_to_image
        self.published_at = published_at
        self.content = content


class EverythingResponse:
    status: str
    total_results: int
    articles: List[Article]

    def __init__(self, status: str, total_results: int, articles: List[Article]) -> None:
        self.status = status
        self.total_results = total_results
        self.articles = articles