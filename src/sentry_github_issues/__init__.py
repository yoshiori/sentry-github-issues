try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('sentry-github-issues').version
except Exception, e:
    VERSION = 'unknown'
