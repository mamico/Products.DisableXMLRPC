# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


version = '1.0.0a2'

with open('README.rst') as f:
    long_description = f.read()
with open('CHANGES.rst') as f:
    long_description += '\n\n' + f.read()


setup(
    name='Products.DisableXMLRPC',
    version=version,
    description=(
        "Backport of Zope 5.13's enable-xmlrpc switch: disable Zope's "
        "built-in XML-RPC support on Zope 2.13, 4 and 5 < 5.13"),
    long_description=long_description,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Zope',
        'Framework :: Zope2',
        'Framework :: Zope :: 4',
        'Framework :: Zope :: 5',
        'Framework :: Plone',
        'License :: OSI Approved :: Zope Public License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Security',
    ],
    keywords='zope plone xmlrpc security',
    author='RedTurtle Technology',
    author_email='mauro.amico@redturtle.it',
    license='ZPL 2.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['Products'],
    include_package_data=True,
    zip_safe=False,
    python_requires='>=2.7',
    # Zope is not declared on purpose: the distribution is called "Zope2"
    # up to 2.13 and "Zope" from 4.0 on.
    install_requires=[],
)
