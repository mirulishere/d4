import os
import subprocess

class Uad:
    """Driver class for FIR Filter Hardware"""
    def __init__(self, inst):
        self.inst = inst

    def reset(self):
        os.system(f'{self.inst} com --action reset')

    def enable(self):
        os.system(f'{self.inst} com --action enable')

    def disable(self):
        os.system(f'{self.inst} com --action disable')

    def write_coef(self, index, value):
        """Write a coefficient to the FIR"""
        os.system(f'{self.inst} coef --index {index} --write {hex(value)}')

    def write_input(self, value):
        """Write an input sample"""
        os.system(f'{self.inst} input --write {hex(value)}')

    def read_output(self):
        """Read one output sample"""
        out_bytes = subprocess.check_output(f'{self.inst} output --read', shell=True)
        return int(out_bytes.decode().strip(), 0)


def load_coefficients(uad, cfg_file):
    """Load coefficients from a .cfg file into the FIR"""
    print(f"Loading coefficients from {cfg_file}")
    with open(cfg_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            idx, val = line.split()
            uad.write_coef(int(idx), int(val, 0))


def read_vector(vec_file):
    """Read input vector file and return list of samples"""
    samples = []
    with open(vec_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            samples.append(int(line, 0))
    return samples


def run_filter_test(uad, cfg_file, vec_file):
    """Run FIR test with given coefficient file and input vector"""
    uad.reset()
    uad.enable()
    load_coefficients(uad, cfg_file)

    input_samples = read_vector(vec_file)
    output_samples = []

    for sample in input_samples:
        uad.write_input(sample)
        out = uad.read_output()
        output_samples.append(out)

    return output_samples


if __name__ == "__main__":
    impl = "impl0"
    cfg_files = ["p0.cfg", "p4.cfg", "p7.cfg", "p9.cfg"]
    vec_file = "square.vec"

    uad = Uad(impl)
    all_results = {}

    for cfg in cfg_files:
        print("\n==============================")
        print(f"Testing coefficients from {cfg}")
        print("==============================")
        out_samples = run_filter_test(uad, cfg, vec_file)
        all_results[cfg] = out_samples

    # Print first 16 output samples per configuration for observation
    print("\n=== Output Summary (first 16 samples) ===")
    for cfg, samples in all_results.items():
        print(f"\n{cfg}:")
        for i, val in enumerate(samples[:16]):
            print(f"  [{i:02d}] {val}")
