from collections.abc import AsyncIterator
from dataclasses import dataclass

import anthropic

from .config import Settings


@dataclass
class Completion:
    text: str
    stop_reason: str | None
    input_tokens: int
    output_tokens: int


class LLM:
    def __init__(self, settings: Settings):
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.request_timeout_s,
            max_retries=2,
        )
        self.model = settings.model
        self.max_output_tokens = settings.max_output_tokens

    async def complete(self, system: str, messages: list[dict]) -> Completion:
        msg = await self._client.messages.create(
            model=self.model, max_tokens=self.max_output_tokens, system=system, messages=messages
        )
        text = "".join(block.text for block in msg.content if block.type == "text")
        return Completion(text, msg.stop_reason, msg.usage.input_tokens, msg.usage.output_tokens)

    async def stream(self, system: str, messages: list[dict]) -> AsyncIterator[str | Completion]:
        async with self._client.messages.stream(
            model=self.model, max_tokens=self.max_output_tokens, system=system, messages=messages
        ) as stream:
            async for chunk in stream.text_stream:
                yield chunk
            final = await stream.get_final_message()
        text = "".join(block.text for block in final.content if block.type == "text")
        yield Completion(text, final.stop_reason, final.usage.input_tokens, final.usage.output_tokens)
