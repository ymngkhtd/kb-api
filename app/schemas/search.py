"""Search request/response schemas."""

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    q: str
    path: str = ""
    extensions: list[str] = Field(default=[".md", ".txt"])
    max_results: int = Field(default=50, le=200)
    use_regex: bool = False


class SemanticSearchQuery(BaseModel):
    query: str
    path: str = ""
    top_k: int = Field(default=10, le=50)


class ClassifyRequest(BaseModel):
    title: str
    content: str


class SearchMatch(BaseModel):
    line: int
    text: str


class SearchResult(BaseModel):
    path: str
    name: str
    matches: list[SearchMatch]
    match_count: int


class SemanticResult(BaseModel):
    path: str
    snippet: str
    score: float


class ClassifySuggestion(BaseModel):
    category: str
    suggested_path: str
    confidence: float
    reason: str
