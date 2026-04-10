#!/usr/bin/env python3
"""
LuoOS Model Configuration
=========================
Smart model selection and configuration for optimal performance.

Features:
- Auto-detect available models from Ollama
- Intelligent model selection based on task type
- Model capability detection
- Performance-based recommendations

Created by Luo Kai (luokai25) — Enhanced by Claude Code
"""
import json
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ModelCapability(Enum):
    """Model capability levels."""
    SMALL = "small"          # < 4B params, fast but limited
    MEDIUM = "medium"        # 4-15B params, balanced
    LARGE = "large"          # 15-70B params, capable
    VERY_LARGE = "very_large"  # > 70B params, most capable


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    size: str  # e.g., "7b", "13b", "70b"
    family: str  # e.g., "llama", "mistral", "gemma"
    capabilities: ModelCapability
    context_length: int
    recommended_for: List[str]
    speed_rating: int  # 1-5, 5 is fastest
    quality_rating: int  # 1-5, 5 is best


# Model knowledge base
MODEL_INFO = {
    # Llama 3.1 models
    "llama3.1:405b": ModelInfo("llama3.1:405b", "405b", "llama", ModelCapability.VERY_LARGE, 131072, ["reasoning", "code", "creative"], 1, 5),
    "llama3.1:70b": ModelInfo("llama3.1:70b", "70b", "llama", ModelCapability.LARGE, 131072, ["reasoning", "code", "creative"], 2, 5),
    "llama3.1:8b": ModelInfo("llama3.1:8b", "8b", "llama", ModelCapability.MEDIUM, 131072, ["chat", "general"], 4, 3),
    "llama3.1": ModelInfo("llama3.1", "8b", "llama", ModelCapability.MEDIUM, 131072, ["chat", "general"], 4, 3),

    # Llama 3 models
    "llama3:70b": ModelInfo("llama3:70b", "70b", "llama", ModelCapability.LARGE, 8192, ["reasoning", "code"], 2, 4),
    "llama3:8b": ModelInfo("llama3:8b", "8b", "llama", ModelCapability.MEDIUM, 8192, ["chat", "general"], 4, 3),
    "llama3": ModelInfo("llama3", "8b", "llama", ModelCapability.MEDIUM, 8192, ["chat", "general"], 4, 3),

    # Mistral models
    "mistral:7b": ModelInfo("mistral:7b", "7b", "mistral", ModelCapability.MEDIUM, 32768, ["chat", "code", "general"], 4, 4),
    "mistral": ModelInfo("mistral", "7b", "mistral", ModelCapability.MEDIUM, 32768, ["chat", "code", "general"], 4, 4),
    "mixtral:8x7b": ModelInfo("mixtral:8x7b", "8x7b", "mistral", ModelCapability.LARGE, 32768, ["reasoning", "code"], 2, 4),
    "mixtral": ModelInfo("mixtral", "8x7b", "mistral", ModelCapability.LARGE, 32768, ["reasoning", "code"], 2, 4),
    "mixtral:8x22b": ModelInfo("mixtral:8x22b", "8x22b", "mistral", ModelCapability.LARGE, 65536, ["reasoning", "code"], 1, 5),

    # Gemma models
    "gemma2:27b": ModelInfo("gemma2:27b", "27b", "gemma", ModelCapability.LARGE, 8192, ["reasoning", "chat"], 2, 4),
    "gemma2:9b": ModelInfo("gemma2:9b", "9b", "gemma", ModelCapability.MEDIUM, 8192, ["chat", "general"], 4, 3),
    "gemma2": ModelInfo("gemma2", "9b", "gemma", ModelCapability.MEDIUM, 8192, ["chat", "general"], 4, 3),
    "gemma:7b": ModelInfo("gemma:7b", "7b", "gemma", ModelCapability.MEDIUM, 8192, ["chat"], 4, 3),

    # Qwen models
    "qwen2.5:72b": ModelInfo("qwen2.5:72b", "72b", "qwen", ModelCapability.LARGE, 131072, ["reasoning", "code"], 1, 5),
    "qwen2.5:32b": ModelInfo("qwen2.5:32b", "32b", "qwen", ModelCapability.LARGE, 32768, ["reasoning", "code"], 2, 4),
    "qwen2.5:14b": ModelInfo("qwen2.5:14b", "14b", "qwen", ModelCapability.MEDIUM, 32768, ["chat", "code"], 3, 3),
    "qwen2.5:7b": ModelInfo("qwen2.5:7b", "7b", "qwen", ModelCapability.MEDIUM, 32768, ["chat"], 4, 3),

    # Code models
    "codellama:34b": ModelInfo("codellama:34b", "34b", "codellama", ModelCapability.LARGE, 16384, ["code"], 2, 4),
    "codellama:13b": ModelInfo("codellama:13b", "13b", "codellama", ModelCapability.MEDIUM, 16384, ["code"], 3, 3),
    "codellama:7b": ModelInfo("codellama:7b", "7b", "codellama", ModelCapability.MEDIUM, 16384, ["code"], 4, 2),
    "deepseek-coder:33b": ModelInfo("deepseek-coder:33b", "33b", "deepseek", ModelCapability.LARGE, 16384, ["code"], 2, 5),
    "deepseek-coder:6.7b": ModelInfo("deepseek-coder:6.7b", "6.7b", "deepseek", ModelCapability.MEDIUM, 16384, ["code"], 4, 3),

    # Small models
    "phi3:14b": ModelInfo("phi3:14b", "14b", "phi", ModelCapability.MEDIUM, 16384, ["chat", "reasoning"], 4, 4),
    "phi3:3.8b": ModelInfo("phi3:3.8b", "3.8b", "phi", ModelCapability.SMALL, 4096, ["chat"], 5, 2),
    "tinyllama": ModelInfo("tinyllama", "1.1b", "tinyllama", ModelCapability.SMALL, 2048, ["chat"], 5, 1),
}


