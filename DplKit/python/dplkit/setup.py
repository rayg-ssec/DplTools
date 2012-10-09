from setuptools import setup, find_packages

classifiers = ""
version = '0.1.0'

setup(
    name='dplkit',
    version=version,
    description="Simple examples and tools for Data Pot Luck",
    classifiers=filter(None, classifiers.split("\n")),
    keywords='',
    author='R.K.Garcia',
    author_email='rayg@ssec.wisc.edu',
    url='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    # namespace_packages=['ifg'],
    include_package_data=True,
    zip_safe=True,
    install_requires=['numpy'],
    dependency_links = ['http://larch.ssec.wisc.edu/cgi-bin/repos.cgi'],
    # entry_points = {'console_scripts' : [
    #     'shis_res = ifg.util.csv_maker:main',
    #     'xdrleash = ifg.util.leash:main',
    #     'leash_echo = ifg.util.leash:echo',
    #     'sim_sdr = ifg.util.sim_xdr:main',
    #     'fbf2cdf = ifg.util.fbf2cdf:main'
    #     ]}
)
