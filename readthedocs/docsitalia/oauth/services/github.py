from __future__ import absolute_import
from builtins import str
import logging
import json
import re

from django.conf import settings

from readthedocs.oauth.services.github import GitHubService
from readthedocs.oauth.models import RemoteOrganization, RemoteRepository
from readthedocs.restapi.client import api

from ..models import Publisher, parse_metadata_repo, create_projects_from_metadata

log = logging.getLogger(__name__)


class DocsItaliaGithubService(GitHubService):
    def sync(self):
        """Sync organizations."""
        self.sync_organizations()

    def sync_organizations(self):
        """Sync organizations from GitHub API."""
        try:
            orgs = self.paginate('https://api.github.com/user/orgs')
            for org in orgs:
                org_resp = self.get_session().get(org['url'])
                org_obj = self.create_organization(org_resp.json())

                # we ingest only whitelisted organizations
                if not org_obj:
                    continue

                publisher = Publisher.objects.get(organizations=org_obj, active=True)
                metadata_repo = self.paginate(
                    'https://api.github.com/repos/{org_login}/{docs_italia_conf}'.format(
                        org_login=org_object.slug,
                        docs_italia_conf=publisher.config_repo_name
                    )
                )

                # no metadata no party
                if not metadata_repo:
                    log.debug('Syncing GitHub organizations: no metadata repo for {}'.format(publisher))
                    continue

                metadata = parse_metadata_repo(metadata_repo)
                publisher.metadata = metadata
                publisher.save()
                create_projects_from_metadata(metadata)

                # Add repos
                # TODO ?per_page=100
                org_repos = self.paginate(
                    '{org_url}/repos'.format(org_url=org['url'])
                )

                for repo in org_repos:
                    self.create_repository(repo, organization=org_obj)

                # TODO: set active=False for projects that are not whitelisted anymore
        except (TypeError, ValueError) as e:
            log.error('Error syncing GitHub organizations: %s',
                      str(e), exc_info=True)
            raise Exception('Could not sync your GitHub organizations, '
                            'try reconnecting your account')

    def create_organization(self, fields):
        """
        Update or create remote organization from GitHub API response.

        :param fields: dictionary response of data from API
        :rtype: Publisher
        """
        # TODO: is this the right one?
        name = fields.get('name')
        try:
             publisher = Publisher.objects.get(
                 name=name,
                 active=True)
        except Publisher.DoesNotExist:
             return None

        try:
            organization = RemoteOrganization.objects.get(
                slug=fields.get('login'),
                users=self.user,
                account=self.account,
            )
        except RemoteOrganization.DoesNotExist:
            # TODO: fun fact: slug is not unique
            organization = RemoteOrganization.objects.create(
                slug=fields.get('login'),
                account=self.account,
            )
            organization.users.add(self.user)

        publisher.organizations.add(organization)

        organization.url = fields.get('html_url')
        organization.name = name
        organization.email = fields.get('email')
        organization.avatar_url = fields.get('avatar_url')
        if not organization.avatar_url:
            organization.avatar_url = self.default_org_avatar_url
        organization.json = json.dumps(fields)
        organization.account = self.account
        organization.save()

        return organization
