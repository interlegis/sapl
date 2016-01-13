

def int_to_roman(int_value):
    # if isinstance(int_value, type(1)):
    #    raise TypeError("expected integer, got %s" % type(int_value))
    if not 0 < int_value < 4000:
        raise ValueError("Argument must be between 1 and 3999")
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M', 'CM', 'D', 'CD', 'C', 'XC',
            'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
    result = ""
    for i in range(len(ints)):
        count = int(int_value / ints[i])
        result += nums[i] * count
        int_value -= ints[i] * count
    return result


def int_to_letter(int_value):
    result = ''
    int_value -= 1
    while int_value >= 26:
        rest = int_value % 26
        int_value = int(int_value / 26) - 1
        result = chr(rest + 65) + result
    result = chr(int_value + 65) + result
    return result
