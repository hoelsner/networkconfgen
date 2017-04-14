NetworkConfGen
==============

[Jinja2](http://jinja.pocoo.org/docs/2.9/) based configuration generator with some extensions required to generate configurations for 
network devices. It's build on top of the Jinja2 template engine. 

The following python versions are supported:

  * python 2.7 (requires `py2-ipaddress` backport)
  * python 3.4
  * python 3.5
  * python 3.6

## Setup and Installation

You can install it via pip:

```
pip install networkconfgen 
```

## Quickstart

Before you begin, I assume that you are already familiar with the Jinja2 Template syntax. If not, please take a look at the 
[Jinja2 Template Designer Documentation](http://jinja.pocoo.org/docs/2.9/templates/).

The following custom filters are added to the standard Jinja2 template syntax:

  * filter to **convert strings to VLAN names** (e.g. `{{ "Data Network"|valid_vlan_name }}` will render to `Data_Network`) 
  * filter to convert an integer (0-32) 
    * to a dotted decimal **network mask** (e.g. `{{ "24"|dotted_decimal }}` will render to `255.255.255.0`)
    * to a dotted decimal **hostmask/wildcard mask** (e.g. `{{ "24"|wildcard_mask }}` will render to `0.0.0.255`)  
  * filter to **convert a given VLAN range to a list** with individual values (e.g. `{{ "2-4"|wildcard_expand_vlan_list }}` will render to `[2, 3, 4]`)
  * an experimental filter to convert interface names between vendors (e.g. `{{ "Gi0/0/1"|convert_interface_name("juniper_junos") }}` will render to `ge-0/0/0`)

The following jinja2 extension are enabled by default: 

  * Jinja2 Expression Statement (`do`) extension, see [the Jinja 2 docmentation for details](http://jinja.pocoo.org/docs/2.9/extensions/#expression-statement) 

The following example script shows, how to render jinja2 templates from strings:
 
```python
from networkconfgen import NetworkConfGen


if __name__ == "__main__":
    confgen = NetworkConfGen()
    template = "My {{ awesome }} template"
    parameters = {
        "awesome": "great"
    }
    
    # returns a NetworkConfGenResult instance
    result = confgen.render_from_string(template_content=template, parameters=parameters)
    
    # verify that the rendering was successful
    if not result.render_error:
        # raw output from jinja2
        print(result.template_result)
        # cleaned result (strip whitespace and 4 consecutive blanks)
        print(result.cleaned_template_result())
       
    else: 
        print("Something went wrong: %s" % result.error_text)
```

The result of the `render_from_string` (and `render_from_file`) functions is an instance of the class `NetworkConfGenResult` with 
the following attributes and methods:

| attribute/method             | description                                                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `template_result`            | The result of the template rendering process (if no error during rendering occurred)                               |
| `render_error`               | `True` if an error during rendering occurred (e.g. Syntax Errors)                                                  |
| `content_error`              | `True` if one of the custom filters produces an invalid result, indicate that the result may not be trustworthy    |
| `from_string`                | `True` if the template was rendered from a string value, otherwise `False`                                         |
| `error_text`                 | contains the error message if a rendering error occurred                                                           |
| `search_path`                | (`render_from_file` only, primarily for debugging) where is the template stored                                    |
| `template_file_name`         | (`render_from_file` only, primarily for debugging) name of the template, that was used                             |
| `cleaned_template_result()`  | returns a cleaned representation of the template_result (without whitespace and tabs/4 times blanks)               |
| `to_json()`                  | returns a dictionary representation of this class |

You can als render templates that are stored in directories to use more advanced features, like 
[Template inheritance](http://jinja.pocoo.org/docs/2.9/templates/#template-inheritance) and multiple template files. 
To enable the file-based lookup, just modify the following two lines from the previous example:

```python
...
if __name__ == "__main__":
    confgen = NetworkConfGen(searchpath="templates")
    
    ...
    
    # will look for a template file located at "./templates/my_template_file.txt"
    result = confgen.render_from_file(file_name="my_template_file.txt", parameters=parameters)
    
    ...
```

You find additional example scripts in the examples directory. 

## content error checking
  
To check if something went wrong with in the custom filter, you can verify the content with the `content_error` property (see the previous table 
in the "Quickstart" section). The `content_error` is set to `True` if the template result contains well-known error codes that are added by the  
custom filters.
