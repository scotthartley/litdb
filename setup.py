from setuptools import setup, find_packages

# def readme():
#     with open("README.rst", encoding='utf8') as file:
#         return file.read()

exec(open('crossref_db/_version.py').read())

setup(name='crossref-db',
      version=__version__,
      description='Retrieves articles from Crossref, manages local YAML DB.',
      # long_description=readme(),
      author='Scott Hartley',
      author_email='scott.hartley@miamioh.edu',
      url='https://hartleygroup.org',
      # license='MIT',
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'crossref_db = crossref_db:main',
          ]
      },
      install_requires=["PyYAML", "habanero", "argparse"],
      python_requires=">=3.6",
      )
