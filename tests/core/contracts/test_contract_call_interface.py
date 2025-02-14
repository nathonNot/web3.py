from decimal import (
    Decimal,
    getcontext,
)
from distutils.version import (
    LooseVersion,
)
import json
import pytest

import eth_abi
from eth_tester.exceptions import (
    TransactionFailed,
)
from eth_utils import (
    is_text,
)
from eth_utils.toolz import (
    identity,
)
from hexbytes import (
    HexBytes,
)

from web3._utils.ens import (
    contract_ens_addresses,
)
from web3.exceptions import (
    BadFunctionCallOutput,
    BlockNumberOutofRange,
    FallbackNotFound,
    InvalidAddress,
    MismatchedABI,
    NoABIFound,
    NoABIFunctionsFound,
    ValidationError,
)


def deploy(w3, Contract, apply_func=identity, args=None):
    args = args or []
    deploy_txn = Contract.constructor(*args).transact()
    deploy_receipt = w3.eth.wait_for_transaction_receipt(deploy_txn)
    assert deploy_receipt is not None
    address = apply_func(deploy_receipt['contractAddress'])
    contract = Contract(address=address)
    assert contract.address == address
    assert len(w3.eth.get_code(contract.address)) > 0
    return contract


@pytest.fixture()
def address_reflector_contract(w3, AddressReflectorContract, address_conversion_func):
    return deploy(w3, AddressReflectorContract, address_conversion_func)


@pytest.fixture()
def math_contract(w3, MathContract, address_conversion_func):
    return deploy(w3, MathContract, address_conversion_func)


@pytest.fixture()
def string_contract(w3, StringContract, address_conversion_func):
    return deploy(w3, StringContract, address_conversion_func, args=["Caqalai"])


@pytest.fixture()
def arrays_contract(w3, ArraysContract, address_conversion_func):
    # bytes_32 = [keccak('0'), keccak('1')]
    bytes32_array = [
        b'\x04HR\xb2\xa6p\xad\xe5@~x\xfb(c\xc5\x1d\xe9\xfc\xb9eB\xa0q\x86\xfe:\xed\xa6\xbb\x8a\x11m',  # noqa: E501
        b'\xc8\x9e\xfd\xaaT\xc0\xf2\x0cz\xdfa(\x82\xdf\tP\xf5\xa9Qc~\x03\x07\xcd\xcbLg/)\x8b\x8b\xc6',  # noqa: E501
    ]
    byte_arr = [b'\xff', b'\xff', b'\xff', b'\xff']
    return deploy(w3, ArraysContract, address_conversion_func, args=[bytes32_array, byte_arr])


@pytest.fixture()
def strict_arrays_contract(w3_strict_abi, StrictArraysContract, address_conversion_func):
    # bytes_32 = [keccak('0'), keccak('1')]
    bytes32_array = [
        b'\x04HR\xb2\xa6p\xad\xe5@~x\xfb(c\xc5\x1d\xe9\xfc\xb9eB\xa0q\x86\xfe:\xed\xa6\xbb\x8a\x11m',  # noqa: E501
        b'\xc8\x9e\xfd\xaaT\xc0\xf2\x0cz\xdfa(\x82\xdf\tP\xf5\xa9Qc~\x03\x07\xcd\xcbLg/)\x8b\x8b\xc6',  # noqa: E501
    ]
    byte_arr = [b'\xff', b'\xff', b'\xff', b'\xff']
    return deploy(
        w3_strict_abi,
        StrictArraysContract,
        address_conversion_func,
        args=[bytes32_array, byte_arr]
    )


@pytest.fixture()
def address_contract(w3, WithConstructorAddressArgumentsContract, address_conversion_func):
    return deploy(
        w3,
        WithConstructorAddressArgumentsContract,
        address_conversion_func,
        args=["0xd3CdA913deB6f67967B99D67aCDFa1712C293601"]
    )


