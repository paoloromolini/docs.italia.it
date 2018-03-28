from __future__ import absolute_import
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from readthedocs.projects.models import Project
from readthedocs.oauth.models import RemoteOrganization

from .utils import load_yaml


# TODO: do the validation :)
def validate_publisher_metadata(settings):
    return load_yaml(settings)


# TODO: do the validation :)
def validate_projects_metadata(settings):
    return load_yaml(settings)





@python_2_unicode_compatible
class Publisher(models.Model):
    """
    The Publisher is the organization that hosts projects (PublisherProject)

    The idea is to tie a Publisher to a RemoteOrganization, if we have a
    Publisher instance for a RemoteOrganization we can sync its data as
    available in the well-known repo and config files.

    Given the requirement of handling content in different languages we don't
    want to duplicate the publisher data here so the config file is the source
    of truth. A parsed version of the configuration is saved in the metadata
    field.

    The publisher homepage is handled by a django view with data from the metadata field.
    """
    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # we need something unique
    name = models.CharField(_('Name'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)

    # TODO: is this enough to hold the publisher metadata?
    # https://github.com/italia/docs-italia-starter-kit/tree/master/repo-configurazione
    metadata = models.JSONField(_('Publisher Metadata'), blank=True)
    projects_metadata = models.JSONField(_('Projects Metadata'), blank=True)

    # the name of the repository that will hold the metadata
    config_repo_name = models.CharField(_('Docs italia config repo'), default=u'docs-italia-conf')

    # the same publisher may have projects in multiple platforms
    remote_organization = models.ManyToMany(_('Remote organization'), RemoteOrganization)

    active = models.BooleanField(_('Active'), default=False)

    def __str__(self):
        return self.name

    def create_projects_from_metadata(self, settings):
        slugs = []
        for project in settings['projects']:
            slug = slugify(project['name'])
            proj, created = PublisherProjects.objects.get_or_create(
                publisher=self,
                name=project['name'],
                slug=slug
            )
            proj.metadata = project
            proj.active = True
            proj.save()

            slugs.append(slug)

        # TODO: double check this is something we want
        PublisherProjects.objects.filter(
            publisher=self
        ).exclude(
            slug__in=slugs
        ).update(
            active=False
        )


class PublisherProject(models.Model):
    """
    The PublisherProject is the project that contains documents

    These are created from the organization metadata and created at import time

    The publisher project homepage is handled by a django view with data from the metadata field.
    """
    # Auto fields
    pub_date = models.DateTimeField(_('Publication date'), auto_now_add=True)
    modified_date = models.DateTimeField(_('Modified date'), auto_now=True)

    # we need something unique
    name = models.CharField(_('Name'), max_length=255, unique=True)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)

    # this holds the metadata for the single project
    metadata = models.JSONField(_('Metadata'), blank=True)

    # the organization that holds the project
    publisher = models.ForeignKey(_('Publisher'), Publisher)
    # projects are the documents :) TODO: update this at import time
    projects = models.ManyToMany(_('Projects'), Project)

    active = models.BooleanField(_('Active'), default=False)

    def __str__(self):
        return self.name
