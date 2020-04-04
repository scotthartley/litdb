litdb: A Python script that manages a database of publications using ORCID ids and Crossref
===========================================================================================

litdb is a Python script that manages a `YAML <https://yaml.org>`__
database of publications by querying
`Crossref <https://www.crossref.org/>`__ for a list of `ORCID
ids <https://orcid.org/>`__. So, it can be used to maintain lists of
publications for a team of researchers, or members of the same
department, etc. A companion script, litdb_format, will pull from the
database and format output. These can be run manually, but they are
intended to be run as scheduled jobs to maintain the database
automatically as new articles are published.

litdb uses the `habanero <https://github.com/sckott/habanero>`__ package
to interface with Crossref and `PyYAML <https://pyyaml.org>`__ to
interpret the YAML files.

Installation
------------

Download the release and install with pip (or just use the source code).

Usage
-----

To update the database, simply run
``litdb config_file.yaml db_file.yaml``. The database file
``db_file.yaml`` will be created if it does not yet exist. The
configuration file ``config_file.yaml`` is required and should have the
following format:

::

   settings:
     email: "my_email@address"
     article_type: "journal-article"
     sort_field: "published"
     order: "desc"
     num_records: 10

   journal-blacklist:
     - Journal Name

   affiliation: Organization Name

   authors:
     ####-####-####-####:
       name: Author Name
     ####-####-####-####:
       name: Author Name
       strict: True

-  The ``settings`` define the interaction with Crossref:

   -  The ``email`` field should be set to take advantage of Crossref’s
      “`polite pool <https://github.com/CrossRef/rest-api-doc>`__”.
   -  ``article_type`` specifies the type of article (via the “type”
      field in the Crossref metadata) that should be retrieved
      (“journal-article” for a typical peer-reviewed publication).
   -  ``sort_field`` specifies how the returned Crossref records will be
      sorted.
   -  ``order`` specifies the sort order.
   -  ``num_records`` specifies how many records will be retrieved. This
      should be a larger number when the database is initialized but
      then much smaller afterwards when it is just being updated.

-  The ``journal-blacklist`` is used to screen out journals from the
   database. For example, in chemistry articles will be double-published
   in *Angewante Chemie* and *Angewante Chemie, International Edition*,
   so these should only be included once.

-  The ``affiliation`` is the affiliation of the authors. This is used
   for authors where the “strict” field has been set to omit
   publications from previous work at other institutions.

-  The ``authors`` is the list of authors:

   -  The primary identification is their ORCID ID, as in
      ``####-####-####-####``.
   -  ``name`` is fairly obvious.
   -  Set ``strict: True`` to only include publications that match
      *both* the ORCID ID and include the affiliation. This may miss
      some publications, because not every Crossref record includes
      detailed affiliations, but it avoids false positives.

The ``litdb`` program has two other modes. Using the ``--ad_doi`` or
``-ad`` options followed by a DOI will add that publication to the
database (regardless of the authorship).

Using the ``--override_doi`` or ``-od`` options followed by a DOI, field
name, and new field value allows data retrieved from Crossref to be
overridden on output. This can be used to correct errors in the Crossref
data or to suppress articles by setting the “omit” field to “True”. So,
for example, ``litdb config.yaml lit.yaml -od DOI_NUMBER omit True``
will cause the output of the article with DOI ``DOI_NUMBER`` to be
suppressed. The command
``litdb config.yaml lit.yaml -od DOI_NUMBER pages 20–30`` would set the
page numbers of article with DOI ``DOI_NUMBER`` to be set to 20–30.

Because it is a simple YAML document, the database can always be edited
manually when larger changes must be made. The Crossref data itself
(under the ``crossref`` key) should not be edited (it will be changed
back if that record is pulled back down from Crossref), but any field
can be overridden by specifying new values under the ``override`` key.

Records from the database can be output using the command
``litdb_format template_file.yaml db_file.yaml``. The template file
should look something like this:

