# LSTM CWE 78 classification
A simple LSTM model for classification Java method into vulnerable/not vulnerable. It was tested on Juliet Java dataset for CWE 78 (command injections)

preprocess_bulk.py - uses SSAGen to prepare SSA representations for Juliet Java dataset.

simple_lstm.py - transforms SSA represenations into vector form for fitting into LSTM based binary classification model.