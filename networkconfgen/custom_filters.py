"""
Any custom filter that is bound to the Jinja2 Template Engine used in the NetworkConfGen class
"""
import logging
import re
from ipaddress import IPv4Network
from networkconfgen.constants import ERROR_UNKNOWN, ERROR_INVALID_VLAN_RANGE, ERROR_INVALID_VALUE, \
    CISCO_INTERFACE_PATTERN, JUNIPER_INTERFACE_PATTERN, OS_CISCO_IOS, OS_JUNIPER_JUNOS, ERROR_PARAMETER, \
    ERROR_REGEX, ERROR_NO_MATCH

logger = logging.getLogger("networkconfgen")


def get_interface_components(interface_string, regex_to_use=CISCO_INTERFACE_PATTERN):
    """
    split the given string to the interface_name, chassis, module and port (consider experimental)

    :param interface_string:
    :param regex_to_use: regular expression, that defines four named parameters interface_name, chassis, module and port
    :return: tuple with the interface_name (lowered), the chassis number (default to 0 if not found), the module and port
    """
    pattern = re.compile(regex_to_use)
    param = pattern.match(interface_string.lower())

    interface_name = param.group("interface_name").lower()
    if not param.group("chassis"):
        chassis = 0
    else:
        chassis = param.group("chassis")

    module = param.group("module")
    port = int(param.group("port"))

    return interface_name, str(chassis), str(module), str(port)


def dotted_decimal(prefix_length):
    """
    converts the given prefix length to a dotted decimal representation

    :param prefix_length:
    :return:
    """
    try:
        ip = IPv4Network("0.0.0.0/" + str(prefix_length))
        return str(ip.netmask)

    except Exception:
        return "%s(%s)" % (ERROR_INVALID_VALUE, prefix_length)


def wildcard_mask(prefix_length):
    """
    converts the given prefix length to a dotted decimal hostmask (e.g. for ACLs)

    :param prefix_length:
    :return:
    """
    try:
        ip = IPv4Network("0.0.0.0/" + str(prefix_length))
        return str(ip.hostmask)

    except Exception:
        return "%s(%s)" % (ERROR_INVALID_VALUE, prefix_length)


def valid_vlan_name(vlan_name):
    """
    create a valid VLAN name (removed certain unwanted charaters)

    :param vlan_name:
    :return:
    """
    invalid_chars = list(";,.#+*=?%$()[]")

    clean_string = vlan_name.replace(" ", "_")
    clean_string = clean_string.replace("-", "_")
    clean_string = "".join(e for e in clean_string if e not in invalid_chars)

    return clean_string


def convert_interface_name(interface_name, target_vendor=None):
    """
    used to convert an vendor specific interface name to another interface name of a different vendor

    :param interface_name: interface string, that should be converted
    :param target_vendor: target Vendor string ('cisco_ios' or 'juniper_junos')
    """
    if target_vendor is None:
        target_vendor = OS_JUNIPER_JUNOS

    translation_map = {
        # from => to => interface name (lowercase)
        OS_CISCO_IOS: {
            OS_JUNIPER_JUNOS: {
                "eth": "ge",
                "fa": "ge",
                "gi": "ge",
                "te": "xe",
                "fo": "et",
            },
        },
        OS_JUNIPER_JUNOS: {
            OS_CISCO_IOS: {
                "ge": "gi",
                "xe": "te",
            },
        }
    }

    try:
        result = None
        if re.match(CISCO_INTERFACE_PATTERN, interface_name, re.IGNORECASE):
            if OS_CISCO_IOS not in target_vendor:  # don't modify if the target vendor is the same
                # cisco interface detected
                logger.debug("Cisco interface string '%s' detected by convert_interface_name" % interface_name)

                if OS_JUNIPER_JUNOS in target_vendor.lower():
                    # juniper port numbering starts with 0
                    intf, chassis, module, port = get_interface_components(interface_name, CISCO_INTERFACE_PATTERN)
                    result = "%s-%s/%s/%s" % (translation_map[OS_CISCO_IOS][OS_JUNIPER_JUNOS][intf],
                                              chassis, module, str(int(port) - 1))

        elif re.match(JUNIPER_INTERFACE_PATTERN, interface_name, re.IGNORECASE):
            if OS_JUNIPER_JUNOS not in target_vendor:  # don't modify if the target vendor is the same
                # juniper interface detected
                logger.debug("Juniper interface string '%s' detected by convert_interface_name" % interface_name)

                if OS_CISCO_IOS in target_vendor.lower():
                    intf, chassis, module, port = get_interface_components(interface_name, JUNIPER_INTERFACE_PATTERN)
                    result = "%s%s/%s/%s" % (translation_map[OS_JUNIPER_JUNOS][OS_CISCO_IOS][intf],
                                             chassis, module, str(int(port) + 1))

        if result:
            return result

        else:
            return interface_name

    except Exception as ex:
        msg = "Exception while translating interface name '%s' to '%s' (%s)" % (interface_name, target_vendor, str(ex))

        logger.error(msg)
        logger.debug(msg, exc_info=True)
        return ERROR_UNKNOWN


