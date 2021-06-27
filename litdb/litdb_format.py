import argparse
import yaml
import sys
import re
from pathlib import Path

PATTERN = r"\{(.*)\}"


def apply_template(record, template):
    """Apply a template defined in template to a record. The template
    must include versions for complete and incomplete records.
    """
    output_elements = {}
    for e in template['elements']:
        field = re.search(PATTERN, template['elements'][e]).group(1)
        replacement = getattr(record, field)
        if replacement:
            output_elements[e] = template['elements'][e].replace(
                    f"{{{field}}}", replacement)
        else:
            output_elements[field] = ""

    if record.finalized:
        output = template['templates']['complete']
    else:
        output = template['templates']['incomplete']
    for e in output_elements:
        # breakpoint()
        output = output.replace(f"{{{e}}}", output_elements[e])

    return output.encode('ascii', 'xmlcharrefreplace').decode('ascii')


def litdb_format():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "template_file",
        help="Configuration file name")
    parser.add_argument(
        "db_file",
        help="Database file name")
    args = parser.parse_args()

    try:
        with open(args.template_file) as template_file:
            template = yaml.load(template_file.read(),
                                 Loader=yaml.Loader)
    except FileNotFoundError:
        print("A template file must be provided.")
        sys.exit(1)

    try:
        with open(args.db_file) as db_file:
            db = yaml.load(db_file.read(), Loader=yaml.Loader)
    except FileNotFoundError:
        print("A database file must be provided.")
        sys.exit(1)

    # Generate output for every filter defined in the template. Stored
    # as a dictionary with the (unique) filter name as the key.
    outputs = {}
    for f in template['filters']:
        outputs[f] = []
        for doi in db:
            if not db[doi].omit:
                if 'property' in template['filters'][f]:
                    # The filter has defined a property that will be
                    # used to filter.
                    target_field = template['filters'][f]['property']
                    target_value = str(template['filters'][f]['value'])
                    if target_value in getattr(db[doi], target_field):
                        key = getattr(db[doi],
                                      template['filters'][f]['sort_by'])
                        output = apply_template(db[doi], template)
                        outputs[f].append([key, output])
                else:
                    # The filter uses all records (i.e., outputs all records,
                    # possibly to limit to a certain number of most recent).
                    key = getattr(db[doi], template['filters'][f]['sort_by'])
                    output = apply_template(db[doi], template)
                    outputs[f].append([key, output])
        if template['filters'][f]['sort_order'] == 'reverse':
            outputs[f] = sorted(outputs[f], reverse=True)
        else:
            outputs[f] = sorted(outputs[f], reverse=False)
        if 'max_records' in template['filters'][f]:
            outputs[f] = outputs[f][:template['filters'][f]['max_records']]

    # Write all of the files.
    if 'output_directory' in template:
        output_directory = Path(template['output_directory'])
        if not output_directory.is_dir():
            output_directory.mkdir(parents=True)
    else:
        output_directory = Path(".")
    for f in outputs:
        output_filename = output_directory / f"{f}.{template['file_extension']}"
        with open(output_filename, 'w') as output_file:
            if 'header' in template:
                print(template['header'], file=output_file)
            for n in outputs[f]:
                print(n[1], file=output_file)
            if 'footer' in template:
                print(template['footer'], file=output_file)
