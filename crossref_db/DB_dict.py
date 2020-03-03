class DB_dict(dict):
    """Subclass of dict that automates data retrieval to allow overrides.
    """

    CR_KEY = 'crossref'
    OV_KEY = 'override'
    ERROR_STRING = "MISSING DATA"
    MULTICHAR_INITIALS = ["Md", "Wm"]

    def override(self, key):
        if DB_dict.OV_KEY in self:
            if key in self[DB_dict.OV_KEY]:
                return self[DB_dict.OV_KEY][key]
        if key in self[DB_dict.CR_KEY]:
            return self[DB_dict.CR_KEY][key]
        else:
            return None

    @property
    def title(self):
        return self.override('title')

    @property
    def journal(self):
        return self.override('journal')

    @property
    def authors(self):
        if 'authors' in self[DB_dict.CR_KEY]:
            authors = self.override('authors')
            for n in range(len(authors)):
                authors[n]['given_name'] = (
                        self.add_initial_periods(authors[n]['given_name']))
            return authors
        else:
            return None

    @property
    def pages(self):
        return self.override('pages')

    @property
    def year(self):
        return self.override('year')

    @property
    def finalized(self):
        if self.year and self.pages:
            return True
        else:
            return False

    @staticmethod
    def parse_cr(cr_results):
        """Given a set of raw cr_results, converts into a dictionary of key
        fields.
        """
        records = {}
        for r in cr_results:
            record = DB_dict()
            record[DB_dict.CR_KEY] = {}

            doi = r['DOI']
            record[DB_dict.CR_KEY]['title'] = r['title'][0]

            record[DB_dict.CR_KEY]['authors'] = []
            for a in r['author']:
                author = {}
                author['family_name'] = a['family']
                author['given_name'] = a['given']
                author['affiliation'] = [i['name'] for i in a['affiliation']]
                if 'ORCID' in a:
                    author['orcid'] = a['ORCID']
                record[DB_dict.CR_KEY]['authors'].append(author)

            if 'published-print' in r:
                record[DB_dict.CR_KEY]['year'] = str(
                        r['published-print']['date-parts'][0][0])
            elif 'issued' in r:
                record[DB_dict.CR_KEY]['year'] = str(
                        r['issued']['date-parts'][0][0])

            if 'volume' in r:
                record[DB_dict.CR_KEY]['volume'] = r['volume']

            if 'page' in r:
                record[DB_dict.CR_KEY]['pages'] = r['page']
            elif 'issue' in r:
                record[DB_dict.CR_KEY]['pages'] = DB_dict.ERROR_STRING

            if 'container-title' in r:
                record[DB_dict.CR_KEY]['journal'] = r['container-title'][0]

            records[doi] = record
        return records

    @staticmethod
    def add_initial_periods(name):
        names = name.split()
        for n in range(len(names)):
            if len(names[n]) == 1:
                names[n] = names[n] + "."
            elif names[n] in DB_dict.MULTICHAR_INITIALS:
                names[n] = names[n] + "."
        return " ".join(names)

    @staticmethod
    def merge_dbs(new_records, db, journal_blacklist=[], affiliation=""):
        """Update records in list of DB_dict with new records.
        """

        def flatten(l):
            """https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
            """
            flat_list = []
            for sublist in l:
                for item in sublist:
                    flat_list.append(item)
            return flat_list

        num_additions = 0
        num_updates = 0
        for doi in new_records:
            if doi not in db:
                all_affiliations = flatten(
                        [j['affiliation'] for j in
                            new_records[doi][DB_dict.CR_KEY]['authors']])
                correct_affiliation = False
                for a in all_affiliations:
                    if affiliation in a:
                        correct_affiliation = True
                correct_journal = (new_records[doi][DB_dict.CR_KEY]['journal']
                                   not in journal_blacklist)
                if correct_affiliation and correct_journal:
                    db[doi] = DB_dict()
                    db[doi][DB_dict.CR_KEY] = new_records[doi][DB_dict.CR_KEY]
                    num_additions += 1
            elif new_records[doi][DB_dict.CR_KEY] != db[doi][DB_dict.CR_KEY]:
                db[doi][DB_dict.CR_KEY] = new_records[doi][DB_dict.CR_KEY]
                num_updates += 1
        return db, num_additions, num_updates
