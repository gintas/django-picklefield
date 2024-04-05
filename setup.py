from setuptools import find_packages, setup

import picklefield

with open('README.rst') as file_:
    long_description = file_.read()

setup(
    name='django-picklefield',
    version=picklefield.__version__,
    description='Pickled object field for Django',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Simon Charette',
    author_email='charette.s+django-picklefiel@gmail.com',
    url='http://github.com/gintas/django-picklefield',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Framework :: Django :: 4.1',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['django pickle model field'],
    packages=find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.8',
    install_requires=['Django>=3.2'],
    extras_require={
        'tests': ['tox'],
    },
)
