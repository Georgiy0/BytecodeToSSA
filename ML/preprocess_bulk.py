import os, sys
from subprocess import call

command = 'python bparser.py {path} {methods_db} {ssaout}'

def main(dir, methods_db_path, ssaout_path):
    files = os.listdir(dir)
    cfiles = [os.path.join(dir, f) for f in files if f.endswith(".class")]
    for cf in cfiles:
        print(f"Processing {cf}...")
        call(command.format(path=cf, methods_db=methods_db_path, ssaout=ssaout_path))

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: .py <dir> <methods_db> <ssaout>")
        sys.exit(1)
    if not os.path.isdir(sys.argv[1]):
        print("[!] Invalid dir path.")
        sys.exit(1)
    if not os.path.isfile(sys.argv[2]):
        print("[!] Invalid methods db path.")
        sys.exit(1)
    if not os.path.isdir(sys.argv[3]):
        print("[!] Invalid ssaout path.")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])