@pytest.fixture(params=[b'\x04\x06', '0x0406', '0406'])
def bytes_contract(w3, BytesContract, request, address_conversion_func):
    if is_text(request.param) and request.param[:2] != '0x':
        with pytest.warns(
            DeprecationWarning,
            match='in v6 it will be invalid to pass a hex string without the "0x" prefix'
        ):
            return deploy(w3, BytesContract, address_conversion_func, args=[request.param])
    else:
        return deploy(w3, BytesContract, address_conversion_func, args=[request.param])


@pytest.fixture()
def fixed_reflection_contract(w3, FixedReflectionContract, address_conversion_func):
    return deploy(w3, FixedReflectionContract, address_conversion_func)


@pytest.fixture()
def payable_tester_contract(w3, PayableTesterContract, address_conversion_func):
    return deploy(w3, PayableTesterContract, address_conversion_func)


@pytest.fixture()
def revert_contract(w3, RevertContract, address_conversion_func):
    return deploy(w3, RevertContract, address_conversion_func)


@pytest.fixture()
def call_transaction():
    return {
        'data': '0x61bc221a',
        'to': '0xc305c901078781C232A2a521C2aF7980f8385ee9'
    }


@pytest.fixture(params=[
    '0x0406040604060406040604060406040604060406040604060406040604060406',
    '0406040604060406040604060406040604060406040604060406040604060406',
    HexBytes('0406040604060406040604060406040604060406040604060406040604060406'),
])
def bytes32_contract(w3, Bytes32Contract, request, address_conversion_func):
    if is_text(request.param) and request.param[:2] != '0x':
        with pytest.warns(DeprecationWarning):
            return deploy(w3, Bytes32Contract, address_conversion_func, args=[request.param])
    else:
        return deploy(w3, Bytes32Contract, address_conversion_func, args=[request.param])


@pytest.fixture()
def undeployed_math_contract(MathContract, address_conversion_func):
    empty_address = address_conversion_func("0x000000000000000000000000000000000000dEaD")
    _undeployed_math_contract = MathContract(address=empty_address)
    return _undeployed_math_contract


@pytest.fixture()
def mismatched_math_contract(w3, StringContract, MathContract, address_conversion_func):
    deploy_txn = StringContract.constructor("Caqalai").transact()
    deploy_receipt = w3.eth.wait_for_transaction_receipt(deploy_txn)
    assert deploy_receipt is not None
    address = address_conversion_func(deploy_receipt['contractAddress'])
    _mismatched_math_contract = MathContract(address=address)
    return _mismatched_math_contract


@pytest.fixture()
def fallback_function_contract(w3, FallbackFunctionContract, address_conversion_func):
    return deploy(w3, FallbackFunctionContract, address_conversion_func)


@pytest.fixture()
def receive_function_contract(w3, ReceiveFunctionContract, address_conversion_func):
    return deploy(w3, ReceiveFunctionContract, address_conversion_func)


@pytest.fixture()
def no_receive_function_contract(w3, NoReceiveFunctionContract, address_conversion_func):
    return deploy(w3, NoReceiveFunctionContract, address_conversion_func)


@pytest.fixture()
def tuple_contract(w3, TupleContract, address_conversion_func):
    return deploy(w3, TupleContract, address_conversion_func)


@pytest.fixture()
def nested_tuple_contract(w3, NestedTupleContract, address_conversion_func):
    return deploy(w3, NestedTupleContract, address_conversion_func)


def test_invalid_address_in_deploy_arg(WithConstructorAddressArgumentsContract):
    with pytest.raises(InvalidAddress):
        WithConstructorAddressArgumentsContract.constructor(
            "0xd3cda913deb6f67967b99d67acdfa1712c293601",
        ).transact()


def test_call_with_no_arguments(math_contract, call):
    result = call(contract=math_contract,
                  contract_function='return13')
    assert result == 13


def test_call_with_one_argument(math_contract, call):
    result = call(contract=math_contract,
                  contract_function='multiply7',
                  func_args=[3])
    assert result == 21


