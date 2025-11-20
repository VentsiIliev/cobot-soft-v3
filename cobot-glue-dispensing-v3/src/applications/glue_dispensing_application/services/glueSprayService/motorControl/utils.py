def int_to_hex32(num):
    # Mask to 32 bits and format as 8 hex digits
    return f"0x{num & 0xFFFFFFFF:08X}"


def split_into_16bit(num):
    num32 = num & 0xFFFFFFFF
    high16 = (num32 >> 16) & 0x00FF
    low16 = num32 & 0xFFFF
    return f"0x{high16:04X}", f"0x{low16:04X}"