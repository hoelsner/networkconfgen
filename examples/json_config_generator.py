"""
How-to use the NetworkConfigGen module (with JSON data)
=======================================================

Run the script with the following command (assuming that the `networkconfgen` library is installed):

```
python3 how_to_use.py example_parameters.json how_to_template.template
```

The example_parameters.json contains the parameters that are used to render the how_to_template.template file.

"""
import os
import sys
import json
from networkconfgen import NetworkConfGen

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("additional arguments required, use the following command to run the script:\n\t"
              "python3 how_to_use.py example_parameters.json how_to_template.template\n\n")
        sys.exit()

    parameter_file = sys.argv[1]
    template_file = sys.argv[2]

    # verify given arguments
    if not (os.path.exists(parameter_file) and os.path.isfile(parameter_file)):
        print("parameter file doesn't exists or not found. Please verify your arguments")
        sys.exit()

    if not (os.path.exists(template_file) and os.path.isfile(template_file)):
        print("template file doesn't exists or not found. Please verify your arguments")
        sys.exit()

    # load parameters
    try:
        with open(parameter_file) as f:
            params = json.loads(f.read())

    except Exception as ex:
        print("unable to load JSON parameters: %s" % ex)
        sys.exit()

    # load template
    try:
        with open(template_file) as f:
            template = f.read()

    except Exception as ex:
        print("unable to load template files: %s" % ex)
        sys.exit()

    # generate configuration and print to stdout (using the string renderer)
    confgen = NetworkConfGen()
    result = confgen.render_from_string(template_content=template, parameters=params)

    if result.render_error:
        print("!!! Error during rendering of the template:\n\n%s\n\n" % result.error_text)

    elif result.content_error:
        print("!!! Error with the content of the template, rendered results are:\n\n%s\n\n" % result.template_result)

    else:
        # use the cleaned output if no error occurred (lstrip whitespace and rstrip tabs and 4 consecutive blanks)
        print("Everything was fine :D\n\n%s\n\n" % result.cleaned_template_result())