@pytest.mark.parametrize(
    'call_args,call_kwargs',
    (
        ((9, 7), {}),
        ((9,), {'b': 7}),
        (tuple(), {'a': 9, 'b': 7}),
    ),
)
def test_call_with_multiple_arguments(math_contract, call, call_args, call_kwargs):
    result = call(contract=math_contract,
                  contract_function='add',
                  func_args=call_args,
                  func_kwargs=call_kwargs)
    assert result == 16


@pytest.mark.parametrize(
    'call_args,call_kwargs',
    (
        ((9, 7), {}),
        ((9,), {'b': 7}),
        (tuple(), {'a': 9, 'b': 7}),
    ),
)
def test_saved_method_call_with_multiple_arguments(math_contract, call_args, call_kwargs):
    math_contract_add = math_contract.functions.add(*call_args, **call_kwargs)
    result = math_contract_add.call()
    assert result == 16


def test_call_get_string_value(string_contract, call):
    result = call(contract=string_contract,
                  contract_function='getValue')
    # eth_abi.decode_abi() does not assume implicit utf-8
    # encoding of string return values. Thus, we need to decode
    # ourselves for fair comparison.
    assert result == "Caqalai"


@pytest.mark.skipif(
    LooseVersion(eth_abi.__version__) >= LooseVersion("2"),
    reason="eth-abi >=2 does utf-8 string decoding")
def test_call_read_string_variable(string_contract, call):
    result = call(contract=string_contract,
                  contract_function='constValue')
    assert result == b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff".decode(errors='backslashreplace')  # noqa: E501


@pytest.mark.skipif(
    LooseVersion(eth_abi.__version__) < LooseVersion("2"),
    reason="eth-abi does not raise exception on undecodable bytestrings")
def test_call_on_undecodable_string(string_contract, call):
    with pytest.raises(BadFunctionCallOutput):
        call(
            contract=string_contract,
            contract_function='constValue')


def test_call_get_bytes32_array(arrays_contract, call):
    result = call(contract=arrays_contract,
                  contract_function='getBytes32Value')
    # expected_bytes32_array = [keccak('0'), keccak('1')]
    expected_bytes32_array = [
        b'\x04HR\xb2\xa6p\xad\xe5@~x\xfb(c\xc5\x1d\xe9\xfc\xb9eB\xa0q\x86\xfe:\xed\xa6\xbb\x8a\x11m',  # noqa: E501
        b'\xc8\x9e\xfd\xaaT\xc0\xf2\x0cz\xdfa(\x82\xdf\tP\xf5\xa9Qc~\x03\x07\xcd\xcbLg/)\x8b\x8b\xc6',  # noqa: E501
    ]
    assert result == expected_bytes32_array


def test_call_get_bytes32_const_array(arrays_contract, call):
    result = call(contract=arrays_contract,
                  contract_function='getBytes32ConstValue')
    # expected_bytes32_array = [keccak('A'), keccak('B')]
    expected_bytes32_array = [
        b'\x03x?\xac.\xfe\xd8\xfb\xc9\xadD>Y.\xe3\x0ea\xd6_G\x11@\xc1\x0c\xa1U\xe97\xb45\xb7`',
        b'\x1fg[\xff\x07Q_]\xf9g7\x19N\xa9E\xc3lA\xe7\xb4\xfc\xef0{|\xd4\xd0\xe6\x02\xa6\x91\x11',
    ]
    assert result == expected_bytes32_array


def test_call_get_byte_array(arrays_contract, call):
    result = call(contract=arrays_contract,
                  contract_function='getByteValue')
    expected_byte_arr = [b'\xff', b'\xff', b'\xff', b'\xff']
    assert result == expected_byte_arr


@pytest.mark.parametrize('args,expected', [([b''], [b'\x00']), (['0x'], [b'\x00'])])
def test_set_byte_array(arrays_contract, call, transact, args, expected):
    transact(
        contract=arrays_contract,
        contract_function='setByteValue',
        func_args=[args]
    )
    result = call(contract=arrays_contract,
                  contract_function='getByteValue')

    assert result == expected


