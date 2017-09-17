import logging
import jinja2
import os
import json
from networkconfgen import custom_filters
from networkconfgen.constants import ERROR_UNKNOWN, ERROR_INVALID_VLAN_RANGE, ERROR_INVALID_VALUE, ERROR_CODES

logger = logging.getLogger("networkconfgen")


class NetworkConfGenResult(object):
    """
    Object, that represents the result of the config generator
    """
    template_result = ""
    error_text = None
    search_path = None
    template_file_name = None

    @property
    def render_error(self):
        """
        errors during rendering
        """
        return self.error_text is not None

    @property
    def content_error(self):
        """
        identify errors within render content (known error codes)
        """
        content_has_error = False

        if self.template_result is not None:
            for e in ERROR_CODES["_ERROR_"].keys():
                if ERROR_CODES["_ERROR_"][e] in self.template_result:
                    content_has_error = True
                    break

        else:
            # No content, therefore no error
            return False

        return content_has_error

    @property
    def from_string(self):
        """
        returns true, if the result was generated from string
        """
        return self.template_file_name is None

    def cleaned_template_result(self):
        """
        returns a cleaned template result (trim tabs on the left side, whitespace on the right side and remove
        empty lines)
        """
        if self.template_result is None:
            return None

        result = ""
        lines = self.template_result.split("\n")
        last_line = len(lines)
        counter = 1
        for line in lines:
            if line != "":
                line = line.replace("    ", "\t")
                if counter == last_line:
                    result += line.lstrip("\t").rstrip()

                else:
                    result += line.lstrip("\t").rstrip() + "\n"

            counter += 1

        return result

    def to_json(self):
        return {
            "template_file_name": self.template_file_name,
            "render_error": self.render_error,
            "content_error": self.content_error,
            "from_string": self.from_string,
            "search_path": self.search_path,
            "template_result": self.template_result,
            "error_text": self.error_text
        }

    def __str__(self):
        """
        return string to the template_result or render_error if template_result is none
        """
        if self.template_result:
            return self.template_result

        else:
            return self.error_text

    def __repr__(self):
        return json.dumps(self.to_json(), indent=4, sort_keys=True)


class NetworkConfGen(object):
    """
    Base class for the customized Jinja2 based configuration generator

    The entire overview about the Jinja2 syntax is available at http://jinja.pocoo.org/docs/2.9/templates/
    """
    _template_engine = None
    _searchpath = None

    def __init__(self, searchpath=None,
                 block_start_string="{%",
                 block_end_string="%}",
                 line_statement_prefix=None,
                 comment_start_string="{#",
                 comment_end_string="#}",
                 line_comment_prefix=None,
                 variable_start_string="{{",
                 variable_end_string="}}"):
        self._searchpath = searchpath

        if searchpath is None:
            # if no searchpath is given, use an empty Dict loader
            loader = jinja2.DictLoader({})

        else:
            loader = jinja2.FileSystemLoader(searchpath=searchpath)

        self._template_engine = jinja2.Environment(
            loader=loader,
            lstrip_blocks=True,
            trim_blocks=True,
            block_start_string=block_start_string,
            block_end_string=block_end_string,
            comment_start_string=comment_start_string,
            comment_end_string=comment_end_string,
            line_statement_prefix=line_statement_prefix,
            line_comment_prefix=line_comment_prefix,
            variable_start_string=variable_start_string,
            variable_end_string=variable_end_string
        )

        self._template_engine.filters["clean_string"] = custom_filters.valid_vlan_name  # removes special characters
        self._template_engine.filters["valid_vlan_name"] = custom_filters.valid_vlan_name
        self._template_engine.filters["dotted_decimal"] = custom_filters.dotted_decimal
        self._template_engine.filters["expand_vlan_list"] = custom_filters.expand_vlan_list
        self._template_engine.filters["wildcard_mask"] = custom_filters.wildcard_mask       # aka hostmask
        self._template_engine.filters["convert_interface_name"] = custom_filters.convert_interface_name
        self._template_engine.filters["split_interface"] = custom_filters.split_interface
        self._template_engine.filters["split_interface_cisco_ios"] = custom_filters.split_interface_cisco_ios
        self._template_engine.filters["split_interface_juniper_junos"] = custom_filters.split_interface_juniper_junos
        self._template_engine.add_extension('jinja2.ext.do')

    def _add_error_codes(self, parameter_dictionary):
        if type(parameter_dictionary) is not dict:
            raise AttributeError("parameter_dictionary must be a dict type")

        parameter_dictionary.update(ERROR_CODES)

        return parameter_dictionary

    def render_from_string(self, template_content, parameters):
        """
        render a Jinja2 template from a string using the custom Jinja2 environment

        :param template_content:
        :param parameters: dictionary that contains all parameters
        :return:
        """
        if type(parameters) is not dict:
            raise AttributeError("parameters must be a dictionary")

        if type(template_content) is not str:
            raise AttributeError("file attribute must be a string")

        obj = NetworkConfGenResult()

        try:
            template = self._template_engine.from_string(template_content)
            obj.template_result = template.render(self._add_error_codes(parameters))

        except jinja2.TemplateSyntaxError as ex:
            obj.error_text = "Template Syntax Exception in line '%d' (%s)" % (ex.lineno, ex)
            obj.template_result = None
            logger.error(obj.error_text, exc_info=True)

        except Exception as ex:
            obj.error_text = "Unexpected Exception (%s)" % ex
            obj.template_result = None
            logger.error(obj.error_text, exc_info=True)

        return obj

    def render_from_file(self, file, parameters):
        """
        render a Jinja2 template from a file within the searchpath using the custom Jinja2 environment (required to use
        more advanced template features).

        :param file:
        :param parameters:
        :return:
        """
        if type(parameters) is not dict:
            raise AttributeError("parameters attribute must be a dictionary")

        if type(file) is not str:
            raise AttributeError("file attribute must be a string")

        if not self._searchpath:
            # add a warning message if no search path is set (won't load a FileSystemLoader in Jinja2)
            logger.warning("searchpath attribute not set, don't expect to find anything")

        obj = NetworkConfGenResult()
        obj.search_path = self._searchpath
        obj.template_file_name = file

        try:
            logger.debug("render template from file '%s'" % os.path.abspath(os.path.join(self._searchpath, file)))
            template = self._template_engine.get_template(file)
            obj.template_result = template.render(self._add_error_codes(parameters))

        except jinja2.TemplateNotFound as ex:
            obj.error_text = "Template %s not found" % (ex.name)
            obj.template_result = None
            logger.error(obj.error_text, exc_info=True)

        except jinja2.TemplateSyntaxError as ex:
            obj.error_text = "Template Syntax Exception file '%s', line '%d' (%s)" % (ex.filename, ex.lineno, ex)
            obj.template_result = None
            logger.error(obj.error_text, exc_info=True)

        except Exception as ex:
            obj.error_text = "Unexpected Exception (%s)" % ex
            obj.template_result = None
            logger.error(obj.error_text, exc_info=True)

        return obj
