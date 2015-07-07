#!/usr/bin/env python
from setuptools import setup, find_packages

tests_require = [
    'nose',
]

install_requires = [
    'sentry>=5.0.0',
]

setup(
    name='sentry-github-issues',
    version='0.0.1',
    author='Yoshiori Shoji',
    author_email='yoshiori@gmail.com',
    url='http://github.com/yoshiori/sentry-github-issues',
    description='A Sentry extension which integrates with GitHub.',
    long_description=__doc__,
    license='MTI',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    test_suite='runtests.runtests',
    include_package_data=True,
    entry_points={
       'sentry.apps': [
            'github_issues = sentry_github_issues',
        ],
       'sentry.plugins': [
            'github_issues = sentry_github_issues.plugin:GitHubIssuesPlugin'
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
