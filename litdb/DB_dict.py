from datetime import date


class DB_dict(dict):
    """Subclass of dict that automates data retrieval to allow
    overrides. Used to store records retrieved from Crossref.
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
    def doi(self):
        return self.override('doi')

    @property
    def title(self):
        # Removes extra whitespace and newlines.
        return " ".join(self.override('title').split())

    @property
    def journal(self):
        return self.override('journal')

    @property
    def authors_list(self):
        """Returns the authors as a list.
        """
        if 'authors' in self[DB_dict.CR_KEY]:
            authors = self.override('authors')
            for n in range(len(authors)):
                authors[n]['given_name'] = (
                        DB_dict.add_initial_periods(authors[n]['given_name']))
            return authors
        else:
            return None

    @property
    def authors(self):
        """Returns the authors as a formatted string.
        """
        authors_list = []
        for a in self.authors_list:
            authors_list.append(f"{a['family_name']}, {a['given_name']}")
        return "; ".join(authors_list)

    @property
    def pages(self):
        # Includes ERROR_STRING for output.
        if DB_dict.OV_KEY in self:
            if 'pages' in self[DB_dict.OV_KEY]:
                return self[DB_dict.OV_KEY]['pages']
        elif 'pages' in self[DB_dict.CR_KEY]:
            if self.doi not in self[DB_dict.CR_KEY]['pages']:
                return self.override('pages').replace("-", "–")
        elif self.finalized:
            return DB_dict.ERROR_STRING
        else:
            return None

    @property
    def pages_raw(self):
        # Omits the error string for output.
        if 'pages' in self[DB_dict.CR_KEY]:
            if self.doi not in self[DB_dict.CR_KEY]['pages']:
                return self.override('pages').replace("-", "–")
        else:
            return None

    @property
    def year(self):
        """Returns the year published. Must always return something so
        that records will always be included somewhere if filtered by
        year.
        """
        if self.override('published-print'):
            return self.override('published-print')[0:4]
        elif self.override('issued'):
            return self.override('issued')[0:4]
        else:
            return self['created'][0:4]

    @property
    def deposited(self):
        return self.override('deposited')

    @property
    def created(self):
        return self.override('created')

    @property
    def volume(self):
        return self.override('volume')

    @property
    def issue(self):
        return self.override('issue')

    @property
    def finalized(self):
        """Records are considered finalized once they have an issue or
        pages assigned.
        """
        if self.issue or self.pages_raw:
            return True
        else:
            return False

    @property
    def omit(self):
        """Defines whether a record should be ignored on output.
        """
        if DB_dict.OV_KEY in self:
            if 'omit' in self[DB_dict.OV_KEY]:
                return self[DB_dict.OV_KEY]['omit']
        else:
            return False

    def add_override(self, field, value):
        """Adds an override field to the db.
        """

        if DB_dict.OV_KEY not in self:
            self[DB_dict.OV_KEY] = {}
        self[DB_dict.OV_KEY][field] = value

    @staticmethod
    def parse_cr(cr_results):
        """Given a set of raw cr_results, imports as a dictionary of
        key fields.
        """

        def convert_date(imported_date):
            if len(imported_date) == 3:
                return date(*imported_date).isoformat()
            else:
                return str(imported_date[0])

        records = {}
        for r in cr_results:
            record = DB_dict()
            record[DB_dict.CR_KEY] = {}

            record[DB_dict.CR_KEY]['doi'] = r['DOI']
            record[DB_dict.CR_KEY]['title'] = r['title'][0]

            record[DB_dict.CR_KEY]['authors'] = []
            for a in r['author']:
                author = {}
                author['family_name'] = a['family']
                if 'given' in a:
                    author['given_name'] = a['given']
                author['affiliation'] = [i['name'] for i in a['affiliation']]
                if 'ORCID' in a:
                    author['orcid'] = a['ORCID']
                record[DB_dict.CR_KEY]['authors'].append(author)

            if 'published-print' in r:
                record[DB_dict.CR_KEY]['published-print'] = convert_date(
                        r['published-print']['date-parts'][0])
            if 'issued' in r:
                record[DB_dict.CR_KEY]['issued'] = convert_date(
                        r['issued']['date-parts'][0])
            if 'published-online' in r:
                record[DB_dict.CR_KEY]['published-online'] = convert_date(
                        r['published-online']['date-parts'][0])
            record[DB_dict.CR_KEY]['deposited'] = r['deposited']['date-time']
            record[DB_dict.CR_KEY]['created'] = r['created']['date-time']

            if 'volume' in r:
                record[DB_dict.CR_KEY]['volume'] = r['volume']

            if 'issue' in r:
                record[DB_dict.CR_KEY]['issue'] = r['issue']

            if 'page' in r:
                record[DB_dict.CR_KEY]['pages'] = r['page']
            elif 'article-number' in r and 'published-print' in r:
                record[DB_dict.CR_KEY]['pages'] = r['article-number']

            if 'container-title' in r:
                record[DB_dict.CR_KEY]['journal'] = r['container-title'][0]
            if 'short-container-title' in r:
                if len(r['short-container-title']) != 0:
                    record[DB_dict.CR_KEY]['journal-abr'] = (
                            r['short-container-title'][0])

            if 'publisher' in r:
                record[DB_dict.CR_KEY]['publisher'] = r['publisher']

            records[record[DB_dict.CR_KEY]['doi']] = record
        return records

    @staticmethod
    def add_initial_periods(name):
        """Adds periods to the ends of initials in author names. This is
        done on the basis of their length (i.e., 1 letter), although
        longer initials can be defined in the the MULTICHAR_INITIALS
        constant.
        """
        names = name.split()
        for n in range(len(names)):
            if len(names[n]) == 1:
                names[n] = names[n] + "."
            elif names[n] in DB_dict.MULTICHAR_INITIALS:
                names[n] = names[n] + "."
        return " ".join(names)

    @staticmethod
    def merge_dbs(new_records, db, config=None):
        """Update records in list of DB_dict with new records.
        """

        def flatten(l):
            """Flattens a list ([[a], [b], [c]] -> [a , b, c])
            https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
            """
            flat_list = []
            for sublist in l:
                for item in sublist:
                    flat_list.append(item)
            return flat_list

        def diff_dict(d1, d2):
            """Compares two dictionaries and returns the list of keys
            that differentiate them.
            """
            different_keys = set()

            for key in d1:
                if key in d2:
                    if d1[key] != d2[key]:
                        different_keys.add(key)
                else:
                    different_keys.add(key)
            for key in d2:
                if key in d1:
                    if d1[key] != d2[key]:
                        different_keys.add(key)
                else:
                    different_keys.add(key)

            return different_keys

        if config:
            if 'journal-blacklist' in config:
                journal_blacklist = config['journal-blacklist']
            else:
                journal_blacklist = []
            if 'affiliation' in config:
                affiliation = config['affiliation']
            else:
                affiliation = ""
        else:
            journal_blacklist = []
            affiliation = ""

        # List of orcid ids for authors that must have strict
        # affiliations.
        strict_list = []
        for orcid in config['authors']:
            if 'strict' in config['authors'][orcid]:
                if config['authors'][orcid]['strict']:
                    strict_list.append(orcid)

        additions = []
        updates = {}
        for doi in new_records:
            if doi not in db:
                # First check to make sure that the article satisfies
                # the author and affiliation requirements.
                all_affiliations = flatten(
                        [j['affiliation'] for j in
                            new_records[doi][DB_dict.CR_KEY]['authors']])
                # If an author is flagged as strict, record should only
                # be added if affiliation is explicitly indicated.
                strict = False
                for author in new_records[doi][DB_dict.CR_KEY]['authors']:
                    if 'orcid' in author:
                        for orcid in strict_list:
                            if orcid in author['orcid']:
                                strict = True
                correct_affiliation = False
                if len(all_affiliations) == 0 and not strict:
                    correct_affiliation = True
                else:
                    for a in all_affiliations:
                        if affiliation in a:
                            correct_affiliation = True

                correct_journal = (new_records[doi][DB_dict.CR_KEY]['journal']
                                   not in journal_blacklist)

                if correct_affiliation and correct_journal:
                    db[doi] = DB_dict()
                    db[doi][DB_dict.CR_KEY] = new_records[doi][DB_dict.CR_KEY]
                    additions.append(doi)
            elif new_records[doi][DB_dict.CR_KEY] != db[doi][DB_dict.CR_KEY]:
                # Update if record has changed.
                changed_field_keys = diff_dict(
                        db[doi][DB_dict.CR_KEY],
                        new_records[doi][DB_dict.CR_KEY])
                changes = {}
                for key in changed_field_keys:
                    changes[key] = (db[doi][DB_dict.CR_KEY].get(key),
                                    new_records[doi][DB_dict.CR_KEY].get(key))
                db[doi][DB_dict.CR_KEY] = new_records[doi][DB_dict.CR_KEY]
                updates[doi] = changes
        return db, additions, updates
