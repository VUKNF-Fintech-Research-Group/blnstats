import datetime
import json
from decimal import Decimal
import re
import base64


def timestamp_to_datetime_string(timestamp):
    """
    Convert a Unix timestamp to a formatted datetime string.

    Args:
        timestamp (int): Unix timestamp

    Returns:
        str: Formatted datetime string (YYYY-MM-DD HH:MM:SS)
    """
    dt_object = datetime.datetime.fromtimestamp(timestamp)
    return dt_object.strftime('%Y-%m-%d %H:%M:%S')



def hex_to_onion(hex_str):
    """
    Convert a hex string to an onion address.

    Args:
        hex_str (str): Hexadecimal string

    Returns:
        str: Onion address
    """
    decoded_bytes = bytes.fromhex(hex_str)
    encoded_base32 = base64.b32encode(decoded_bytes).decode('utf-8').lower().rstrip('=')
    return f"{encoded_base32}.onion"



def parse_date(date_string):
    """
    Parse a date string into a datetime object.

    Args:
        date_string (str): Date string in the format 'YYYY-MM-DD'

    Returns:
        datetime.date: Parsed date object
    """
    return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()



def format_satoshis_as_btc(satoshis):
    """
    Convert satoshis to BTC and format as a string.

    Args:
        satoshis (int): Amount in satoshis

    Returns:
        str: Formatted BTC amount
    """
    btc = satoshis / 100000000
    return f"{btc:.8f} BTC"



def safe_divide(numerator, denominator):
    """
    Perform division safely, returning 0 if the denominator is 0.

    Args:
        numerator (float): Numerator
        denominator (float): Denominator

    Returns:
        float: Result of division, or 0 if denominator is 0
    """
    return numerator / denominator if denominator != 0 else 0



def is_valid_bitcoin_address(address):
    """
    Check if a given string is a valid Bitcoin address.
    This is a basic check and doesn't guarantee the address is actually in use.

    Args:
        address (str): Bitcoin address to validate

    Returns:
        bool: True if the address format is valid, False otherwise
    """
    # Regular expression for Bitcoin addresses
    pattern = r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[ac-hj-np-z02-9]{39,59}$'
    return bool(re.match(pattern, address))

