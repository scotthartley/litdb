import argparse
import yaml
import sys
# from .DB_dict import DB_dict


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
        key = getattr(db[doi], template['sort-by'])
        output = db[doi].title
        outputs.append([key, output])

    breakpoint()

