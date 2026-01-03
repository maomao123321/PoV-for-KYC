from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
from typing import Any, Dict, Optional

import httpx

from .exceptions import ModelCallError, SchemaValidationError
from .schemas import ExtractionPayload

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are a KYC document parser. Return strict JSON only. "
    "If a field is unreadable, set it to null and add it to missing_fields."
)


class FireworksExtractor:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "accounts/fireworks/models/qwen2p5-vl-32b-instruct",
        fallback_model: str = "accounts/fireworks/models/qwen2p5-vl-32b-instruct",
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_base: float = 0.8,
    ) -> None:
        self.api_key = api_key or os.getenv("FIREWORKS_API_KEY", "")
        self.model = model
        self.fallback_model = fallback_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "FireworksExtractor":
        self._client = httpx.AsyncClient(
            base_url="https://api.fireworks.ai/inference/v1",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client:
            await self._client.aclose()

    async def extract(
        self,
        image_bytes: bytes,
        mime_type: str,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> ExtractionPayload:
        if not self._client:
            raise RuntimeError("Extractor must be used as an async context manager.")

        data_url = self._to_data_url(image_bytes, mime_type)
        schema_def = ExtractionPayload.model_json_schema()
        user_text = (
            "Extract passport or driver's license fields into the provided schema. "
            "Return ai_confidence, missing_fields, evidence, mrz_raw. "
            "Do not add commentary."
        )
        body = self._build_body(data_url, system_prompt, user_text, schema_def, self.model)
        # Primary attempt
        try:
            response_payload = await self._post_with_retry(body)
            return self._parse_payload(response_payload)
        except SchemaValidationError:
            # Retry once on parse issues
            try:
                retry_payload = await self._post_with_retry(body)
                return self._parse_payload(retry_payload)
            except SchemaValidationError:
                pass
        except ModelCallError:
            pass

        # Fallback model if primary failed to call or parse
        fallback_body = self._build_body(
            data_url, system_prompt, user_text, schema_def, self.fallback_model
        )
        fallback_response = await self._post_with_retry(fallback_body)
        return self._parse_payload(fallback_response)

    def _build_body(
        self,
        data_url: str,
        system_prompt: str,
        user_text: str,
        schema_def: Dict[str, Any],
        model_name: str,
    ) -> Dict[str, Any]:
        return {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": json.dumps(schema_def, indent=2)},
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "max_tokens": 2000,
        }

    async def _post_with_retry(self, body: Dict[str, Any]) -> Dict[str, Any]:
        assert self._client
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(
                    "/chat/completions", json=body, timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code not in {429, 500, 502, 503, 504}:
                    raise ModelCallError(str(exc)) from exc
            except httpx.RequestError as exc:
                # network/timeout
                if attempt == self.max_retries - 1:
                    raise ModelCallError(str(exc)) from exc
            await asyncio.sleep(self.backoff_base * (2**attempt))
        raise ModelCallError("Model call failed after retries.")

    def _parse_payload(self, response: Dict[str, Any]) -> ExtractionPayload:
        try:
            message = response["choices"][0]["message"]
            if "parsed" in message and isinstance(message["parsed"], dict):
                parsed = message["parsed"]
            else:
                content = message.get("content")
                text_blob = self._content_to_str(content)
                logger.debug(f"Raw content from model: {text_blob[:500]}")
                parsed = self._coerce_json(text_blob)
            return ExtractionPayload.model_validate(parsed)
        except (KeyError, json.JSONDecodeError, ValueError) as exc:
            logger.error(f"Parse failed. Response keys: {response.keys()}, error: {exc}")
            raise SchemaValidationError(f"Failed to parse structured output: {exc}") from exc

    @staticmethod
    def _content_to_str(content: Any) -> str:
        """
        Fireworks may return content as a string or list of text blocks.
        Normalize to a single string before json parsing.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, str):
                    texts.append(block)
                elif isinstance(block, dict) and "text" in block:
                    texts.append(str(block["text"]))
            return "".join(texts)
        return str(content)

    @staticmethod
    def _coerce_json(raw_text: str) -> Dict[str, Any]:
        """Try to robustly parse JSON payloads, handling fenced or partial content."""
        text = raw_text.strip()
        # Strip code fences if present
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        # Fast path
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Attempt to extract outermost braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            return json.loads(candidate)

        # Reraise with original context
        return json.loads(text)

    @staticmethod
    def _to_data_url(image_bytes: bytes, mime_type: str) -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