@pytest.mark.parametrize(
    'args,expected', [
        ([b'1'], [b'1']),
        (['0xDe'], [b'\xDe'])
    ]
)
def test_set_strict_byte_array(strict_arrays_contract, call, transact, args, expected):
    transact(
        contract=strict_arrays_contract,
        contract_function='setByteValue',
        func_args=[args]
    )
    result = call(contract=strict_arrays_contract,
                  contract_function='getByteValue')

    assert result == expected


@pytest.mark.parametrize('args', ([''], ['s']))
def test_set_strict_byte_array_with_invalid_args(strict_arrays_contract, transact, args):
    with pytest.raises(ValidationError):
        transact(
            contract=strict_arrays_contract,
            contract_function='setByteValue',
            func_args=[args]
        )


def test_call_get_byte_const_array(arrays_contract, call):
    result = call(contract=arrays_contract,
                  contract_function='getByteConstValue')
    expected_byte_arr = [b'\x00', b'\x01']
    assert result == expected_byte_arr


def test_call_read_address_variable(address_contract, call):
    result = call(contract=address_contract,
                  contract_function='testAddr')
    assert result == "0xd3CdA913deB6f67967B99D67aCDFa1712C293601"


def test_init_with_ens_name_arg(w3, WithConstructorAddressArgumentsContract, call):
    with contract_ens_addresses(
        WithConstructorAddressArgumentsContract,
        [("arg-name.eth", "0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413")],
    ):
        address_contract = deploy(w3, WithConstructorAddressArgumentsContract, args=[
            "arg-name.eth",
        ])

    result = call(contract=address_contract,
                  contract_function='testAddr')
    assert result == "0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413"


def test_call_read_bytes_variable(bytes_contract, call):
    result = call(contract=bytes_contract, contract_function='constValue')
    assert result == b"\x01\x23"


def test_call_get_bytes_value(bytes_contract, call):
    result = call(contract=bytes_contract, contract_function='getValue')
    assert result == b'\x04\x06'


def test_call_read_bytes32_variable(bytes32_contract, call):
    result = call(contract=bytes32_contract, contract_function='constValue')
    assert result == b"\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23\x01\x23"  # noqa


def test_call_get_bytes32_value(bytes32_contract, call):
    result = call(contract=bytes32_contract, contract_function='getValue')
    assert result == b'\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06\x04\x06'  # noqa


@pytest.mark.parametrize(
    'value, expected',
    [
        (
            '0x' + '11' * 20,
            '0x' + '11' * 20,
        ),
        (
            '0xbb9bc244d798123fde783fcc1c72d3bb8c189413',
            InvalidAddress,
        ),
        (
            '0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413',
            '0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413',
        ),
    ]
)
def test_call_address_reflector_with_address(address_reflector_contract, value, expected, call):
    if not isinstance(expected, str):
        with pytest.raises(expected):
            call(contract=address_reflector_contract,
                 contract_function='reflect',
                 func_args=[value])
    else:
        assert call(contract=address_reflector_contract,
                    contract_function='reflect',
                    func_args=[value]) == expected


@pytest.mark.parametrize(
    'value, expected',
    [
        (
            ['0x' + '11' * 20, '0x' + '22' * 20],
            ['0x' + '11' * 20, '0x' + '22' * 20],
        ),
        (
            ['0x' + '11' * 20, '0x' + 'aa' * 20],
            InvalidAddress
        ),
        (
            [
                '0xFeC2079e80465cc8C687fFF9EE6386ca447aFec4',
                '0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413',
            ],
            [
                '0xFeC2079e80465cc8C687fFF9EE6386ca447aFec4',
                '0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413',
            ],
        ),
    ]
)
def test_call_address_list_reflector_with_address(address_reflector_contract,
                                                  value,
                                                  expected,
                                                  call):
    if not isinstance(expected, list):
        with pytest.raises(expected):
            call(contract=address_reflector_contract,
                 contract_function='reflect',
                 func_args=[value])
    else:
        assert call(contract=address_reflector_contract,
                    contract_function='reflect',
                    func_args=[value]) == expected


