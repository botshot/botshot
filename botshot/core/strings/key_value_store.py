from abc import ABC, abstractmethod
from typing import Optional


class KeyValueStore(ABC):

    def validate_key(self, key):
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")

    def validate_value(self, value):
        if not value or not isinstance(value, str):
            raise ValueError("Value must be a non-empty string")

    @abstractmethod
    def update(self, key: str, value: str, lang: Optional[str]):
        pass

    @abstractmethod
    def delete(self, key: str, lang: Optional[str]):
        pass

    @abstractmethod
    def get(self, key: str, lang: Optional[str]) -> Optional[str]:
        pass

    @abstractmethod
    def __contains__(self, key: str, lang: Optional[str]):
        pass

    def __getitem__(self, key: str, lang: Optional[str]) -> Optional[str]:
        return self.get(key, lang)

    def __setitem__(self, key: str, value: str, lang: Optional[str]):
        return self.update(key, value, lang)
