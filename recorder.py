import asyncio
import time
from pathlib import Path

import numpy as np

from dyn200_modbus import DYN200Reader
from pulse_control import PulseControl
from tests import TESTS


dir_path = Path(__file__).parent / "data"


def get_id():
    files = dir_path.glob("./*.csv")
    int_suffixes = set()
    for file in files:
        suffixes = file.suffixes
        if len(suffixes) < 2:
            continue
        suffix = suffixes[-2]

        int_suff = None
        try:
            int_suff = int(suffix[1:])
        except ValueError:
            continue
        else:
            int_suffixes.add(int_suff)
    if not int_suffixes:
        return 0
    max_int = max(int_suffixes)
    if max_int is not None:
        return max_int + 1
    else:
        return 0


def process_mesurements(index, dataset, pulse, torque, t):
    cols, size = dataset.shape
    if index >= size:
        dataset.resize((cols, size * 2), refcheck=False)

    dataset[0][index] = t
    dataset[1][index] = pulse
    dataset[2][index] = torque


def save_data(path, dataset):
    with open(path, "wb") as outfile:
        np.savetxt(
            outfile,
            np.transpose(dataset),
            delimiter=",",
            newline="\n",
            header="t,pulse,torque",
        )


async def run_test(
    dyn_reader, pulse_control, schedule, name, duration, hz=100, warning_sync=0.002
):
    file_path = dir_path / f"{name}.{get_id()}.csv"
    resolved_path = file_path.resolve()
    array = np.zeros((3, duration * hz), dtype=np.float32)
    start = time.time()
    current_time = 0
    try:
        ind = 0
        while current_time <= duration:
            before = time.time()

            await schedule(pulse_control, current_time, duration)
            torque = dyn_reader.read_torque()
            await asyncio.sleep(0)  # give cyphal handlers a chance to run
            pulse = pulse_control.pulse
            if np.isnan(pulse):
                print("Saw 'NaN' pulse")
                continue

            after = time.time()
            dt = after - before
            current_time = after - start
            is_synced = (dt - 1 / hz) < warning_sync
            if not is_synced:
                print(f"OUT OF SYNC: {pulse=}, {torque=}")

            process_mesurements(ind, array, pulse, torque, current_time)

            ind += 1
            if ind % 500 == 0:
                save_data(resolved_path, array)
    except KeyboardInterrupt:
        pass
    finally:
        save_data(resolved_path, array)


async def main():
    duration = 60
    delay = 4

    dyn_reader = DYN200Reader()
    pulse_control = PulseControl()
    pulse_control.start()

    for test_name, schedule in TESTS.items():
        print(f"Running <{test_name}>")
        await run_test(dyn_reader, pulse_control, schedule, test_name, duration)
        await asyncio.sleep(delay)

    pulse_control.close()


asyncio.run(main())