def test_call_address_reflector_single_name(address_reflector_contract, call):
    with contract_ens_addresses(
        address_reflector_contract,
        [("dennisthepeasant.eth", "0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413")],
    ):
        result = call(contract=address_reflector_contract,
                      contract_function='reflect',
                      func_args=['dennisthepeasant.eth'])
        assert result == '0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413'


def test_call_address_reflector_name_array(address_reflector_contract, call):
    names = [
        'autonomouscollective.eth',
        'wedonthavealord.eth',
    ]
    addresses = [
        '0xBB9bc244D798123fDe783fCc1C72d3Bb8C189413',
        '0xFeC2079e80465cc8C687fFF9EE6386ca447aFec4',
    ]

    with contract_ens_addresses(address_reflector_contract, zip(names, addresses)):
        result = call(contract=address_reflector_contract,
                      contract_function='reflect',
                      func_args=[names])

    assert addresses == result


def test_call_reject_invalid_ens_name(address_reflector_contract, call):
    with contract_ens_addresses(address_reflector_contract, []):
        with pytest.raises(ValueError):
            call(contract=address_reflector_contract,
                 contract_function='reflect',
                 func_args=['type0.eth'])


def test_call_missing_function(mismatched_math_contract, call):
    expected_missing_function_error_message = "Could not decode contract function call"
    with pytest.raises(BadFunctionCallOutput) as exception_info:
        call(contract=mismatched_math_contract, contract_function='return13')
    assert expected_missing_function_error_message in str(exception_info.value)


def test_call_undeployed_contract(undeployed_math_contract, call):
    expected_undeployed_call_error_message = "Could not transact with/call contract function"
    with pytest.raises(BadFunctionCallOutput) as exception_info:
        call(contract=undeployed_math_contract, contract_function='return13')
    assert expected_undeployed_call_error_message in str(exception_info.value)


def test_call_fallback_function(fallback_function_contract):
    result = fallback_function_contract.fallback.call()
    assert result == []


@pytest.mark.parametrize('tx_params,contract_name,expected', (
    ({'gas': 210000}, 'no_receive', 'fallback'),
    ({'gas': 210000, 'value': 2}, 'no_receive', ''),
    ({'value': 2, 'gas': 210000, 'data': '0x477a5c98'}, 'no_receive', ''),
    ({'gas': 210000, 'data': '0x477a5c98'}, 'no_receive', 'fallback'),
    ({'data': '0x477a5c98'}, 'receive', 'fallback'),
    ({'value': 2}, 'receive', 'receive'),
))
def test_call_receive_fallback_function(w3,
                                        tx_params,
                                        expected,
                                        call,
                                        receive_function_contract,
                                        no_receive_function_contract,
                                        contract_name):
    if contract_name == 'receive':
        contract = receive_function_contract
    elif contract_name == 'no_receive':
        contract = no_receive_function_contract
    else:
        raise AssertionError('contract must be either receive or no_receive')

    initial_value = call(contract=contract, contract_function='getText')
    assert initial_value == ''
    to = {'to': contract.address}
    merged = {**to, **tx_params}
    w3.eth.send_transaction(merged)
    final_value = call(contract=contract, contract_function='getText')
    assert final_value == expected


def test_call_nonexistent_receive_function(fallback_function_contract):
    with pytest.raises(FallbackNotFound, match='No receive function was found'):
        fallback_function_contract.receive.call()


def test_throws_error_if_block_out_of_range(w3, math_contract):
    w3.provider.make_request(method='evm_mine', params=[20])
    with pytest.raises(BlockNumberOutofRange):
        math_contract.functions.counter().call(block_identifier=-50)


def test_accepts_latest_block(w3, math_contract):
    w3.provider.make_request(method='evm_mine', params=[5])
    math_contract.functions.increment().transact()

    late = math_contract.functions.counter().call(block_identifier='latest')
    pend = math_contract.functions.counter().call(block_identifier='pending')

    assert late == 1
    assert pend == 1


