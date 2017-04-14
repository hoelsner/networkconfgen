# regular expression to deconstruct interface names
ERROR_UNKNOWN = "$$UNKOWN_ERROR_IN_CUSTOM_FUNCTION$$"
ERROR_INVALID_VLAN_RANGE = "$$INVALID_VLAN_RANGE$$"
ERROR_INVALID_VALUE = "$$INVALID_VALUE$$"
CISCO_INTERFACE_PATTERN = r"^(?P<interface_name>((gi)|(fa)|(te)|(fo)|(eth)){1})" \
                          r"[a-z]*" \
                          r"(((?P<chassis>\d+))/)?" \
                          r"(?P<module>\d+)/" \
                          r"(?P<port>\d+)$"
JUNIPER_INTERFACE_PATTERN = r"^(?P<interface_name>((ge)|(xe)){1})" \
                            r"\-" \
                            r"(?P<chassis>\d+)/" \
                            r"(?P<module>\d+)/" \
                            r"(?P<port>\d+)$"

# operating system identification strings
OS_CISCO_IOS = "cisco_ios"
OS_JUNIPER_JUNOS = "juniper_junos"
