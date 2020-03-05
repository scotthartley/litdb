from setuptools import setup, find_packages

# def readme():
#     with open("README.rst", encoding='utf8') as file:
#         return file.read()

exec(open('litdb/_version.py').read())

setup(name='litdb',
      version=__version__,
      description=("Manages local YAML DB with a focus on retrieving articles "
                   "from Crossref."),
      # long_description=readme(),
      author='Scott Hartley',
      author_email='scott.hartley@miamioh.edu',
      url='https://hartleygroup.org',
      # license='MIT',
      packages=find_packages(),
      entry_points={
          'console_scripts': [
              'litdb = litdb:main',
          ]
      },
      install_requires=["PyYAML", "habanero", "argparse"],
      python_requires=">=3.6",
      )
