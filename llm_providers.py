"""
LLMプロバイダー抽象化レイヤー

複数のLLMプロバイダー（OpenAI、Groq等）を統一的に扱うための抽象化層。
プロバイダーの切り替えは、このファイルの先頭の定数を変更するだけで可能。
"""

from abc import ABC, abstractmethod
from typing import Optional
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# ==========================================
# 🔧 現在使用中のLLMプロバイダー設定
# ==========================================
# この行を変更するだけでプロバイダーを切り替え可能
CURRENT_PROVIDER = "groq"  # "openai" または "groq"
CURRENT_MODEL = "openai/gpt-oss-120b"
# Groq推論モデル用の設定（openai/で始まるモデルの場合のみ使用）
CURRENT_REASONING_EFFORT = "medium"  # "low", "medium", "high"
CURRENT_MAX_COMPLETION_TOKENS = 8192
# ==========================================


class LLMProvider(ABC):
    """LLMプロバイダーの抽象基底クラス"""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        プロンプトを受け取り、LLMの応答を返す

        Args:
            prompt (str): 入力プロンプト

        Returns:
            str: LLMの応答テキスト
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """使用中のモデル名を返す（プロバイダー名を含む）"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI APIプロバイダー"""

    def __init__(self, model: str = "gpt-4o"):
        """
        Args:
            model (str): 使用するOpenAIモデル名
                例: "gpt-4o", "gpt-4o-mini", "gpt-5-nano", "o1-preview"
        """
        from openai import OpenAI  # 遅延インポート

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

        self.client = OpenAI(api_key=api_key)
        self._model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def generate(self, prompt: str) -> str:
        """OpenAI APIを呼び出してテキスト生成（リトライ付き）"""
        try:
            response = self.client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ OpenAI API呼び出しエラー: {e}")
            raise

    @property
    def model_name(self) -> str:
        return f"openai/{self._model}"


class GroqProvider(LLMProvider):
    """Groq APIプロバイダー"""

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        reasoning_effort: Optional[str] = None,
        max_completion_tokens: int = 8192
    ):
        """
        Args:
            model (str): 使用するGroqモデル名
                例: "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-120b"
            reasoning_effort (str, optional): 推論モデル用のパラメータ ("low", "medium", "high")
                openai/gpt-oss-120bなどの推論モデルで使用
            max_completion_tokens (int): 最大出力トークン数（デフォルト: 8192）
        """
        from groq import Groq  # 遅延インポート

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY環境変数が設定されていません")

        self.client = Groq(api_key=api_key)
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._max_completion_tokens = max_completion_tokens

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def generate(self, prompt: str) -> str:
        """Groq APIを呼び出してテキスト生成（リトライ付き）"""
        try:
            # 基本パラメータ
            params = {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "max_completion_tokens": self._max_completion_tokens,
                "temperature": 1,
                "top_p": 1
            }

            # 推論モデル用のパラメータを追加（openai/で始まるモデルの場合）
            if self._model.startswith("openai/") and self._reasoning_effort:
                params["reasoning_effort"] = self._reasoning_effort

            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ Groq API呼び出しエラー: {e}")
            raise

    @property
    def model_name(self) -> str:
        return f"groq/{self._model}"


class LLMFactory:
    """LLMプロバイダーのファクトリークラス"""

    @staticmethod
    def create(provider: str, model: Optional[str] = None) -> LLMProvider:
        """
        指定されたプロバイダーとモデルでLLMProviderインスタンスを作成

        Args:
            provider (str): プロバイダー名 ("openai", "groq")
            model (str, optional): モデル名。Noneの場合はデフォルトを使用

        Returns:
            LLMProvider: 指定されたプロバイダーのインスタンス

        Raises:
            ValueError: 未知のプロバイダー名が指定された場合
        """
        provider = provider.lower()

        if provider == "openai":
            default_model = "gpt-4o"
            return OpenAIProvider(model or default_model)

        elif provider == "groq":
            default_model = "llama-3.3-70b-versatile"
            return GroqProvider(model or default_model)

        else:
            raise ValueError(
                f"未知のプロバイダー: {provider}\n"
                f"対応プロバイダー: openai, groq"
            )

    @staticmethod
    def get_current() -> LLMProvider:
        """
        現在設定されているLLMプロバイダーを取得

        このファイル先頭の CURRENT_PROVIDER と CURRENT_MODEL 定数を使用

        Returns:
            LLMProvider: 現在のプロバイダーインスタンス
        """
        print(f"🤖 使用LLMプロバイダー: {CURRENT_PROVIDER}/{CURRENT_MODEL}")

        if CURRENT_PROVIDER.lower() == "groq":
            # Groqプロバイダーの場合、推論モデルのパラメータも渡す
            return GroqProvider(
                model=CURRENT_MODEL,
                reasoning_effort=CURRENT_REASONING_EFFORT if CURRENT_MODEL.startswith("openai/") else None,
                max_completion_tokens=CURRENT_MAX_COMPLETION_TOKENS
            )
        else:
            # OpenAIなど他のプロバイダーの場合
            return LLMFactory.create(CURRENT_PROVIDER, CURRENT_MODEL)


# 便利な関数：現在のLLMを取得
def get_current_llm() -> LLMProvider:
    """現在設定されているLLMプロバイダーを取得（エイリアス）"""
    return LLMFactory.get_current()