::

   filters:
     Most_recent:
       sort_by: "created"
       sort_order: "reverse"
       max_records: 3
     2020:
       property: year
       value: 2020
       sort_by: "created"
       sort_order: "reverse"
     2019:
       property: year
       value: 2019
       sort_by: "created"
       sort_order: "reverse"

   elements:
     title: "<i>{title}</i><br />"
     authors: "{authors}<br />"
     journal: "<i>{journal}</i>"
     year: "<b>{year}</b>"
     volume: ", <i>{volume}</i>"
     pages: ", {pages}"
     doi: "{doi}"

   templates:
     complete: |-
       <p>{title}{authors}<a href="https://doi.org/{doi}" rel="noopener" target="_blank">{journal} {year}{volume}{pages}</a></p>
     incomplete: |-
       <p>{title}{authors}<a href="https://doi.org/{doi}" rel="noopener" target="_blank">{journal}, in press</a></p>

   file_extension: html

   output_directory: output_html

This template will produce three separate html files that can be pasted
into an online list of publications. These particular files won’t have
proper headers, but they could be included to automate a list of papers
on a website (see below). For this file:

-  The ``filters`` define separate files that will be produced. In this
   case, three files are produced based on the year of publication. One
   is the three most-recent articles, and the other two are articles
   published in 2020 and 2019. For each one,

   -  ``sort_by`` specifies the field that will be used to sort the
      records.
   -  ``sort_order`` specifies how they will be sorted (in this case
      most- to least-recent).
   -  ``max_records`` specifies whether the total number of records
      should be cut off.
   -  ``property`` specifies a property used as a filter.
   -  ``value`` specifies the value of the property that will be used to
      filter.

-  Each individual part of ``elements`` will be used in the templates
   (see below). Each one should include formatting markup and the name
   of a field from the database.
-  There should be two ``templates``. One, ``complete``, is for articles
   that have been assigned their final publication data. The other,
   ``incomplete``, is for articles that are still in press. Each one
   should be made up of the defined elements and any other decoration
   that is needed.
-  The ``file_extension`` is exactly that for each file that is
   produced.
-  The ``output_directory`` specifies the target directory for the
   output.

Here is another example of a template. This one produces as RSS feed of
the articles:

::

   filters:
     Most_recent:
       sort_by: "created"
       sort_order: "reverse"
       max_records: 20
     2020:
       property: "year"
       value: 2020
       sort_by: "created"
       sort_order: "reverse"
     2019:
       property: "year"
       value: 2019
       sort_by: "created"
       sort_order: "reverse"

   elements:
     title: "{title}"
     authors: "{authors}"
     journal: "{journal}"
     year: "{year}"
     volume: "{volume}"
     volume_formatted: ", <i>{volume}</i>"
     pages: "{pages}"
     doi: "{doi}"
     created: "{created}"

   templates:
     complete: |+
       <item>
         <title>{title}</title>
         <link>https://dx.doi.org/{doi}</link>
         <guid>{doi}</guid>
         <pubDate>{created}</pubDate>
         <description>{authors}, {journal}, {year}, {volume}, {pages}</description>
         <content:encoded>
           <![CDATA[
             <i>{title}</i><br />
             {authors}<br />
             <a href="https://dx.doi.org/{doi}" rel="noopener" target="_blank"><i>{journal}</i> <b>{year}</b>{volume_formatted}, {pages}</a>
           ]]>
         </content:encoded>
       </item>
     incomplete: |+
       <item>
         <title>{title}</title>
         <link>https://dx.doi.org/{doi}</link>
         <guid>{doi}</guid>
         <pubDate>{created}</pubDate>
         <description>{authors}, {journal}, {year}, {volume}, {pages}</description>
         <content:encoded>
           <![CDATA[
             <i>{title}</i><br />
             {authors}<br />
             <a href="https://dx.doi.org/{doi}" rel="noopener" target="_blank"><i>{journal}</i>, in press</a>
           ]]>
         </content:encoded>
       </item>

   header: |
     <?xml version="1.0" encoding="UTF-8" ?>
     <rss version="2.0">
     <channel>
     <title>The title of the feed.</title>

   footer: |
     </channel>
     </rss>

   file_extension: xml

   output_directory: /path/to/directory/output_xml

The idea here is the same as the HTML template, but it uses the
``header`` and ``footer`` fields to provide the text needed at the start
and end of each .xml file.
