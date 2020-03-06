import argparse
import yaml
import sys
# from .DB_dict import DB_dict


def apply_template(record, template):
    output_elements = {}
    for e in template['elements']:
        replacement = getattr(record, e)
        if replacement:
            output_elements[e] = template['elements'][e].replace(
                    f"{{{e}}}", replacement)
        else:
            output_elements[e] = ""

    if record.finalized:
        output = template['templates']['complete']
    else:
        output = template['templates']['incomplete']
    for e in output_elements:
        output = output.replace(f"{{{e}}}", output_elements[e])
    return output


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
                                 Loader=yaml.FullLoader)
    except FileNotFoundError:
        print("A template file must be provided.")
        sys.exit()

    try:
        with open(args.db_file) as db_file:
            db = yaml.load(db_file.read(), Loader=yaml.FullLoader)
    except FileNotFoundError:
        print("A database file must be provided.")
        sys.exit()

    outputs = []
    for doi in db:
        if not db[doi].omit:
            key = getattr(db[doi], template['sort-by'])
            output = apply_template(db[doi], template)
            outputs.append([key, output])
    outputs = sorted(outputs)

    for n in outputs:
        print(n[1])
