from networkconfgen.constants import CISCO_INTERFACE_PATTERN, JUNIPER_INTERFACE_PATTERN
from networkconfgen import custom_filters


def test_get_interface_components_string():
    # Test split of Cisco Interface Names
    test_strings = {
        "GigabitEthernet0/1/1": ("gi", "0", "1", "1"),
        "TenGigabitEthernet3/2/1": ("te", "3", "2", "1"),
        "FastEthernet0/1": ("fa", "0", "0", "1"),
        "FortyGigabitEthernet1/0/1": ("fo", "1", "0", "1"),
        "Ethernet12/32": ("eth", "0", "12", "32"),
    }

    for key in test_strings.keys():
        assert test_strings[key] == custom_filters.get_interface_components(key, CISCO_INTERFACE_PATTERN)

    # Test split of Juniper Interface Names
    test_strings = {
        "ge-0/1/2": ("ge", "0", "1", "2"),
        "xe-1/2/3": ("xe", "1", "2", "3"),
    }

    for key in test_strings.keys():
        assert test_strings[key] == custom_filters.get_interface_components(key, JUNIPER_INTERFACE_PATTERN)


def test_dotted_decimal():
    test_string = {
        "32": "255.255.255.255",
        "31": "255.255.255.254",
        "30": "255.255.255.252",
        "29": "255.255.255.248",
        "28": "255.255.255.240",
        "27": "255.255.255.224",
        "26": "255.255.255.192",
        "25": "255.255.255.128",
        "24": "255.255.255.0",
        "23": "255.255.254.0",
        "22": "255.255.252.0",
        "21": "255.255.248.0",
        "20": "255.255.240.0",
        "19": "255.255.224.0",
        "18": "255.255.192.0",
        "17": "255.255.128.0",
        "16": "255.255.0.0",
        "0": "0.0.0.0",
        "33": "$$INVALID_VALUE$$(33)",
        "-32": "$$INVALID_VALUE$$(-32)",
        "foobar": "$$INVALID_VALUE$$(foobar)"
    }

    for key in test_string.keys():
        assert test_string[key] == custom_filters.dotted_decimal(key)


def test_wildcard_mask():
    test_string = {
        "32": "0.0.0.0",
        "31": "0.0.0.1",
        "30": "0.0.0.3",
        "29": "0.0.0.7",
        "28": "0.0.0.15",
        "27": "0.0.0.31",
        "26": "0.0.0.63",
        "25": "0.0.0.127",
        "24": "0.0.0.255",
        "23": "0.0.1.255",
        "22": "0.0.3.255",
        "21": "0.0.7.255",
        "20": "0.0.15.255",
        "19": "0.0.31.255",
        "18": "0.0.63.255",
        "17": "0.0.127.255",
        "16": "0.0.255.255",
        "0": "255.255.255.255",
        "33": "$$INVALID_VALUE$$(33)",
        "-32": "$$INVALID_VALUE$$(-32)",
        "foobar": "$$INVALID_VALUE$$(foobar)"
    }

    for key in test_string.keys():
        assert test_string[key] == custom_filters.wildcard_mask(key)


def test_get_valid_vlan_name():
    test_strings = {
        "Test Test": "Test_Test",       # blank is replaced with _
        "foo-bar": "foo_bar",           # - is replaced with _
        "#something": "something",
        "VLAN+Foobar": "VLANFoobar"
    }

    for key in test_strings.keys():
        assert test_strings[key] == custom_filters.valid_vlan_name(key)


def test_convert_interface_name():
    # test cisco to juniper conversion (pass through if nothing useful is identified)
    test_cisco_string = {
        "GigabitEthernet0/1/1": "ge-0/1/0",
        "GigabitEthernet5/11/12": "ge-5/11/11",
        "Ethernet1/1": "ge-0/1/0",
        "FastEthernet0/1/1": "ge-0/1/0",
        "TenGigabitEthernet0/1/1": "xe-0/1/0",
        "FortyGigabitEthernet0/1/1": "et-0/1/0",
        "et-0/1/0": "et-0/1/0",
        "passthrough": "passthrough"
    }

    for e in test_cisco_string.keys():
        assert test_cisco_string[e] == custom_filters.convert_interface_name(e, "juniper_junos")
        assert test_cisco_string[e] == custom_filters.convert_interface_name(e)

    # test juniper to cisco conversion (pass through if nothing useful is identified)
    test_juniper_strings = {
        "ge-0/1/0": "gi0/1/1",
        "xe-1/1/12": "te1/1/13",
        "gi0/1/1": "gi0/1/1",
        "passthrough": "passthrough"
    }

    for e in test_juniper_strings.keys():
        assert test_juniper_strings[e] == custom_filters.convert_interface_name(e, "cisco_ios")


def test_expand_vlan_list():
    # results is always a list containing the expanded VLAN IDs or the error code
    test_data = {
        "1-5": [1, 2, 3, 4, 5],
        "5-100": [e for e in range(5, 101)],
        "1": ['$$INVALID_VLAN_RANGE$$(1)'],
        "123-1": ['$$INVALID_VLAN_RANGE$$(123-1)'],
        "1232-12": ['$$INVALID_VLAN_RANGE$$(1232-12)'],
        "Foo-Bar": ['$$INVALID_VLAN_RANGE$$(Foo-Bar)']
    }

    for e in test_data.keys():
        assert test_data[e] == custom_filters.expand_vlan_list(e)
