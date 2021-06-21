# BytecodeToSSA
A converter from Java bytecode to SSA representation for ML applications.

SSAGen - implements a simple JVM bytecode emulator in order to unroll the stack during method execution and create methods SSA representation.

ML - contains a set of python scripts that prepare SSA representations received from SSAGen and fit them into a simple classification model (vulnerable/not vulnerable) based on a LSTM layer and dense layer for classification.