def test_accepts_block_hash_as_identifier(w3, math_contract):
    blocks = w3.provider.make_request(method='evm_mine', params=[5])
    math_contract.functions.increment().transact()
    more_blocks = w3.provider.make_request(method='evm_mine', params=[5])

    old = math_contract.functions.counter().call(block_identifier=blocks['result'][2])
    new = math_contract.functions.counter().call(block_identifier=more_blocks['result'][2])

    assert old == 0
    assert new == 1


def test_neg_block_indexes_from_the_end(w3, math_contract):
    w3.provider.make_request(method='evm_mine', params=[5])
    math_contract.functions.increment().transact()
    math_contract.functions.increment().transact()
    w3.provider.make_request(method='evm_mine', params=[5])

    output1 = math_contract.functions.counter().call(block_identifier=-7)
    output2 = math_contract.functions.counter().call(block_identifier=-6)

    assert output1 == 1
    assert output2 == 2


def test_returns_data_from_specified_block(w3, math_contract):
    start_num = w3.eth.get_block('latest').number
    w3.provider.make_request(method='evm_mine', params=[5])
    math_contract.functions.increment().transact()
    math_contract.functions.increment().transact()

    output1 = math_contract.functions.counter().call(block_identifier=start_num + 6)
    output2 = math_contract.functions.counter().call(block_identifier=start_num + 7)

    assert output1 == 1
    assert output2 == 2


message_regex = (
    r"\nCould not identify the intended function with name `.*`, "
    r"positional argument\(s\) of type `.*` and "
    r"keyword argument\(s\) of type `.*`."
    r"\nFound .* function\(s\) with the name `.*`: .*"
)
diagnosis_arg_regex = (
    r"\nFunction invocation failed due to improper number of arguments."
)
diagnosis_encoding_regex = (
    r"\nFunction invocation failed due to no matching argument types."
)
diagnosis_ambiguous_encoding = (
    r"\nAmbiguous argument encoding. "
    r"Provided arguments can be encoded to multiple functions matching this call."
)


def test_no_functions_match_identifier(arrays_contract):
    with pytest.raises(MismatchedABI):
        arrays_contract.functions.thisFunctionDoesNotExist().call()


def test_function_1_match_identifier_wrong_number_of_args(arrays_contract):
    regex = message_regex + diagnosis_arg_regex
    with pytest.raises(ValidationError, match=regex):
        arrays_contract.functions.setBytes32Value().call()


def test_function_1_match_identifier_wrong_args_encoding(arrays_contract):
    regex = message_regex + diagnosis_encoding_regex
    with pytest.raises(ValidationError, match=regex):
        arrays_contract.functions.setBytes32Value('dog').call()


def test_function_multiple_match_identifiers_no_correct_number_of_args(w3):
    MULTIPLE_FUNCTIONS = json.loads('[{"constant":false,"inputs":[],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"bytes32"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"uint256"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"uint8"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"int8"}],"name":"a","outputs":[],"type":"function"}]')  # noqa: E501
    Contract = w3.eth.contract(abi=MULTIPLE_FUNCTIONS)
    regex = message_regex + diagnosis_arg_regex
    with pytest.raises(ValidationError, match=regex):
        Contract.functions.a(100, 'dog').call()


def test_function_multiple_match_identifiers_no_correct_encoding_of_args(w3):
    MULTIPLE_FUNCTIONS = json.loads('[{"constant":false,"inputs":[],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"bytes32"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"uint256"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"uint8"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"int8"}],"name":"a","outputs":[],"type":"function"}]')  # noqa: E501
    Contract = w3.eth.contract(abi=MULTIPLE_FUNCTIONS)
    regex = message_regex + diagnosis_encoding_regex
    with pytest.raises(ValidationError, match=regex):
        Contract.functions.a('dog').call()


