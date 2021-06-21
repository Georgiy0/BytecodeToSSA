from abc import ABC, abstractmethod

class JVMStack(object):
    def __init__(self):
        self.stack = []
        
    def push(self, var):
        self.stack.append(var)
        
    def pop(self):
        if len(self.stack) == 0:
            raise EmulationError(f"Stack empty")
        return self.stack.pop()
        
    def __str__(self):
        stackelems = [f"V{v}" for v in self.stack]
        return str(stackelems)
    def __repr__(self):
        stackelems = [f"V{v}" for v in self.stack]
        return str(stackelems)

class JVMVarArray(object):
    def __init__(self, size):
        self.vararr = [None] * size
        self.max_written = 0
        
    def __getitem__(self, key):
        try:
            var = self.vararr[key]
        except IndexError:
            raise EmulationError(f"Not enough VARARR space")
        if var is None:
            raise EmulationError(f"Accessing not initialized cell of VARARR")
        return var
            
    def __setitem__(self, key, value):
        if key > self.max_written:
            self.max_written = key
        try:
            self.vararr[key] = value
        except IndexError:
            raise EmulationError(f"Not enough VARARR space")
            
    def __str__(self):
        vararrelems = ["NOVAR" if e is None else f"V{e}" for e in self.vararr[:self.max_written + 1]]
        return str(vararrelems)
    def __repr__(self):
        vararrelems = ["NOVAR" if e is None else f"V{e}" for e in self.vararr[:self.max_written + 1]]
        return str(vararrelems)
        
class EmulationContext(object):
    def __init__(self, ssaout, instructions, stack, vararr, methods_db, newVarGetter):
        self.instructions = instructions
        self.stack = stack
        self.vararr = vararr
        self.methods_db = methods_db
        self.get_new_var = newVarGetter
        self.ssaout = ssaout
        
    def get_new_var(self):
        return self.get_new_var()
        
    def add_ssaout_inst(self, target, function, args):
        self.ssaout.append([target, function, args])


class EmulationError(Exception):
    pass

class InstEmulator(ABC):
    @abstractmethod
    def Emulate(self, inst, econtext): pass

class DefaultInstEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        
class AconstNullEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        retvar = econtext.get_new_var()
        econtext.stack.push(retvar)
        method = "special.aconstnull"
        if method not in econtext.methods_db:
            econtext.methods_db[method] = len(econtext.methods_db) + 1
        func = econtext.methods_db[method]
        econtext.add_ssaout_inst(retvar, func, [])
            
class LoadConstEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        retvar = econtext.get_new_var()
        econtext.stack.push(retvar)
        method = "special.loadconst"
        if method not in econtext.methods_db:
            econtext.methods_db[method] = len(econtext.methods_db) + 1
        func = econtext.methods_db[method]
        econtext.add_ssaout_inst(retvar, func, [])
        
class AloadEmulator(InstEmulator):
    def __init__(self, index):
        self.index = index
        
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        index = self.index if self.index is not None else int(inst.args.raw)
        var = econtext.vararr[index]
        econtext.stack.push(var)
        
class AstoreEmulator(InstEmulator):
    def __init__(self, index):
        self.index = index
        
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        var = econtext.stack.pop()
        index = self.index if self.index is not None else int(inst.args.raw)
        econtext.vararr[index] = var
        
class PopEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        econtext.stack.pop()
        
class DupEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        var = econtext.stack.pop()
        econtext.stack.push(var)
        econtext.stack.push(var)
        
class IfIntCmpEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        econtext.stack.pop()
        
class GotoEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        pos = econtext.instructions.index(inst)
        previousInst = econtext.instructions[pos - 1]
        if previousInst.opcode == 182: # if it was invokevirtual
            econtext.stack.push(econtext.get_new_var()) # push thrown exception on stack
            print(f"Pushed exception object on stack")
            
class GetStaticEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        econtext.stack.push(econtext.get_new_var())
        method = inst.args.name
        if method.startswith("java.") and method not in econtext.methods_db:
            econtext.methods_db[method] = len(econtext.methods_db) + 1
        
class InvokeVirtualEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        argc = len(inst.args.args)
        argv = [econtext.stack.pop() for _ in range(argc)]
        argv.reverse()
        obj = econtext.stack.pop()
        retvar = None
        if inst.args.rettype != 'void':
            retvar = econtext.get_new_var()
            econtext.stack.push(retvar)
        method = inst.args.methodfull
        if method.startswith("java.") and method not in econtext.methods_db:
            econtext.methods_db[method] = len(econtext.methods_db) + 1
        func = econtext.methods_db[method] if method in econtext.methods_db else len(econtext.methods_db) + 1
        econtext.add_ssaout_inst(retvar, func, argv)
        print(f"Calling: {inst.args.rettype} {inst.args.method} (this=V{obj}, {', '.join([f'V{v}' for v in argv])})")

class InvokeSpecialEmulator(InvokeVirtualEmulator):
    pass
    
class InvokeStaticEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        argc = len(inst.args.args)
        argv = [econtext.stack.pop() for _ in range(argc)]
        argv.reverse()
        retvar = None
        if inst.args.rettype != 'void':
            retvar = econtext.get_new_var()
            econtext.stack.push(retvar)
        method = inst.args.methodfull
        if method.startswith("java.") and method not in econtext.methods_db:
            econtext.methods_db[method] = len(econtext.methods_db) + 1
        func = econtext.methods_db[method] if method in econtext.methods_db else len(econtext.methods_db) + 1
        econtext.add_ssaout_inst(retvar, func, argv)
        print(f"Calling: {inst.args.rettype} {inst.args.method} ({', '.join([f'V{v}' for v in argv])})")
        
class InvokeDynamicEmulator(InvokeStaticEmulator):
    pass
    
class NewEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        retvar = econtext.get_new_var()
        econtext.stack.push(retvar)
        method = inst.args.raw.strip()
        if method.startswith("java.") and method not in econtext.methods_db:
            econtext.methods_db[method] = len(econtext.methods_db) + 1
        func = econtext.methods_db[method] if method in econtext.methods_db else len(econtext.methods_db) + 1
        econtext.add_ssaout_inst(retvar, func, [])
    
class AthrowEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        econtext.stack.pop()
        
class IfnullEmulator(InstEmulator):
    def Emulate(self, inst, econtext):
        print(f"Emulating. {inst}")
        econtext.stack.pop()