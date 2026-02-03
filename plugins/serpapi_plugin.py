from serpapi import GoogleSearch

from .plugin import StreamDeckPlugin


class SerpAPIPlugin(StreamDeckPlugin):
    api_key: str = ""

    def __init__(self, api_key: str = "", **data):
        super().__init__(**data)
        self.api_key = api_key

    @staticmethod
    def search(
        query: str, api_key: str, engine: str = "google_ai_mode", cc: str = "US"
    ) -> list[dict]:
        """Fetch organic search results from SerpAPI.

        Args:
            query: Search query string
            api_key: SerpAPI API key
            engine: Search engine to use (default: "bing")
            cc: Country code (default: "US")

        Returns:
            List of organic search results
        """
        params = {
            "engine": engine,
            "q": query,
            "cc": cc,
            "api_key": api_key,
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        return results.get("text_blocks", [])

    @staticmethod
    def parse_text_blocks(text_blocks: list[dict]) -> str:
        """Parse text_blocks from SerpAPI response into readable text.

        Args:
            text_blocks: List of text block dictionaries from SerpAPI response

        Returns:
            Formatted string with parsed content
        """
        output = []
        for block in text_blocks:
            block_type = block.get("type", "")
            if block_type == "heading":
                snippet = block.get("snippet", "")
                output.append(f"\n## {snippet}\n")
            elif block_type == "paragraph":
                snippet = block.get("snippet", "")
                output.append(snippet)
            elif block_type == "list":
                items = block.get("list", [])
                for item in items:
                    snippet = item.get("snippet", "")
                    output.append(f"  - {snippet}")
        return "\n".join(output)
