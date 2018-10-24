import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

install_requires = [
    'dj-database-url==0.4.1',
    'django-haystack==2.6.0',
    'django>=1.10,<1.11',
    # TODO O django-admin-bootstrapped 2.5.7 não inseriu a mudança que permite
    # a compatibilidade com Django 1.9+. A linha abaixo será mudada quando uma
    # nova versão do django-admin-bootstrapped for lançada
    # 'git+git://github.com/django-admin-bootstrapped/
    #      django-admin-bootstrapped.git',
    'django-bootstrap3==7.0.1',
    'django-bower==5.2.0',
    'django-braces==1.9.0',
    'django-compressor==2.0',
    'django-crispy-forms==1.6.1',
    'django-extensions==1.9.8',
    'django-extra-views==0.11.0',
    'django-filter==0.15.3',
    'django-floppyforms==1.6.2',
    'django-model-utils==3.1.1',
    'django-sass-processor==0.5.8',
    'djangorestframework==3.4.0',
    'drfdocs',
    'easy-thumbnails==2.5',
    'django-image-cropping==1.1.0',
    # 'git+git://github.com/interlegis/trml2pdf.git',
    'libsass==0.11.1',
    'psycopg2==2.7.4',
    'python-decouple==3.0',
    'pytz==2016.4',
    'pyyaml==3.11',
    'rtyaml==0.0.3',
    'textract==1.5.0',
    'unipath==1.1',
    'pysolr==3.6.0',
    'python-magic==0.4.12',
    'gunicorn==19.6.0',
    'django-reversion==2.0.8',
    'WeasyPrint==0.42',
    'whoosh==2.7.4',
    'django-speedinfo==1.3.5',
    'django-reversion-compare==0.8.4'
]
setup(
    name='interlegis-sapl',
    version='3.1.128',
    packages=find_packages(),
    include_package_data=True,
    license='GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007',
    description='SAPL - Legislative Process Support System',
    long_description=README,
    url='https://github.com/interlegis/sapl',
    author='interlegis',
    author_email='',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=install_requires,
)
