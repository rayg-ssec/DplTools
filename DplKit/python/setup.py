from setuptools import setup, find_packages

classifiers = ""
version = '0.1.1'

setup(
    name='dplkit',
    version=version,
    description="Libraries, scripts, and utilities for UW SSEC Data Pot-Luck (DPL)",
    classifiers=filter(None, classifiers.split("\n")),
    keywords='',
    author='Ray Garcia, SSEC',
    author_email='rayg@ssec.wisc.edu',
    url='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    #namespace_packages=['ifg'],
    include_package_data=True,
    zip_safe=True,
    install_requires=['numpy'],
    dependency_links = ['http://larch.ssec.wisc.edu/cgi-bin/repos.cgi']
)

