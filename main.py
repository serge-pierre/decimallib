from decimallib import DecimalNumber, ROUND_HALF_EVEN

a = DecimalNumber('1.23')
b = DecimalNumber('4.567')

# Arithmetic — results are exact at the natural scale
print((a + b).get())    # '5.797'
print((a - b).get())    # '-3.337'
print((a * b).get())    # '5.61741'

# Division — scale and rounding mode are mandatory
print(a.divide(b, scale=6, mode=ROUND_HALF_EVEN).get())   # '0.269369'

# Quantize — round to a target scale in place
n = a * b           # '5.61741'
n.quantize(2, ROUND_HALF_EVEN)
print(n.get())   