class ModelManager:
    """
    Manages model selection and configuration.
    """

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self._available_models: List[str] = []
        self._cached_info: Dict[str, ModelInfo] = {}

    def list_available_models(self) -> List[str]:
        """Get list of models available in Ollama."""
        try:
            with urllib.request.urlopen(f"{self.ollama_url}/api/tags", timeout=5) as r:
                data = json.loads(r.read())
                self._available_models = [m["name"] for m in data.get("models", [])]
                return self._available_models
        except urllib.error.URLError:
            return []
        except Exception:
            return []

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get info about a specific model."""
        # Check cache
        if model_name in self._cached_info:
            return self._cached_info[model_name]

        # Check known models
        for name, info in MODEL_INFO.items():
            if name in model_name.lower() or model_name.lower() in name:
                self._cached_info[model_name] = info
                return info

        # Unknown model - try to infer from name
        return self._infer_model_info(model_name)

    def _infer_model_info(self, model_name: str) -> ModelInfo:
        """Infer model info from model name."""
        name_lower = model_name.lower()

        # Try to extract size
        size = "unknown"
        for s in ["70b", "405b", "72b", "32b", "27b", "22b", "14b", "13b", "9b", "8b", "7b", "3.8b", "1.1b", "1b"]:
            if s in name_lower:
                size = s
                break

        # Try to infer family
        family = "unknown"
        for f in ["llama", "mistral", "gemma", "qwen", "codellama", "deepseek", "phi", "tiny"]:
            if f in name_lower:
                family = f
                break

        # Determine capability from size
        capability = ModelCapability.MEDIUM
        if size in ["1b", "1.1b", "3.8b"]:
            capability = ModelCapability.SMALL
        elif size in ["70b", "72b", "405b"]:
            capability = ModelCapability.VERY_LARGE if size == "405b" else ModelCapability.LARGE

        return ModelInfo(
            name=model_name,
            size=size,
            family=family,
            capabilities=capability,
            context_length=4096,
            recommended_for=["general"],
            speed_rating=3,
            quality_rating=3
        )

    def select_best_model(
        self,
        task_type: str = "general",
        prefer_speed: bool = False,
        prefer_quality: bool = False
    ) -> str:
        """
        Select the best available model for a task type.

        Args:
            task_type: Type of task ("chat", "code", "reasoning", "creative")
            prefer_speed: Prefer faster models
            prefer_quality: Prefer higher quality models

        Returns:
            Name of the best available model
        """
        available = self.list_available_models()
        if not available:
            return "mistral"  # Default fallback

        # Score each available model
        scores: List[Tuple[str, float]] = []

        for model in available:
            info = self.get_model_info(model)
            score = 0.0

            # Base score from quality rating
            score += info.quality_rating * 2

            # Bonus for task suitability
            if task_type in info.recommended_for:
                score += 3

            # Speed vs quality preference
            if prefer_speed:
                score += info.speed_rating
            elif prefer_quality:
                score += (5 - info.speed_rating) * 0.5

            # Capability bonus
            if info.capabilities == ModelCapability.VERY_LARGE:
                score += 2 if prefer_quality else 0.5
            elif info.capabilities == ModelCapability.LARGE:
                score += 1.5
            elif info.capabilities == ModelCapability.SMALL:
                score -= 1 if prefer_quality else 0

            scores.append((model, score))

        # Sort by score and return best
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0]

    def get_recommended_context_length(self, model_name: str) -> int:
        """Get recommended context length for a model."""
        info = self.get_model_info(model_name)
        return info.context_length if info else 4096

    def is_model_capable(self, model_name: str, task_type: str) -> bool:
        """Check if a model is suitable for a task type."""
        info = self.get_model_info(model_name)
        if not info:
            return True  # Assume capable if unknown

        # Small models struggle with complex tasks
        if info.capabilities == ModelCapability.SMALL:
            return task_type in ["chat", "general"]

        # Medium models can do most things
        if info.capabilities == ModelCapability.MEDIUM:
            return task_type in ["chat", "general", "code"]

        # Large models can do everything
        return True


# Default model preferences for different tasks
DEFAULT_MODELS = {
    "chat": ["mistral", "llama3:8b", "llama3.1:8b", "gemma2:9b"],
    "code": ["deepseek-coder:33b", "codellama:34b", "mistral", "mixtral"],
    "reasoning": ["llama3.1:70b", "mixtral:8x22b", "qwen2.5:72b", "mistral"],
    "creative": ["llama3.1:70b", "llama3:70b", "mistral", "gemma2:27b"],
    "fast": ["tinyllama", "phi3:3.8b", "mistral:7b", "llama3.1:8b"],
}


def create_model_manager(ollama_url: str = "http://localhost:11434") -> ModelManager:
    """Factory function to create a model manager."""
    return ModelManager(ollama_url)


# Quick helper functions
def get_best_available_model(ollama_url: str = "http://localhost:11434") -> str:
    """Quick function to get the best available model."""
    manager = ModelManager(ollama_url)
    return manager.select_best_model()


def get_fast_model(ollama_url: str = "http://localhost:11434") -> str:
    """Quick function to get a fast model."""
    manager = ModelManager(ollama_url)
    return manager.select_best_model(prefer_speed=True)


if __name__ == "__main__":
    # Test the model manager
    manager = ModelManager()

    print("Available models:")
    for model in manager.list_available_models():
        info = manager.get_model_info(model)
        if info:
            print(f"  {model}: {info.family} {info.size}, context={info.context_length}")

    print(f"\nBest for chat: {manager.select_best_model('chat')}")
    print(f"Best for code: {manager.select_best_model('code')}")
    print(f"Best for reasoning: {manager.select_best_model('reasoning')}")
    print(f"Fastest: {manager.select_best_model(prefer_speed=True)}")