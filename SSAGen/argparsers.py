from abc import ABC, abstractmethod
import re

class Args(ABC):
    def __init__(self, raw):
        self.raw = raw

    @abstractmethod
    def Parse(self): pass
    
class DefaultArgs(Args):       
    def Parse(self): pass
    
    def __repr__(self): return self.raw
    def __str__(self): return self.raw
    
class RegexArgs(Args):
    REGEX = None
        
    def Parse(self):
        m = self.REGEX.match(self.raw)
        if m is None:
            raise ValueError(f"Unsupported args for {self.__class__.__name__} opcode: {self.raw}")
        self.captures = m.groupdict()

class GetStaticArgs(RegexArgs):
    REGEX = re.compile(r"(?P<class>[a-zA-Z\.0-9_]+)\s+{\s+(?P<stattype>[a-zA-Z\.0-9_]+)\s+(?P<statname>[a-zA-Z\.0-9_]+)\s+}")

    def Parse(self):
        super().Parse()
        self.cls = self.captures["class"]
        self.stattype = self.captures["stattype"]
        self.statname = self.captures["statname"]
        self.name = f"{self.cls}.{self.statname}"

    def __repr__(self): return self.name
    def __str__(self): return self.name
    
class InvokeVirtualArgs(RegexArgs):
    REGEX = re.compile(r"class\s+(?P<class>[a-zA-Z\.0-9_]+)\s+{\s+(?P<rettype>[a-zA-Z\.0-9]+)\s+(?P<method>[a-zA-Z\.0-9<>_]+)\s+\((?P<args>[a-zA-Z\.0-9,\s]*)\)\s+}")
        
    def Parse(self):
        super().Parse()
        self.cls = self.captures["class"]
        self.rettype = self.captures["rettype"]
        self.method = self.captures["method"]
        self.methodfull = f"{self.cls}.{self.method}"
        self.args = [a.strip() for a in self.captures["args"].split(",") if a.strip() != '']
        
        
    def __repr__(self): return f"{self.rettype} {self.cls}.{self.method} ({', '.join(self.args)})"
    def __str__(self): return f"{self.rettype} {self.cls}.{self.method} ({', '.join(self.args)})"
    
class InvokeSpecialArgs(InvokeVirtualArgs):
    pass
    
class InvokeStaticArgs(InvokeVirtualArgs):
    pass
    
class InvokeDynamicArgs(RegexArgs):
    REGEX = re.compile(r"(?P<rettype>[a-zA-Z\.0-9_]+)\s+(?P<method>[a-zA-Z\.0-9_]+)\s+\((?P<args>[a-zA-Z\.0-9,\s_]*)\).*")
    
    def Parse(self):
        super().Parse()
        self.rettype = self.captures["rettype"]
        self.method = self.captures["method"]
        self.methodfull = self.method
        self.args = [a.strip() for a in self.captures["args"].split(",")]
        
    def __repr__(self): return f"{self.rettype} {self.method} ({', '.join(self.args)})"
    def __str__(self): return f"{self.rettype} {self.method} ({', '.join(self.args)})"