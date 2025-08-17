from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class EnumRepository(ABC):

    # single function to get enum by name
    @abstractmethod
    def get_enum_by_name(self, name: str) -> Optional[Any]:
        pass