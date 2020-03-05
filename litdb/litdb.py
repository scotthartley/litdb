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
        "--doi",
        help="DOI to be added to database")
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

    if args.doi:
        retrieved_record = get_doi([args.doi], configuration)
        db, num_additions, num_updates = DB_dict.merge_dbs(
                retrieved_record, db)
    else:
        retrieved_records = update_from_cr(configuration)
        dois_to_check = []
        for doi in db:
            if not db[doi].finalized:
                dois_to_check.append(doi)

        db, num_additions, num_updates_new = DB_dict.merge_dbs(
                retrieved_records, db, configuration['journal-blacklist'],
                configuration['affiliation'])

        updated_records = get_doi(dois_to_check, configuration)
        db, _, num_updates_old = DB_dict.merge_dbs(
                updated_records, db, configuration['journal-blacklist'],
                configuration['affiliation'])
        num_updates = num_updates_new + num_updates_old

    print(f"{num_additions} records added, {num_updates} records updated.")

    with open(args.db_file, 'w') as db_file:
        print(yaml.dump(db), file=db_file)
