import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

install_requires = [
    'django>=1.11.19,<3.0',
    'django-haystack==2.8.1',
    'django-filter==2.0.0',
    'djangorestframework==3.11.2',
    'dj-database-url==0.5.0',
    'django-braces==1.9.0',
    'django-crispy-forms==1.7.2',
    'django-floppyforms==1.7.0',
    'django-extra-views==0.12.0',
    'django-model-utils==3.1.2',
    'django-extensions==2.1.4',
    'django-image-cropping==1.2.0',
    'django-webpack-loader==0.6.0',
    'drf-yasg==1.20.0',
    'easy-thumbnails==2.5',
    'python-decouple==3.1',
    'psycopg2-binary==2.7.6.1',
    'pyyaml==5.4',
    'pytz==2018.9',
    'python-magic==0.4.15',
    'unipath==1.1',
    'WeasyPrint==44',
    'gunicorn==19.9.0',
    'pysolr==3.6.0',

    # 'git+git://github.com/interlegis/trml2pdf.git',
    # 'git+git://github.com/interlegis/django-admin-bootstrapped',
]
setup(
    name='interlegis-sapl',
    version='3.1.163-RC20',
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
