from abc import abstractmethod, ABC
from typing import Tuple, Optional, List

from model.StreamData import StreamData
from model.SubData import SubData


class Provider(ABC):

    @abstractmethod
    def search(self, query: str):
        pass

    @abstractmethod
    def get_streams_data(self, src_bytes: bytes) -> Tuple[Optional[List[StreamData]], Optional[List[SubData]]]:
        pass

    @abstractmethod
    def get_premium(self):
        pass