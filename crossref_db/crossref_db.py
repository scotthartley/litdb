import argparse
from habanero import Crossref
import yaml
import sys
from .DB_dict import DB_dict


def update_from_cr(config):
    """Retrieve records from Crossref.
    """
    crossref = Crossref(mailto=config['settings']['email'])
    orcid_ids = [n for n in config['authors']]
    cr_results = crossref.works(
            filter={'orcid': orcid_ids,
                    'type': [config['settings']['article_type']]},
            sort=config['settings']['sort_field'],
            order=config['settings']['order'],
            limit=config['settings']['num_records'])
    return DB_dict.parse_cr(cr_results)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_file",
        help="Configuration file name")
    parser.add_argument(
        "db_file",
        help="Database file name")
    args = parser.parse_args()

    try:
        with open(args.config_file) as config_file:
            configuration = yaml.load(config_file.read(),
                                      Loader=yaml.FullLoader)
    except FileNotFoundError:
        print("A configuration file must be provided.")
        sys.exit()

    try:
        with open(args.db_file) as db_file:
            db = yaml.load(db_file.read(), Loader=yaml.FullLoader)
    except FileNotFoundError:
        db = {}

    retrieved_records = update_from_cr(configuration)

    db = DB_dict.merge_dbs(retrieved_records, db)

    with open(args.db_file, 'w') as db_file:
        print(yaml.dump(db), file=db_file)
