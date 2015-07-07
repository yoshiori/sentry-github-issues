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

    api_endpoint = forms.CharField(label=_('API endpoint'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. https://github.example.com/api/v3/'}),
        help_text=_('if Github Enterprise, Enter api endpoint. '), required=False)

    web_endpoint = forms.CharField(label=_('Web endpoint'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. https://github.example.com/'}),
        help_text=_('if Github Enterprise, Enter web endpoint. '), required=False)

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
        api_endpoint = self.get_option('api_endpoint', group.project) or "https://api.github.com/"

        url = '%srepos/%s/issues' % (api_endpoint, repo,)
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
            raise forms.ValidationError(_('Error communicating with GitHub issues: %s') % (msg,))

        try:
            data = json.loads(resp.read())
        except Exception, e:
            raise forms.ValidationError(_('Error decoding response from GitHub issues: %s') % (e,))

        return data['number']

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'GH-%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        repo = self.get_option('repo', group.project)
        web_endpoint = self.get_option('web_endpoint', group.project) or "https://github.com/"
        return '%s%s/issues/%s' % (web_endpoint, repo, issue_id)
