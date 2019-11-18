#!/usr/bin/env python

import argparse
import json

from typing import List, Tuple

from Crypto.Hash import keccak as keccak_thing


def load_deployment_addreses(filename: str) -> dict:
    with open(filename, 'r') as f:
        address_map = json.load(f)
        address_map = {key: value.lower().split('0x')[1]
                             for key, value in address_map.items()}
        print(f"Loaded {len(address_map)} mainnet addresses.")
    return address_map


def load_storage_keys(filename: str) -> List:
    with open(filename, 'r') as f:
        keys = json.load(f)
        keys = [key.lower().split('0x')[1] for key in keys]
        print(f"Loaded {len(keys)} nonzero storage keys.")
    return keys


def keccak(s: bytes) -> str:
    keccak_hash = keccak_thing.new(digest_bits=256)
    keccak_hash.update(s)
    return keccak_hash.hexdigest()


def key_from_1d_mapping(offset: int, a: str) -> str:
    sixtyfour = bytes.fromhex(a).rjust(32, b'\x00') \
        + bytes([offset]).rjust(32, b'\x00')
    assert len(sixtyfour) == 64
    return keccak(sixtyfour)


def key_from_2d_mapping(offset: int, a: str, b: str) -> str:
    sixtyfour = bytes.fromhex(b).rjust(32, b'\x00') \
        + bytes.fromhex(key_from_1d_mapping(offset, a))
    assert len(sixtyfour) == 64
    return keccak(sixtyfour)


def key_struct_pos(a: str, pos: int):
    key_as_int = int(a, 16) + pos
    key_as_hex = hex(key_as_int).split('0x')[1]
    return key_as_hex


def subtract_wards(address_map: dict, expected_wards: List[str], keys: set):
    for contract in expected_wards:
        slot = key_from_1d_mapping(0, address_map[contract])
        if slot in keys:
            print(f"{contract} at 0x{address_map[contract]} is a ward.")
            print(f"(slot is 0x{slot})")
            keys.remove(slot)
        else:
            print(f"WARNING: {contract} at 0x{address_map[contract]} is"
                  " not a ward!")


def subtract_cans(address_map: dict, expected_wishes: Tuple[str, str], keys: set):
    for (trustor, trustee) in expected_wishes:
        who, usr = address_map[trustor], address_map[trustee]
        slot = key_from_2d_mapping(1, who, usr)
        if slot in keys:
            print(f"{trustor} has hoped {trustee}.")
            print(f"(slot is 0x{slot})")
            keys.remove(slot)
        else:
            print(f"WARNING: {trustor} has NOT hoped {trustee}!")


def subtract_ilk_inits(expected_ilks: str, keys: set):
    for ilk in expected_ilks:
        slot = key_struct_pos(key_from_1d_mapping(2, ilk), 1)
        if slot in keys:
            print(f"Ilk {ilk} has been initialised.")
            print(f"(slot is 0x{slot})")
            keys.remove(slot)
        else:
            print(f"WARNING: Ilk {ilk} has NOT been initialised!")


def subtract_others(expected_keys: List[str], keys: set):
    for key in expected_keys:
        if key in keys:
            keys.remove(key)
            print(f"Key {key} is nonzero.")
        else:
            print(f"WARNING: Key {key} is zero.")


parser = argparse.ArgumentParser(prog='verify-dss-deploy')
parser.add_argument("--keys", help="File containing a (JSON-encoded) list of"
                    " storage keys", type=str, required=True)
parser.add_argument("--contracts", help="File containing a (JSON-encoded)"
                    " dictionary of deployed contracts.", type=str, required=True)
arguments = parser.parse_args()

vat_keys = load_storage_keys(arguments.keys)
address_map = load_deployment_addreses(arguments.contracts)

keys_unaccounted = set(vat_keys)
print(f"Starting with {len(keys_unaccounted)} nonzero storage keys...")

vat_expected_wards = [
    'MCD_CAT',
    'MCD_SPOT',
    'MCD_JUG',
    'MCD_POT',
    'MCD_END',
    'MCD_PAUSE_PROXY',
    'MCD_JOIN_SAI',
    'MCD_JOIN_ETH_A',
    'MCD_JOIN_BAT_A'
]

vat_expected_cans = [
    ('MCD_CAT', 'MCD_FLIP_SAI'),
    ('MCD_CAT', 'MCD_FLIP_ETH_A'),
    ('MCD_CAT', 'MCD_FLIP_BAT_A'),
    ('MCD_VOW', 'MCD_FLAP')
]

vat_expected_ilks = [
    'SAI',
    'ETH-A',
    'BAT-A'
]


vat_other_known_keys = [
    # vat live flag
    '000000000000000000000000000000000000000000000000000000000000000a'
]

vat_expected_ilk_inits = [bytes(symbol, 'ASCII').ljust(32, b'\x00').hex()
                          for symbol in vat_expected_ilks]

subtract_wards(address_map, vat_expected_wards, keys_unaccounted)
subtract_cans(address_map, vat_expected_cans, keys_unaccounted)
subtract_ilk_inits(vat_expected_ilk_inits, keys_unaccounted)
subtract_others(vat_other_known_keys, keys_unaccounted)
print(f"{len(keys_unaccounted)} keys could not be accounted for.")

# print(keys_unaccounted)
