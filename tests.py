import numpy as np


TESTS = {}


def named(name: str | None = None):
    def wrapper(func):
        nonlocal name
        if name is None:
            name = func.__name__
        TESTS[name] = func
        return func

    return wrapper


def part_pulse(pulse_control, t, duration, div):
    pulse = 0
    leg_duration = duration / 2

    if t < leg_duration:
        pulse = t / leg_duration
    elif t < (leg_duration * 2):
        pulse = (leg_duration * 2 - t) / leg_duration
    else:
        pulse = 0

    pulse = pulse / div
    return pulse_control.write(pulse), pulse


@named()
async def half_pulse(pulse_control, t, duration):
    writer, pulse = part_pulse(pulse_control, t, duration, 2)
    await writer
    return pulse


@named()
async def quarter_pulse(pulse_control, t, duration):
    writer, pulse = part_pulse(pulse_control, t, duration, 4)
    await writer
    return pulse


@named()
async def sixth_pulse(pulse_control, t, duration):
    writer, pulse = part_pulse(pulse_control, t, duration, 8)
    await writer
    return pulse


@named()
async def quarter_sin(pulse_control, t, duration):
    pulse = (np.sin(t / 4) + 1) / 8
    await pulse_control.write(pulse)
    return pulse


@named()
async def half_sin(pulse_control, t, duration):
    pulse = (np.sin(t / 4) + 1) / 4
    await pulse_control.write(pulse)
    return pulse