def test_function_multiple_possible_encodings(w3):
    MULTIPLE_FUNCTIONS = json.loads('[{"constant":false,"inputs":[],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"bytes32"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"uint256"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"uint8"}],"name":"a","outputs":[],"type":"function"},{"constant":false,"inputs":[{"name":"","type":"int8"}],"name":"a","outputs":[],"type":"function"}]')  # noqa: E501
    Contract = w3.eth.contract(abi=MULTIPLE_FUNCTIONS)
    regex = message_regex + diagnosis_ambiguous_encoding
    with pytest.raises(ValidationError, match=regex):
        Contract.functions.a(100).call()


def test_function_no_abi(w3):
    contract = w3.eth.contract()
    with pytest.raises(NoABIFound):
        contract.functions.thisFunctionDoesNotExist().call()


def test_call_abi_no_functions(w3):
    contract = w3.eth.contract(abi=[])
    with pytest.raises(NoABIFunctionsFound):
        contract.functions.thisFunctionDoesNotExist().call()


def test_call_not_sending_ether_to_nonpayable_function(payable_tester_contract, call):
    result = call(contract=payable_tester_contract,
                  contract_function='doNoValueCall')
    assert result == []


def test_call_sending_ether_to_nonpayable_function(payable_tester_contract, call):
    with pytest.raises(ValidationError):
        call(contract=payable_tester_contract,
             contract_function='doNoValueCall',
             tx_params={'value': 1})


@pytest.mark.parametrize(
    'function, value',
    (
        # minimum positive unambiguous value (larger than fixed8x1)
        ('reflect', Decimal('12.8')),
        # maximum value (for ufixed256x1)
        ('reflect', Decimal(2 ** 256 - 1) / 10),
        # maximum negative unambiguous value (less than 0 from ufixed*)
        ('reflect', Decimal('-0.1')),
        # minimum value (for fixed8x1)
        ('reflect', Decimal('-12.8')),
        # only ufixed256x80 type supports 2-80 decimals
        ('reflect', Decimal(2 ** 256 - 1) / 10 ** 80),  # maximum allowed value
        ('reflect', Decimal(1) / 10 ** 80),  # smallest non-zero value
        # minimum value (for ufixed8x1)
        ('reflect_short_u', 0),
        # maximum value (for ufixed8x1)
        ('reflect_short_u', Decimal('25.5')),
    ),
)
def test_reflect_fixed_value(fixed_reflection_contract, function, value):
    contract_func = fixed_reflection_contract.functions[function]
    reflected = contract_func(value).call({'gas': 420000})
    assert reflected == value


DEFAULT_DECIMALS = getcontext().prec


@pytest.mark.parametrize(
    'function, value, error',
    (
        # out of range
        ('reflect_short_u', Decimal('25.6'), "no matching argument types"),
        ('reflect_short_u', Decimal('-.1'), "no matching argument types"),
        # too many digits for *x1, too large for 256x80
        ('reflect', Decimal('0.01'), "no matching argument types"),

        # too many digits
        ('reflect_short_u', Decimal('0.01'), "no matching argument types"),
        (
            'reflect_short_u',
            Decimal('1e-%d' % (DEFAULT_DECIMALS + 1)),
            "no matching argument types",
        ),
        ('reflect_short_u', Decimal('25.4' + '9' * DEFAULT_DECIMALS), "no matching argument types"),
        ('reflect', Decimal(1) / 10 ** 81, "no matching argument types"),

        # floats not accepted, for floating point error concerns
        ('reflect_short_u', 0.1, "no matching argument types"),

        # ambiguous
        ('reflect', Decimal('12.7'), "Ambiguous argument encoding"),
        ('reflect', Decimal(0), "Ambiguous argument encoding"),
        ('reflect', 0, "Ambiguous argument encoding"),
    ),
)
def test_invalid_fixed_value_reflections(fixed_reflection_contract, function, value, error):
    contract_func = fixed_reflection_contract.functions[function]
    with pytest.raises(ValidationError, match=error):
        contract_func(value).call({'gas': 420000})


