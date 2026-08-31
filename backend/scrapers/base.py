from abc import ABC, abstractmethod
from typing import List
from ..models import SearchCriteria, FlatListing


class BaseScraper(ABC):
    portal_name: str = "base"

    @abstractmethod
    async def search(self, criteria: SearchCriteria) -> List[FlatListing]:
        """Search the portal for flat listings matching criteria."""
        pass
