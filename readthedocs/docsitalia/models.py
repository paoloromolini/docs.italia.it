from __future__ import absolute_import
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from readthedocs.projects.models import Project
from readthedocs.oauth.models import RemoteOrganization


@python_2_unicode_compatible
class Publisher(models.Model):
    """
    The Publisher is the organization that hosts projects

    The idea is to tie a Publisher to a RemoteOrganization, if we have a
    Publisher instance for a RemoteOrganization we can sync its data as
    available in the well-known repo and config files.

    Given the requirement of handling content in different languages we don't
    want to duplicate the publisher data here so the config file is the source
    of truth. A parsed version of the configuration is saved in the metadata
    field.

    The publisher and the project homepage are handled by a django view.
    """
    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # we need something unique
    name = models.CharField(_('Name'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)

    # TODO: is this enough to hold the publisher metadata?
    # https://github.com/italia/docs-italia-starter-kit/tree/master/repo-configurazione
    metadata = models.JSONField(_('Metadata'), blank=True)
    # the name of the repository that will hold the metadata
    config_repo_name = models.CharField(_('Docs italia config repo'), default=u'docs-italia-conf')

    # the projects linked to the organization, should be the one in the metadata
    projects = models.ManyToManyField(_('Projects'), Project)
    # the same publisher may have projects in multiple platforms
    remote_organization = models.ManyToMany(_('Remote organization'), RemoteOrganization)

    active = models.BooleanField(_('Active'), default=False)

    def __str__(self):
        return self.name

    # TODO
    def repos_whitelist(self):
        return []

    # TODO
    def parse_metadata_repo(self, metadata_repo):
        return """{}"""
