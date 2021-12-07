import pint

# Initialize the global unit registry
ureg = pint.UnitRegistry()

# Define common aliases
Q_ = ureg.Quantity

# Pre-load common units for quick access
meter = ureg.meter
second = ureg.second
kilogram = ureg.kilogram
pascal = ureg.pascal
celsius = ureg.celsius
kelvin = ureg.kelvin
volt = ureg.volt
ampere = ureg.ampere

# Rocketry specific or useful derivations
ureg.define('g_force = 9.80665 * meter / second**2 = g0')
