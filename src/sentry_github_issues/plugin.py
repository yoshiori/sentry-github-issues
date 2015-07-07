from django import forms
from django.utils.translation import ugettext_lazy as _
from sentry.plugins.bases.issue import IssuePlugin
from sentry.utils import json

import sentry_github_issues
import urllib2

class GitHubIssuesOptionsForm(forms.Form):
    repo = forms.CharField(label=_('Repository Name'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. getsentry/sentry'}),
        help_text=_('Enter your repository name, including the owner.'))

    access_token = forms.CharField(label=_('access token'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. xxxxxxxxxxxxxxxxxxxxxxxx'}),
        help_text=_('Enter your personal access token, create here https://github.com/settings/tokens/new'))

    base_url = forms.CharField(label=_('API base url'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. https://github.example.com/'}),
        help_text=_('if Github Enterprise, Enter base url. '), required=False)

    label = forms.CharField(label=_('label'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. sentry'}),
        help_text=_('Enter label text.'), required=False)

class GitHubIssuesPlugin(IssuePlugin):
    slug = 'github-issues'
    title = _('GitHub Issues')
    author = 'Yoshiori SHOJI'
    author_url = 'https://github.com/yoshiori'
    version = sentry_github_issues.VERSION
    description = "Integrate GitHub issues by linking a repository to a project."
    resource_links = [
        ('Bug Tracker', 'https://github.com/yoshiori/sentry-github-issues/issues'),
        ('Source', 'https://github.com/yoshiori/sentry-github-issues'),
    ]
    conf_key = slug
    project_conf_form = GitHubIssuesOptionsForm

    def is_configured(self, request, project, **kwargs):
        return bool(self.get_option('repo', project))

    def get_new_issue_title(self, **kwargs):
        return 'Create GitHub Issue'

    def create_issue(self, request, group, form_data, **kwargs):
        repo = self.get_option('repo', group.project)
        base_url = self.get_option('base_url', group.project)
        endpoint = '%sapi/v3/' % base_url if base_url and base_url != "https://api.github.com/" else "https://api.github.com/"
        url = '%srepos/%s/issues' % (endpoint, repo,)
        data = {
          "title": form_data['title'],
        }
        data["body"] = '%s\n\n[<a href="%s">View on Sentry</a>]' % (form_data['description'], group.get_absolute_url())
        label = self.get_option('label', group.project)
        if label:
            data["label"] = [label]

        req = urllib2.Request(url, json.dumps(data))
        req.add_header('User-Agent', 'sentry-issue-github/%s' % self.version)
        req.add_header('Authorization', 'token %s' % self.get_option('access_token', group.project))
        req.add_header('Content-Type', 'application/json')

        try:
            resp = urllib2.urlopen(req)
        except Exception, e:
            if isinstance(e, urllib2.HTTPError):
                msg = e.read()
                if 'application/json' in e.headers.get('Content-Type', ''):
                    try:
                        msg = json.loads(msg)
                        msg = msg['message']
                    except Exception:
                        pass
            else:
                msg = unicode(e)
            raise forms.ValidationError(_('Error communicating with GitHub: %s') % (msg,))

        try:
            data = json.load(resp)
        except Exception, e:
            raise forms.ValidationError(_('Error decoding response from GitHub: %s') % (e,))

        return data['number']

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'GH-%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        repo = self.get_option('repo', group.project)
        base_url = self.get_option('base_url', group.project) or "https://github.com/"
        return '%s%s/issues/%s' % (base_url, repo, issue_id)
