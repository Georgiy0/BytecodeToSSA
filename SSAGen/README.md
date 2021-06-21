# SSAGen
A converter from Java bytecode to SSA representation via emulation.

bparser.py - the main class (Method) that implements bytecode parsing and emulation pipeline.
Bytecode disassembling is done using OPALDissasembler [https://www.opal-project.de/DeveloperTools.html]. It is planned to replace OPALDissasembler with javassist for better performance in the future.

emulators.py - contains a set of classes that handle emulation of different opcodes. It also contains two classes that emulate JVM frame: Stack and Variable array. The emulation takes into account only the fact of moving data from and into stack in order to create SSA. A helper method (Method.get_new_var) is used to allocate a new statically assigned variable.

Usgae: python3 bparser.py <class> <methods_db> <out ssa dir>
    - class - a path to the target class file
    - methods_db - a path to JSON-dictionary that contains JDK-methods database ("method name" -> index mapping). The database is updated during emulation.
    - out ssa dir - a path to the output directory where resulted ssa representations of methods will be stored.
    
Right now bparser.py is hardcoded to work with Juliet Java dataset. It looks up for methods bad(), goodG2B(), etc. in the target class file.