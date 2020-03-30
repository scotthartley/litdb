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
    return DB_dict.parse_cr(cr_results['message']['items'])


def get_doi(dois, config):
    """Retrieve an article by doi.
    """
    crossref = Crossref(mailto=config['settings']['email'])
    cr_result = crossref.works(ids=dois)
    if len(dois) == 1:
        return DB_dict.parse_cr([cr_result['message']])
    else:
        return DB_dict.parse_cr([c['message'] for c in cr_result])


def litdb():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_file",
        help="Configuration file name")
    parser.add_argument(
        "db_file",
        help="Database file name")
    parser.add_argument(
        "-ad", "--add_doi",
        help="DOI to be added to database")
    parser.add_argument(
        "-od", "--override_doi",
        help="DOI, field, and value to override",
        nargs=3, type=str)
    args = parser.parse_args()

    try:
        with open(args.config_file) as config_file:
            configuration = yaml.load(config_file.read(),
                                      Loader=yaml.FullLoader)
    except FileNotFoundError:
        print("A configuration file must be provided.")
        sys.exit(1)

    try:
        with open(args.db_file) as db_file:
            db = yaml.load(db_file.read(), Loader=yaml.FullLoader)
    except FileNotFoundError:
        # Database file is being created from scratch.
        db = {}

    if args.add_doi:
        retrieved_record = get_doi([args.add_doi], configuration)
        db, num_additions, num_updates = DB_dict.merge_dbs(
                retrieved_record, db, configuration)
    elif args.override_doi:
        doi, field, value = args.override_doi
        db[doi].add_override(field, value)
        num_additions = 0
        num_updates = 1
    else:
        # Get new records, and check all records that are not finalized
        # to see if there are updates.
        dois_to_check = []
        for doi in db:
            if not db[doi].finalized:
                dois_to_check.append(doi)

        retrieved_records = update_from_cr(configuration)
        db, num_additions, num_updates_new = DB_dict.merge_dbs(
                retrieved_records, db, configuration)

        updated_records = get_doi(dois_to_check, configuration)
        db, _, num_updates_old = DB_dict.merge_dbs(
                updated_records, db, configuration)
        num_updates = num_updates_new + num_updates_old

    print(f"{num_additions} records added, {num_updates} records updated.")

    with open(args.db_file, 'w') as db_file:
        print(yaml.dump(db), file=db_file)
