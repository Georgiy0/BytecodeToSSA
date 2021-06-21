import sys, os
import json
from subprocess import call
import tempfile
from bs4 import BeautifulSoup
from argparsers import *
from emulators import *
from mnemonics import MNEMONICS

DISASM_CMD = "java__SEP__-jar__SEP__OPALDisassembler.jar__SEP__-source__SEP__{src}__SEP__-o__SEP__{output}"
    
class Instruction(object):
    ARGPARSE = {
        178: GetStaticArgs,
        182: InvokeVirtualArgs,
        183: InvokeSpecialArgs,
        184: InvokeStaticArgs,
        186: InvokeDynamicArgs
    }
    
    EMULATE = {
        1: AconstNullEmulator(),
        18: LoadConstEmulator(),
        25: AloadEmulator(None),
        42: AloadEmulator(0),
        43: AloadEmulator(1),
        44: AloadEmulator(2),
        45: AloadEmulator(3),
        58: AstoreEmulator(None),
        75: AstoreEmulator(0),
        76: AstoreEmulator(1),
        77: AstoreEmulator(2),
        78: AstoreEmulator(3),
        87: PopEmulator(),
        89: DupEmulator(),
        153: IfIntCmpEmulator(),
        154: IfIntCmpEmulator(),
        155: IfIntCmpEmulator(),
        156: IfIntCmpEmulator(),
        157: IfIntCmpEmulator(),
        158: IfIntCmpEmulator(),
        167: GotoEmulator(),
        178: GetStaticEmulator(),
        182: InvokeVirtualEmulator(),
        183: InvokeSpecialEmulator(),
        184: InvokeStaticEmulator(),
        186: InvokeDynamicEmulator(),
        187: NewEmulator(),
        191: AthrowEmulator(),
        198: IfnullEmulator(),
    }
    
    DEFAULT_EMLATOR = DefaultInstEmulator()
    
    def __init__(self, row):
        self.hasArgs = False
        self.args = None
        columns = row.find_all("td")
        self.pc = int(columns[0].text)
        instruction_info = columns[2]
        
        opcode = instruction_info.find_all("span", {"class": "instruction"})
        if len(opcode) != 1:
            raise ValueError("Couldn't find instruction opcode")
        self.mnem = opcode[0].text.strip()
        try:
            self.opcode = MNEMONICS[self.mnem]
        except KeyError as e:
            raise ValueError(f"Unregistered mnemonic: {self.mnem}")
        
        self.instruction_info = opcode[0].parent
        children = list(self.instruction_info.findChildren("span", recursive=False))
        if len(children) == 2:
            self.hasArgs = True
            rawargs = children[1].text.strip()
        else: # goto support
            children = list(self.instruction_info.findChildren("a", recursive=False))
            if len(children) == 1:
                self.hasArgs = True
                rawargs = children[0].text.strip()
        if self.hasArgs:
            if self.opcode in Instruction.ARGPARSE:
                self.args = Instruction.ARGPARSE[self.opcode](rawargs)
            else:
                self.args = DefaultArgs(rawargs)
            self.args.Parse()
            
        # init emulator
        if self.opcode in Instruction.EMULATE:
            self.emulator = Instruction.EMULATE[self.opcode]
        else:
            self.emulator = Instruction.DEFAULT_EMLATOR
            
    def Emulate(self, econtext):
        self.emulator.Emulate(self, econtext)
            
    def __has_args(self):
        return self.hasArgs
        
    def __repr_args(self): return f" {self.args}" if self.__has_args() else ""
    def __str__(self): return f"{self.pc}: {self.mnem} ({self.opcode})" + self.__repr_args()
    def __repr__(self): return f"{self.pc}: {self.mnem} ({self.opcode})" + self.__repr_args()

class Method(object):
    VARARR_SIZE = 500
    NO_VAR = 0

    def __init__(self, soup, method, method_db):
        self.method = method
        self.method_db = method_db
        self.instructions = None
        method_data = soup.find_all(attrs={"class": "method", "data-name": method})
        if len(method_data) != 1:
            raise ValueError("Method data wasn't found")
        self.method_data = method_data[0]
        self.current_var = 0
        
        self.stack = None
        self.vararr = None
        self.ssaout = None
        
    def Parse(self):
        instruction_table = self.method_data.find_all("table", {"class": "method_bytecode"})
        if len(instruction_table) != 1:
            raise ValueError("No instruction table was found")
        instruction_table = instruction_table[0]
        rows = instruction_table.find_all("tr")
        rows.pop(0)
        self.instructions = [Instruction(row) for row in rows]
        
    def get_new_var(self):
        self.current_var += 1
        print(f"Created var V{self.current_var}")
        return self.current_var
        
    def EmulatorState(self):
        print(f"\tSTACK:  {self.stack}")
        print(f"\tVARARR: {self.vararr}")
        
    def Emulate(self):
        self.stack = JVMStack()
        self.vararr = JVMVarArray(Method.VARARR_SIZE)
        self.vararr[0] = self.get_new_var() # put THIS to the VARARRAY
        self.ssaout = []
        
        econtext = EmulationContext(self.ssaout, self.instructions, self.stack, self.vararr, self.method_db, self.get_new_var)
        for i in self.instructions:
            self.EmulatorState()
            i.Emulate(econtext)
        if len(self.stack.stack) != 0:
            raise ValueError("Stack is not empty after emulation")
        
    def PrintBody(self):
        for i in self.instructions:
            print(i)
        
def invoke(command, args={}):
    call(command.format(**args).split("__SEP__"))
    
def get_temp_file_path():
    t = tempfile.NamedTemporaryFile()
    name = t.name
    t.close()
    return name

def main(class_file, method_db_path, ssaout_path):
    temp = get_temp_file_path()
    invoke(DISASM_CMD, {"src": class_file, "output": temp})
    method_db = json.load(open(method_db_path, 'r'))
    with open(temp) as fp:
        soup = BeautifulSoup(fp, 'html.parser')
        all_methods = soup.find_all("details", {"class": "method"})
        all_methods = [e["data-name"] for e in all_methods]
        for method_name in [m for m in all_methods if m == "bad" or (m != "good" and m.startswith("good"))]:
            print(f"Processing method '{method_name}' for class {class_file}...")
            m = Method(soup, method_name, method_db)
            m.Parse()
            m.Emulate()
            class_file_name = class_file.split("\\")[-1]
            outpath = os.path.join(ssaout_path, f"{class_file_name.replace('.class', '')}_{method_name}.ssa")
            json.dump(m.ssaout, open(outpath, 'w'), indent=4)
    json.dump(m.method_db, open(method_db_path, 'w'), indent=4)
    
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: .py <path to .class file to analyse> <method db path> <out ssa dir>")
        sys.exit(1)
    if not os.path.isfile(sys.argv[1]):
        print("[!] Invalid class file path.")
        sys.exit(1)
    if not os.path.isfile(sys.argv[2]):
        print("[!] Invalid method db file path.")
        sys.exit(1)
    if not os.path.isdir(sys.argv[3]):
        print("[!] Invalid ssaout dir.")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])