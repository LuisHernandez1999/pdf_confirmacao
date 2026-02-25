from abc import ABC, abstractmethod

class StorageService(ABC):

    @abstractmethod
    def upload_file(self, file_path: str, key: str) -> str:
        pass