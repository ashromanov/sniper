"""Optimized low-level functions using Numba JIT compilation."""

import numpy as np
from numba import njit


# Base58 alphabet as numpy array for fast indexing
_BASE58_ALPHABET = np.array(
    list("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"),
    dtype="U1",
)


@njit(cache=True, fastmath=True)
def _bytes_to_int(data: np.ndarray) -> int:
    """Convert bytes array to integer (big-endian).
    
    Args:
        data: Numpy array of uint8 bytes.
        
    Returns:
        Integer representation.
    """
    result = 0
    for byte in data:
        result = (result << 8) | byte
    return result


@njit(cache=True, fastmath=True)
def _count_leading_zeros(data: np.ndarray) -> int:
    """Count leading zero bytes.
    
    Args:
        data: Numpy array of uint8 bytes.
        
    Returns:
        Number of leading zeros.
    """
    count = 0
    for byte in data:
        if byte == 0:
            count += 1
        else:
            break
    return count


@njit(cache=True)
def _encode_base58_core(num: int, leading_zeros: int) -> tuple[np.ndarray, int]:
    """Core base58 encoding logic.
    
    Args:
        num: Integer to encode.
        leading_zeros: Number of leading zeros to prepend.
        
    Returns:
        Tuple of (result array, length).
    """
    # Pre-allocate max possible size (44 chars for 32 bytes)
    result = np.zeros(44, dtype=np.uint8)
    idx = 43
    
    # Encode from right to left
    while num > 0:
        num, rem = divmod(num, 58)
        result[idx] = rem
        idx -= 1
    
    # Add leading zeros as '1' (index 0 in base58 alphabet)
    for _ in range(leading_zeros):
        result[idx] = 0
        idx -= 1
    
    start = idx + 1
    length = 44 - start
    
    return result[start:], length


def bytes_to_pubkey_optimized(data: bytes) -> str:
    """Convert 32 bytes to base58 Solana pubkey using JIT-optimized functions.
    
    Args:
        data: 32-byte pubkey.
        
    Returns:
        Base58-encoded string.
    """
    # Convert to numpy array for numba
    arr = np.frombuffer(data, dtype=np.uint8)
    
    # Count leading zeros
    leading_zeros = _count_leading_zeros(arr)
    
    # Convert to integer
    num = _bytes_to_int(arr)
    
    # Encode to base58
    indices, length = _encode_base58_core(num, leading_zeros)
    
    # Map indices to alphabet characters
    result = "".join(_BASE58_ALPHABET[indices[:length]])
    
    return result
