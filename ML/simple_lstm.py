import numpy
from keras.datasets import imdb
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers.embeddings import Embedding
from keras.preprocessing import sequence

from sklearn.model_selection import train_test_split

# fix random seed for reproducibility
numpy.random.seed(7)

import sys, os
import json

numpy.set_printoptions(threshold=sys.maxsize)

VARS_SIZE = 100
FUNCS_SIZE = 0

def transform_inst(inst_data):
    target = inst_data[0]
    func = inst_data[1]
    args = inst_data[2]
    target_ohe = [0] * VARS_SIZE
    if target is not None:
        target_ohe[target] = 1
    func_ohe = [0] * FUNCS_SIZE
    func_ohe[func] = 1
    args_map = [0] * VARS_SIZE
    for a in args:
        args_map[a] = 1
    vector = target_ohe + func_ohe + args_map
    return vector

def transform_sequence(ssa_data):
    instructions = []
    for inst_data in ssa_data:
        inst_vec = transform_inst(inst_data)
        instructions.append(inst_vec)
    if len(instructions) < 100:
        instructions += [[0] * (VARS_SIZE*2 + FUNCS_SIZE)] * (100 - len(instructions))
    return instructions
    
def ML(X, Y):
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.20, random_state=77)

    model = Sequential()
    model.add(LSTM(100, input_shape=(100, 224)))
    model.add(Dense(1, activation='sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    print(model.summary())
    model.fit(X_train, Y_train, validation_data=(X_test, Y_test), epochs=10, batch_size=64)
    
    print("Trained")
    # Final evaluation of the model
    scores = model.evaluate(X_test, Y_test, verbose=0)
    print("Accuracy: %.2f%%" % (scores[1]*100))

def main(methods_db_path, ssa_dir):
    methods_db = json.load(open(methods_db_path, 'r'))
    methods_cnt = len(methods_db) + 2 # the last indexs stands for wildcard methods
    global FUNCS_SIZE
    FUNCS_SIZE = methods_cnt
    print(f"Methods count: {methods_cnt}")
    ssa_files = [os.path.join(ssa_dir, f) for f in os.listdir(ssa_dir)]
    X = []
    Y = []
    for ssaf in ssa_files:
        ssaf_name = ssaf.split("\\")[-1]
        if ssaf_name.lower().find("bad") != -1:
            y = 1
        elif ssaf_name.lower().find("good") != -1:
            y = 0
        else:
            raise ValueError("No label indicator in file name")
        Y.append(y)
        x = transform_sequence(json.load(open(ssaf, 'r')))
        X.append(x)
    X_np = numpy.asarray(X)
    Y_np = numpy.asarray(Y)
    print(f"X shape: {X_np.shape}")
    print(f"Y shape: {Y_np.shape}")
    
    ML(X_np, Y_np)
    
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: .py <methods_db> <ssa dir>")
        sys.exit(1)
    if not os.path.isfile(sys.argv[1]):
        print("[!] Invalid methods db path.")
        sys.exit(1)
    if not os.path.isdir(sys.argv[2]):
        print("[!] Invlid ssa dir path.")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])