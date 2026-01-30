import csv
import subprocess
import logging
import argparse
import matplotlib.pyplot as plt
import time

# ===============================
# CONSTANTS
# ===============================
CSR_FILTER_EN_BIT = 0
CSR_COEF_EN_BASE  = 1
CSR_HALT_BIT      = 5
MAX_INPUT_SAMPLES = 100

# ===============================
# ARGPARSE & LOGGING
# ===============================
parser = argparse.ArgumentParser(description="Full FIR Validation with Comparison Plots")
parser.add_argument('--unit', default='impl0', help="Target hardware unit")
args = parser.parse_args()

logging.basicConfig(level=logging.INFO, format='%(message)s')

# ===============================
# HELPER FUNCTIONS
# ===============================
def pack_config(cfg_file):
    packed_coef = 0
    packed_csr  = (1 << CSR_FILTER_EN_BIT)

    with open(cfg_file, 'r') as f:
        for row in csv.DictReader(f):
            idx = int(row['coef'])
            val = int(row['value'], 16)

            packed_coef |= (val & 0xFF) << (idx * 8)

            if row['en'] == '1':
                packed_csr |= (1 << (CSR_COEF_EN_BASE + idx))

    return packed_coef, packed_csr


def configure_unit(packed_coef, packed_csr):
    halt_val = packed_csr | (1 << CSR_HALT_BIT)

    subprocess.run(
        ["./" + args.unit, "cfg", "--address", "0x0", "--data", hex(halt_val)],
        check=True
    )
    time.sleep(0.01)

    subprocess.run(
        ["./" + args.unit, "cfg", "--address", "0x4", "--data", hex(packed_coef)],
        check=True
    )

    subprocess.run(
        ["./" + args.unit, "cfg", "--address", "0x0", "--data", hex(packed_csr)],
        check=True
    )


def drive_signal(vec_file, input_store):
    output_vals = []

    with open(vec_file, 'r') as f:
        for line in f:
            sig_str = line.strip()
            if not sig_str:
                continue

            res = subprocess.run(
                ["./" + args.unit, "sig", "--data", sig_str],
                capture_output=True,
                text=True
            )

            try:
                val_in  = int(sig_str, 16)
                val_out = int(res.stdout.strip(), 16)

                if len(input_store) < MAX_INPUT_SAMPLES:
                    input_store.append(val_in)

                output_vals.append(val_out)

            except ValueError:
                continue

    return output_vals


# ===============================
# MAIN VALIDATION FLOW
# ===============================
def run_validation():
    cfg_files = ['p0.cfg', 'p4.cfg', 'p7.cfg', 'p9.cfg']
    all_results = {}
    input_signal_data = []

    for cfg in cfg_files:
        logging.info(f"\n>>> Running Validation Profile: {cfg} <<<")

        packed_coef, packed_csr = pack_config(cfg)
        configure_unit(packed_coef, packed_csr)

        logging.info(
            f"SUT Active. Config: {cfg}, CoefReg: {hex(packed_coef)}"
        )

        all_results[cfg] = drive_signal('sqr.vec', input_signal_data)

    # ===============================
    # PLOTTING (UNCHANGED OUTPUT)
    # ===============================
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Input vs Output Comparison for {args.unit}', fontsize=16)

    for i, cfg in enumerate(cfg_files):
        ax = axs[i // 2, i % 2]

        ax.plot(
            input_signal_data,
            label='Input (square.vec)',
            color='gray',
            linestyle='--',
            alpha=0.6
        )
        ax.plot(
            all_results[cfg],
            label='Filtered Output',
            color='blue',
            linewidth=2
        )

        ax.set_title(f"Configuration: {cfg}")
        ax.legend(loc='upper right')
        ax.grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()


if __name__ == "__main__":
    run_validation()
