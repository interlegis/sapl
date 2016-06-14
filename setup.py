import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

install_requires = [
    'dj-database-url==0.4.1',
    'django-admin-bootstrapped==2.5.7',
    'django-bootstrap3==7.0.1',
    'django-bower==5.1.0',
    'django-braces==1.8.1',
    'django-compressor==2.0',
    'django-crispy-forms==1.6.0',
    'django-extensions==1.6.1',
    'django-extra-views==0.7.1',
    'django-filter==0.13.0',
    'django-floppyforms==1.6.1',
    'django-model-utils==2.4',
    'django-sass-processor==0.3.4',
    'django>=1.9.5',
    'djangorestframework',
    'easy-thumbnails==2.3',
    'libsass==0.11.0',
    'psycopg2==2.6.1',
    'python-decouple==3.0',
    'pytz==2016.3',
    'pyyaml==3.11',
    'rtyaml==0.0.2',
    'unipath==1.1',
    'python-magic==0.4.10',
    'gunicorn==19.4.5',
#git+git://github.com/interlegis/trml2pdf.git    
]
setup(
    name='interlegis-sapl',
    version='3.1.1-alpha',
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
    install_requires = install_requires,
)
