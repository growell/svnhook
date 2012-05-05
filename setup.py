from distutils.core import setup

config = {
    'description': 'Subversion Hook Framework',
    'author': 'Geoff Rowell',
    'url': 'http://sourceforge.net',
    'download_url': 'http://github.com',
    'author_email': 'geoff.rowell@gmail.com',
    'version': '3.00',
    'install_requires': ['nose'],
    'packages': ['svnhook'],
    'scripts': [],
    'name': 'svnhook'
}

setup(**config)