import json
import re
import os
import jinja2
import pytest
import networkconfgen
from networkconfgen import NetworkConfGen, NetworkConfGenResult


@pytest.fixture
def break_template_environment(monkeypatch):
    """force an unexpected exception when rendering templates"""
    class MockTemplateEnvironment:
        filters = dict()

        def __init__(self, *args, **kwargs):
            pass

        def add_extension(self, name):
            pass

        def from_string(self, name):
            raise Exception("oooops, something unexpected happens...")

        def get_template(self, name):
            raise Exception("oooops, something unexpected happens...")

    monkeypatch.setattr(jinja2, "Environment", MockTemplateEnvironment)


class TestNetworkConfGen:
    """
    Test cases and utility methods to verify the functionality of the NetworkConfGen class
    """
    @staticmethod
    def verify_networkconfgenresult(result, expected_json_result, expected_cleaned_result=None):
        """
        :param result: the NetworkConfGenResult instance
        :param expected_json_result: expected dictionary/JSON representation of the instance (used to verfiy the values)
        :param expected_cleaned_result: expected cleaned result (strip whitespace etc.)
        :return:
        """
        if expected_cleaned_result is None:
            expected_cleaned_result = expected_json_result["template_result"]

        assert type(result) == NetworkConfGenResult
        assert result.template_result == expected_json_result["template_result"]
        assert result.error_text == expected_json_result["error_text"]
        assert result.search_path == expected_json_result["search_path"]
        assert result.template_file_name == expected_json_result["template_file_name"]
        assert result.render_error is expected_json_result["render_error"]
        assert result.content_error is expected_json_result["content_error"]
        assert result.from_string is expected_json_result["from_string"]
        assert result.cleaned_template_result() == expected_cleaned_result
        assert type(result.to_json()) is dict
        assert json.dumps(result.to_json(), sort_keys=True) == json.dumps(expected_json_result, sort_keys=True)
        assert repr(result) == json.dumps(expected_json_result, sort_keys=True, indent=4)

        # if a template result is stored in the class, the result will be the template result, if an error occurred,
        # the result will be the error message
        if result.template_result:
            assert str(result) == expected_json_result["template_result"]

        else:
            assert str(result) == expected_json_result["error_text"]

    def test_valid_render_from_string_with_clean_result(self):
        # verify that tabs are stripped
        confgen = NetworkConfGen()

        template_string = "!\n\thostname {{ hostname }}\n!"
        param = {"hostname": "MyName"}
        expected_clean_result = "!\nhostname MyName\n!"

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        assert result.cleaned_template_result() == expected_clean_result

        # verify that tabs are stripped and less than four blanks still exists (will be replaced with tabs during the
        # cleaning of the result)
        param = {"hostname": "MyName"}
        test_templates = {
            "!\n\t hostname {{ hostname }}\n!": "!\n hostname MyName\n!",
            "!\n\t  hostname {{ hostname }}\n!": "!\n  hostname MyName\n!",
            "!\n\t   hostname {{ hostname }}\n!": "!\n   hostname MyName\n!",
            "!\n    hostname {{ hostname }}\n!": "!\nhostname MyName\n!",
            "!\r\n\t hostname {{ hostname }}\r\n!": "!\n hostname MyName\n!",
            "!\r\n\t  hostname {{ hostname }}\r\n!": "!\n  hostname MyName\n!",
            "!\r\n\t   hostname {{ hostname }}\r\n!": "!\n   hostname MyName\n!",
            "!\r\n\t    hostname {{ hostname }}\r\n!": "!\nhostname MyName\n!",
            "!\n\n\t hostname {{ hostname }}\n\n!": "!\n hostname MyName\n!",
            "!\n\n\t  hostname {{ hostname }}\n\n!": "!\n  hostname MyName\n!",
            "!\n\n\t   hostname {{ hostname }}\n\n!": "!\n   hostname MyName\n!",
            "!\n\n    hostname {{ hostname }}\n\n!": "!\nhostname MyName\n!",
            # remove empty last line
            "!\n\t hostname {{ hostname }}\n!\n": "!\n hostname MyName\n!",
            "\n!\n\t hostname {{ hostname }}\n!": "!\n hostname MyName\n!",
        }

        for template, expected_clean_result in test_templates.items():
            result = confgen.render_from_string(template_content=template,
                                                parameters=param)
            assert result.cleaned_template_result() == expected_clean_result

    def test_valid_render_from_string(self):
        confgen = NetworkConfGen()

        template_string = "!\nhostname {{ hostname }}\n!"
        param = {"hostname": "MyName"}
        expected_result = "!\nhostname MyName\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_invalid_parameters_for_render_from_string(self):
        confgen = NetworkConfGen()

        template_string = "!\nhostname {{ hostname }}\n!"
        param = {"hostname": "MyName"}

        with pytest.raises(AttributeError):
            confgen.render_from_string(template_content=template_string, parameters="FooBar")

        with pytest.raises(AttributeError):
            confgen.render_from_string(template_content=["template1", "template2"], parameters=param)

    def test_syntax_exception_render_from_string(self):
        confgen = NetworkConfGen()

        template_string = "!\nhostname {% if hostname %}{{ hostname }}\n!"
        param = {"hostname": "MyName"}
        expected_json_result = {
            "template_file_name": None,
            "render_error": True,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": None,
            "error_text": "Template Syntax Exception in line '2' "
                          "(Unexpected end of template. Jinja was looking for the "
                          "following tags: 'elif' or 'else' or 'endif'. The innermost block that needs to be "
                          "closed is 'if'.)"
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    @pytest.mark.usefixtures("break_template_environment")
    def test_unexpected_exception_render_from_string(self):
        confgen = NetworkConfGen()

        template_string = "!\nhostname {% if hostname %}{{ hostname }}\n!"
        param = {"hostname": "MyName"}
        expected_json_result = {
            "template_file_name": None,
            "render_error": True,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": None,
            "error_text": "Unexpected Exception (oooops, something unexpected happens...)"
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_jinja_trim_blocks(self):
        confgen = NetworkConfGen()
        param = {"values": [1, 2, 3, 4, 5]}

        template_string = """\
!
{% for e in values %}
!
value {{ e }}
{% endfor %}
!"""
        expected_result = "!\n!\nvalue 1\n!\nvalue 2\n!\nvalue 3\n!\nvalue 4\n!\nvalue 5\n!"

        result = confgen.render_from_string(template_content=template_string, parameters=param)

        assert result.template_result == expected_result
        assert result.cleaned_template_result() == expected_result

        template_string = """\
!
{% for e in values %}!
value {{ e }}
{% endfor %}
!"""
        expected_result = "!\n!\nvalue 1\n!\nvalue 2\n!\nvalue 3\n!\nvalue 4\n!\nvalue 5\n!"

        result = confgen.render_from_string(template_content=template_string, parameters=param)

        assert result.template_result == expected_result
        assert result.cleaned_template_result() == expected_result

    def test_jinja_lstrip_blocks(self):
        confgen = NetworkConfGen()

        template_string = {
            "  {% for e in values %}{{ e }}{% endfor %}": "12345",
            "  {% for e in values %} {{ e }}{% endfor %}": " 1 2 3 4 5",
            "  {% for e in values %}{{ e }} {% endfor %}": "1 2 3 4 5 ",
            "{% for e in values %}{{ e }} {% endfor %}": "1 2 3 4 5 ",
        }
        param = {"values": [1, 2, 3, 4, 5]}

        for template, expected_result in template_string.items():
            result = confgen.render_from_string(template_content=template,
                                                parameters=param)

            assert result.template_result == expected_result

    def test_content_error_invalid_value(self):
        """the content_error checks for various error codes that are defined within the custom functions."""
        confgen = NetworkConfGen()

        template_string = "!\nnetmask {{ mask|dotted_decimal }}\n!"
        param = {"mask": "54"}
        expected_result = "!\nnetmask $$INVALID_VALUE$$(54)\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": True,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_content_error_invalid_vlan_range(self):
        confgen = NetworkConfGen()

        template_string = "!\nnetmask {{ vlan_range|expand_vlan_list|join }}\n!"
        param = {"vlan_range": "123-21"}
        expected_result = "!\nnetmask $$INVALID_VLAN_RANGE$$(123-21)\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": True,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_content_error_unknown(self, monkeypatch):
        def re_match_mock(*args, **kwargs):
            raise Exception("Unexpected exception")

        monkeypatch.setattr(re, "match", re_match_mock)
        confgen = NetworkConfGen()

        template_string = "!\nnetmask {{ vlan_range|convert_interface_name }}\n!"
        param = {"vlan_range": "123-21"}
        expected_result = "!\nnetmask $$UNKOWN_ERROR_IN_CUSTOM_FUNCTION$$\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": True,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_valid_render_from_file(self):
        """test rendering from a file (allows the use of more
        advanced features of Jinja2, e.g. inheritance (http://jinja.pocoo.org/docs/2.9/templates/#template-inheritance))
        """
        confgen = NetworkConfGen(searchpath=os.path.join("tests", "data"))

        param = {"hostname": "MyName"}
        expected_result = "!\nhostname MyName\n!"
        expected_json_result = {
            "template_file_name": "valid_syntax.txt",
            "render_error": False,
            "content_error": False,
            "from_string": False,
            "search_path": os.path.join("tests", "data"),
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_file(file=expected_json_result["template_file_name"], parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_syntax_exception_render_from_file(self):
        confgen = NetworkConfGen(searchpath=os.path.join("tests", "data"))

        param = {"hostname": "MyName"}
        expected_json_result = {
            "template_file_name": "invalid_syntax.txt",
            "render_error": True,
            "content_error": False,
            "from_string": False,
            "search_path": os.path.join("tests", "data"),
            "template_result": None,
            "error_text": "Template Syntax Exception file 'tests/data/invalid_syntax.txt', line '2' (Expected an "
                          "expression, got 'end of statement block')"
        }

        result = confgen.render_from_file(file=expected_json_result["template_file_name"], parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_template_not_found_exception_render_from_file(self):
        confgen = NetworkConfGen(searchpath=os.path.join("tests", "data"))

        param = {"hostname": "MyName"}
        expected_json_result = {
            "template_file_name": "not_existing.txt",
            "render_error": True,
            "content_error": False,
            "from_string": False,
            "search_path": os.path.join("tests", "data"),
            "template_result": None,
            "error_text": "Template not_existing.txt not found"
        }

        result = confgen.render_from_file(file=expected_json_result["template_file_name"], parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_invalid_parameters_for_render_from_file(self):
        confgen = NetworkConfGen()
        param = {"hostname": "MyName"}

        with pytest.raises(AttributeError):
            confgen.render_from_file(file="valid_template.txt", parameters="FooBar")

        with pytest.raises(AttributeError):
            confgen.render_from_file(file=["template1", "template2"], parameters=param)

    @pytest.mark.usefixtures("break_template_environment")
    def test_unexpected_exception_render_from_file(self):
        confgen = NetworkConfGen(searchpath=os.path.join("tests", "data"))

        param = {"hostname": "MyName"}
        expected_json_result = {
            "template_file_name": "not_existing.txt",
            "render_error": True,
            "content_error": False,
            "from_string": False,
            "search_path": os.path.join("tests", "data"),
            "template_result": None,
            "error_text": "Unexpected Exception (oooops, something unexpected happens...)"
        }

        result = confgen.render_from_file(file=expected_json_result["template_file_name"], parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_custom_function_clean_string(self):
        confgen = NetworkConfGen()

        template_string = "!\n{{ var1|clean_string }}\n{{ var2|clean_string }}\n{{ var3|clean_string }}\n" \
                          "{{ var4|clean_string }}\n!"
        param = {
            "var1": "My-Valid-String",
            "var2": "My%Valid String",
            "var3": "My%Valid?String;",
            "var4": "My(Valid]String;",
        }
        expected_result = "!\nMy_Valid_String\nMyValid_String\nMyValidString\nMyValidString\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_custom_function_get_valid_vlan_name(self):
        confgen = NetworkConfGen()

        template_string = "!\n{{ var1|valid_vlan_name }}\n{{ var2|valid_vlan_name }}\n" \
                          "{{ var3|valid_vlan_name }}\n{{ var4|valid_vlan_name }}\n!"
        param = {
            "var1": "My-Valid-VLANName",
            "var2": "My%Valid VLANName",
            "var3": "My%Valid?VLANName;",
            "var4": "My(Valid]VLANName;",
        }
        expected_result = "!\nMy_Valid_VLANName\nMyValid_VLANName\nMyValidVLANName\nMyValidVLANName\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_custom_function_dotted_decimal(self):
        confgen = NetworkConfGen()

        template_string = "!\n{{ var1|dotted_decimal }}\n{{ var2|dotted_decimal }}\n" \
                          "{{ var3|dotted_decimal }}\n{{ var4|dotted_decimal }}\n!"
        param = {
            "var1": "32",
            "var2": 32,
            "var3": "24",
            "var4": "26",
        }
        expected_result = "!\n255.255.255.255\n255.255.255.255\n255.255.255.0\n255.255.255.192\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

        template_string = "!\n{{ var1|dotted_decimal }}\n{{ var2|dotted_decimal }}\n!"
        param = {
            "var1": "33",
            "var2": "-1",
        }
        expected_result = "!\n%s(33)\n%s(-1)\n!" % (
            networkconfgen.constants.ERROR_INVALID_VALUE,
            networkconfgen.constants.ERROR_INVALID_VALUE
        )
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": True,  # invalid value will result in an content_error
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_custom_function_expand_vlan_list(self):
        confgen = NetworkConfGen()

        template_string = """\
!
{% for vlan in var1|expand_vlan_list %}
vlan {{ vlan }}
{% endfor %}
{% for vlan in var2|expand_vlan_list %}
vlan {{ vlan }}
{% endfor %}
!
"""
        param = {
            "var1": "10-15",
            "var2": "1000-1005",
        }
        expected_result = "!\nvlan 10\nvlan 11\nvlan 12\nvlan 13\nvlan 14\nvlan 15\n" \
                          "vlan 1000\nvlan 1001\nvlan 1002\nvlan 1003\nvlan 1004\nvlan 1005\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

        param = {
            "var1": "33",
            "var2": "10-FooBar",
        }
        expected_result = "!\nvlan %s(33)\nvlan %s(10-FooBar)\n!" % (
            networkconfgen.constants.ERROR_INVALID_VLAN_RANGE,
            networkconfgen.constants.ERROR_INVALID_VLAN_RANGE
        )
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": True,  # invalid value will result in an content_error
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_custom_function_wildcard_mask(self):
        confgen = NetworkConfGen()

        template_string = "!\n{{ var1|wildcard_mask }}\n{{ var2|wildcard_mask }}\n" \
                          "{{ var3|wildcard_mask }}\n{{ var4|wildcard_mask }}\n!"
        param = {
            "var1": "32",
            "var2": 32,
            "var3": "24",
            "var4": "26",
        }
        expected_result = "!\n0.0.0.0\n0.0.0.0\n0.0.0.255\n0.0.0.63\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

        template_string = "!\n{{ var1|wildcard_mask }}\n{{ var2|wildcard_mask }}\n!"
        param = {
            "var1": "33",
            "var2": "-1",
        }
        expected_result = "!\n%s(33)\n%s(-1)\n!" % (
            networkconfgen.constants.ERROR_INVALID_VALUE,
            networkconfgen.constants.ERROR_INVALID_VALUE
        )
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": True,  # invalid value will result in an content_error
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_custom_function_convert_interface_name(self):
        confgen = NetworkConfGen()

        template_string = "!\n{{ var1|convert_interface_name('%s') }}\n{{ var2|convert_interface_name('%s') }}\n" \
                          "{{ var3|convert_interface_name('%s') }}\n{{ var4|convert_interface_name('%s') }}\n!" % (
                              networkconfgen.constants.OS_JUNIPER_JUNOS,
                              networkconfgen.constants.OS_JUNIPER_JUNOS,
                              networkconfgen.constants.OS_CISCO_IOS,
                              networkconfgen.constants.OS_CISCO_IOS
                          )
        param = {
            "var1": "GigabitEthernet1/0/1",
            "var2": "FooBar",       # value won't change, no error is thrown in this case to maintain stability
            "var3": "xe-0/1/1",
            "var4": "FooBar",       # value won't change, no error is thrown in this case to maintain stability
        }
        expected_result = "!\nge-1/0/0\nFooBar\nte0/1/2\nFooBar\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=param)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)

    def test_jinja_extension_do_expression(self):
        """
        The do expression allows the manipulation of lists within the templates.
        """
        confgen = NetworkConfGen()

        template_string = "!\n{% do val.append('Bar') %}{{ val|join }}\n!"
        params = {
            "val": ["Foo"]
        }
        expected_result = "!\nFooBar\n!"
        expected_json_result = {
            "template_file_name": None,
            "render_error": False,
            "content_error": False,
            "from_string": True,
            "search_path": None,
            "template_result": expected_result,
            "error_text": None
        }

        result = confgen.render_from_string(template_content=template_string,
                                            parameters=params)

        self.verify_networkconfgenresult(result=result, expected_json_result=expected_json_result)