@pytest.mark.parametrize(
    'method_input, expected',
    (
        (
            {'a': 123, 'b': [1, 2], 'c': [
                {'x': 234, 'y': [True, False], 'z': [
                    '0x4AD7E79d88650B01EEA2B1f069f01EE9db343d5c',
                    '0xfdF1946A9b40245224488F1a36f4A9ed4844a523',
                    '0xfdF1946A9b40245224488F1a36f4A9ed4844a523',
                ]},
                {'x': 345, 'y': [False, False], 'z': [
                    '0xefd1FF70c185A1C0b125939815225199079096Ee',
                    '0xf35C0784794F3Cd935F5754d3a0EbcE95bEf851e',
                ]},
            ]},
            (123, [1, 2], [
                (234, [True, False], [
                    '0x4AD7E79d88650B01EEA2B1f069f01EE9db343d5c',
                    '0xfdF1946A9b40245224488F1a36f4A9ed4844a523',
                    '0xfdF1946A9b40245224488F1a36f4A9ed4844a523',
                ]),
                (345, [False, False], [
                    '0xefd1FF70c185A1C0b125939815225199079096Ee',
                    '0xf35C0784794F3Cd935F5754d3a0EbcE95bEf851e',
                ]),
            ]),
        ),
        (
            (123, [1, 2], [
                (234, [True, False], [
                    '0x4AD7E79d88650B01EEA2B1f069f01EE9db343d5c',
                    '0xfdF1946A9b40245224488F1a36f4A9ed4844a523',
                    '0xfdF1946A9b40245224488F1a36f4A9ed4844a523',
                ]),
                (345, [False, False], [
                    '0xefd1FF70c185A1C0b125939815225199079096Ee',
                    '0xf35C0784794F3Cd935F5754d3a0EbcE95bEf851e',
                ]),
            ]),
            (123, [1, 2], [
                (234, [True, False], [
                    '0x4AD7E79d88650B01EEA2B1f069f01EE9db343d5c',
                    '0xfdF1946A9b40245224488F1a36f4A9ed4844a523',
                    '0xfdF1946A9b40245224488F1a36f4A9ed4844a523',
                ]),
                (345, [False, False], [
                    '0xefd1FF70c185A1C0b125939815225199079096Ee',
                    '0xf35C0784794F3Cd935F5754d3a0EbcE95bEf851e',
                ]),
            ]),
        ),
    ),
)
def test_call_tuple_contract(tuple_contract, method_input, expected):
    result = tuple_contract.functions.method(method_input).call()
    assert result == expected


@pytest.mark.parametrize(
    'method_input, expected',
    (
        (
            {'t': [
                {'u': [
                    {'x': 1, 'y': 2},
                    {'x': 3, 'y': 4},
                    {'x': 5, 'y': 6},
                ]},
                {'u': [
                    {'x': 7, 'y': 8},
                    {'x': 9, 'y': 10},
                    {'x': 11, 'y': 12},
                ]},
            ]},
            (
                [
                    ([
                        (1, 2),
                        (3, 4),
                        (5, 6),
                    ],),
                    ([
                        (7, 8),
                        (9, 10),
                        (11, 12),
                    ],),
                ],
            ),
        ),
        (
            (
                [
                    ([
                        (1, 2),
                        (3, 4),
                        (5, 6),
                    ],),
                    ([
                        (7, 8),
                        (9, 10),
                        (11, 12),
                    ],),
                ],
            ),
            (
                [
                    ([
                        (1, 2),
                        (3, 4),
                        (5, 6),
                    ],),
                    ([
                        (7, 8),
                        (9, 10),
                        (11, 12),
                    ],),
                ],
            ),
        ),
    ),
)
def test_call_nested_tuple_contract(nested_tuple_contract, method_input, expected):
    result = nested_tuple_contract.functions.method(method_input).call()
    assert result == expected


def test_call_revert_contract(revert_contract):
    with pytest.raises(TransactionFailed, match="Function has been reverted."):
        # eth-tester will do a gas estimation if we don't submit a gas value,
        # which does not contain the revert reason. Avoid that by giving a gas
        # value.
        revert_contract.functions.revertWithMessage().call({'gas': 100000})
