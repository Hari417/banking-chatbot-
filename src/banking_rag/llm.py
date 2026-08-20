"""
LLM Interface module for Banking RAG Chatbot.
Supports OpenAI-compatible and Ollama API endpoints.
"""

import os
import requests
from typing import List, Dict, Optional, Tuple, Generator
from dataclasses import dataclass, field
import logging

from .config import AppConfig, get_config
from typing import Union

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single chat message."""
    role: str  # 'system', 'user', or 'assistant'
    content: str
    name: Optional[str] = None


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    model: str
    usage: Optional[Dict] = None


class LLMClient:
    """
    LLM client supporting multiple backends:
    - OpenAI API (GPT-4o-mini, etc.)
    - OpenAI-compatible endpoints
    - Ollama (local LLMs)
    """
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize the LLM client."""
        self.config = config or get_config()
        self.llm_config = self.config.llm
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration."""
        if self.llm_config.provider not in ['openai', 'ollama', 'openai_compatible']:
            raise ValueError(f"Unsupported LLM provider: {self.llm_config.provider}")
        
        if self.llm_config.provider == 'openai':
            api_key = self.llm_config.get_api_key()
            if not api_key:
                logger.warning("OPENAI_API_KEY not set - LLM calls will fail")
    
    def _get_base_url(self) -> str:
        """Get the base URL for the API."""
        if self.llm_config.provider == 'ollama':
            return self.llm_config.ollama_base_url.rstrip('/')
        return self.llm_config.api_base.rstrip('/')

    def _get_chat_url(self) -> str:
        """Get the full chat endpoint URL."""
        if self.llm_config.provider == 'ollama':
            return f"{self._get_base_url()}/api/chat"
        return f"{self._get_base_url()}/chat/completions"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {'Content-Type': 'application/json'}
        
        if self.llm_config.provider in ['openai', 'openai_compatible']:
            api_key = self.llm_config.get_api_key()
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
        
        return headers
    
    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict:
        """Build the API request payload."""
        payload = {
            'model': self.llm_config.model,
            'messages': messages,
            'temperature': temperature or self.llm_config.temperature,
            'max_tokens': max_tokens or self.llm_config.max_tokens,
            'stream': stream,
        }

        if self.llm_config.provider == 'ollama':
            payload['think'] = False
        return payload
    
    def _handle_response(self, response: requests.Response) -> LLMResponse:
        """Handle API response (OpenAI or Ollama format)."""
        response.raise_for_status()
        data = response.json()

        if self.llm_config.provider == 'ollama':
            message = data.get('message', {})
            content = message.get('content', '')
            model = data.get('model', self.llm_config.model)
            usage = data.get('eval_count')
            return LLMResponse(content=content, model=model, usage=usage)

        if 'choices' not in data or len(data['choices']) == 0:
            raise ValueError("No choices returned in LLM response")

        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        model = data.get('model', self.llm_config.model)
        usage = data.get('usage')

        return LLMResponse(content=content, model=model, usage=usage)
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt text
            temperature: Sampling temperature (overrides config)
            max_tokens: Maximum tokens to generate (overrides config)
            stream: Whether to stream the response
            
        Returns:
            LLMResponse with generated content
        """
        messages = [
            {'role': 'system', 'content': 'You are a helpful banking assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return self.chat(messages, temperature, max_tokens, stream)
    
    def chat(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        """
        Chat with the LLM.
        
        Args:
            messages: List of ChatMessage objects
            temperature: Sampling temperature (overrides config)
            max_tokens: Maximum tokens to generate (overrides config)
            stream: Whether to stream the response
            
        Returns:
            LLMResponse with generated content
        """
        # Convert ChatMessages to dict format
        msg_dicts = [
            {
                'role': m['role'] if isinstance(m, dict) else m.role,
                'content': m['content'] if isinstance(m, dict) else m.content,
                **({'name': m['name']} if isinstance(m, dict) and m.get('name') else {}),
                **({'name': m.name} if not isinstance(m, dict) and m.name else {})
            }
            for m in messages
        ]
        
        if stream:
            return self._stream_chat(msg_dicts, temperature, max_tokens)
        
        try:
            response = requests.post(
                url=self._get_chat_url(),
                headers=self._get_headers(),
                json=self._build_payload(msg_dicts, temperature, max_tokens, stream),
                timeout=self.llm_config.timeout
            )
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API request failed: {e}")
            raise
    
    def _stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Stream Chat completion.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Yields:
            Chunks of the response
        """
        try:
            response = requests.post(
                url=self._get_chat_url(),
                headers=self._get_headers(),
                json=self._build_payload(messages, temperature, max_tokens, stream=True),
                timeout=self.llm_config.timeout,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        if data == '[DONE]':
                            break
                        try:
                            chunk = eval(data)  # Parse JSON-like data
                            content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            if content:
                                yield content
                        except Exception as e:
                            logger.warning(f"Failed to parse stream chunk: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM streaming failed: {e}")
            raise
    
    def available_models(self) -> List[str]:
        """
        Get list of available models from the API.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(
                url=f"{self._get_base_url()}/models",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return [m['id'] for m in data.get('data', [])]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch models: {e}")
            return [self.llm_config.model]  # Return configured model as fallback


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or get_config()
        self.llm_config = self.config.llm
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        return LLMResponse(
            content="This is a mock response for testing purposes.",
            model="mock-model"
        )
    
    def chat(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        return LLMResponse(
            content="This is a mock response for testing purposes.",
            model="mock-model"
        )


def get_llm_client(mock: bool = False, config: Optional[AppConfig] = None) -> LLMClient:
    """
    Factory function to get LLM client.
    
    Args:
        mock: Whether to use mock client for testing
        config: Configuration instance (uses global if not provided)
        
    Returns:
        LLMClient or MockLLMClient instance
    """
    if mock:
        return MockLLMClient(config)
    return LLMClient(config)
