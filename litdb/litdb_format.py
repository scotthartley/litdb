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

    outputs = {}
    for f in template['filters']:
        outputs[f] = []
        for doi in db:
            if not db[doi].omit:
                if 'property' in template['filters'][f]:
                    target_field = template['filters'][f]['property']
                    target_value = str(template['filters'][f]['value'])
                    if target_value in getattr(db[doi], target_field):
                        key = getattr(db[doi], template['filters'][f]['sort_by'])
                        output = apply_template(db[doi], template)
                        outputs[f].append([key, output])
                else:
                    key = getattr(db[doi], template['filters'][f]['sort_by'])
                    output = apply_template(db[doi], template)
                    outputs[f].append([key, output])
        if template['filters'][f]['sort_order'] == 'reverse':
            outputs[f] = sorted(outputs[f], reverse=True)
        else:
            outputs[f] = sorted(outputs[f], reverse=False)
        if 'max_records' in template['filters'][f]:
            outputs[f] = outputs[f][:template['filters'][f]['max_records']]

    for f in outputs:
        output_filename = f"{args.db_file}_{f}.{template['file_extension']}"
        with open(output_filename, 'w') as output_file:
            for n in outputs[f]:
                print(n[1], file=output_file)