def expand_vlan_list(vlan_list):
    """
    converts a range statement to a list (or a list with an error message if the parameter is not valid) - no
    verification of the VLAN ID range (1-4094)

    :param vlan_list: string in the format `(\d+-\d+)`
    :return: list entry with the result
    """
    result = []
    list_regex = "(\d+-\d+)"
    re_result = re.match(list_regex, vlan_list)

    if re_result is None:
        # if the list is invalid, return a list with a single error entry
        result.append("%s(%s)" % (ERROR_INVALID_VLAN_RANGE, vlan_list))

    else:
        # extract values and check range
        elements = vlan_list.split("-")
        val_a = int(elements[0])
        val_b = int(elements[1])
        if val_a >= val_b:
            result.append("%s(%s)" % (ERROR_INVALID_VLAN_RANGE, vlan_list))

        else:
            # valid parameter, create vlan list
            result.extend(list(range(val_a, val_b + 1)))

    return result


def split_interface(interface_regex, value):
    """
    convert an interface based on the given regular expression to a dictionary with all components, e.g.

        regex: .*(?P<chassis>\d+)\/(?P<module>\d+)\/(?P<port>\d+).*
        value: interface gi1/2/3

    will return

        {
            "chassis": 1,
            "module": 2,
            "port": 3
        }

    or in case of an error to

        {
            "error": "message"
        }

    :param interface_regex: valid regular expression 
    :param value: value that should be parsed
    :return: dictionary with three possible 
    """
    if type(interface_regex) is not str:
        return {"error": "%s(%s)" % (ERROR_PARAMETER, "invalid type for 'interface_regex'")}

    if type(value) is not str:
        return {"error": "%s(%s)" % (ERROR_PARAMETER, "invalid type for 'value'")}

    try:
        pattern = re.compile(interface_regex, re.IGNORECASE)

    except Exception as ex:
        return {"error": "%s(%s)" % (ERROR_REGEX, str(ex))}

    match = pattern.match(value)

    if match:
        # check groups 'chassis', 'module'and 'port'
        # if empty, a None value is used
        result = match.groupdict()
        valid_groups = ["chassis", "module", "port"]

        # add None values if certain groups does not exist
        for key in valid_groups:
            result[key] = None if key not in result.keys() else result[key]

        # delete other keys
        keys_to_delete = []
        for key in result.keys():
            if key not in valid_groups:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del result[key]

    else:
        # no match, return error message
        result = {"error": "%s(pattern '%s' for '%s')" % (ERROR_NO_MATCH, interface_regex, value)}

    return result


def split_interface_cisco_ios(value):
    return split_interface(".*%s.*" % CISCO_INTERFACE_PATTERN, value)


def split_interface_juniper_junos(value):
    return split_interface(".*%s.*" % JUNIPER_INTERFACE_PATTERN, value)
