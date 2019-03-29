from __future__ import unicode_literals

from setuptools import find_packages, setup

import picklefield

with open('README.rst') as file_:
    long_description = file_.read()

setup(
    name='django-picklefield',
    version=picklefield.__version__,
    description='Pickled object field for Django',
    long_description=long_description,
    author='Simon Charette',
    author_email='charette.s+django-picklefiel@gmail.com',
    url='http://github.com/gintas/django-picklefield',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['django pickle model field'],
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=['Django>=1.11'],
    extras_require={
        'tests': ['tox', 'joblib'],
    },
)
