from typing import List, Dict


class PipPackages:
    def __init__(self, packages: Dict | None):
        self.packages = packages

    @classmethod
    def from_list(cls, *packages: str):
        return cls({p : {} for p in packages})


    @classmethod
    def from_dict(cls, *packages: Dict):
        cls.packages = {}
        for package in packages:
            name = package["name"]
            del package["name"]
            cls.packages[name] = package