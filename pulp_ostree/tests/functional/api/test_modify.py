import shutil
import unittest

from urllib.parse import urlparse, urljoin

from requests.exceptions import HTTPError

from pulp_smash import config, api
from pulp_smash.pulp3.bindings import delete_orphans, monitor_task
from pulp_smash.pulp3.utils import gen_repo, modify_repo, gen_distribution

from pulpcore.client.pulp_ostree import (
    DistributionsOstreeApi,
    OstreeOstreeDistribution,
    ContentCommitsApi,
    ContentObjectsApi,
    ContentRefsApi,
    RepositorySyncURL,
    RemotesOstreeApi,
    RepositoriesOstreeApi,
    RepositoriesOstreeVersionsApi,
)

from pulp_ostree.tests.functional.utils import (
    gen_ostree_client,
    gen_ostree_remote,
    init_local_repo_with_remote,
    validate_repo_integrity,
)


class ModifyRepositoryTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize class-wide variables."""
        cls.cfg = config.get_config()
        cls.registry_name = urlparse(cls.cfg.get_base_url()).netloc
        cls.client = api.Client(cls.cfg, api.json_handler)

        client_api = gen_ostree_client()
        cls.repositories_api = RepositoriesOstreeApi(client_api)
        cls.versions_api = RepositoriesOstreeVersionsApi(client_api)
        cls.distributions_api = DistributionsOstreeApi(client_api)
        cls.commits_api = ContentCommitsApi(client_api)
        cls.objs_api = ContentObjectsApi(client_api)
        cls.remotes_api = RemotesOstreeApi(client_api)
        cls.refs_api = ContentRefsApi(client_api)

    @classmethod
    def tearDownClass(cls):
        """Clean orphaned content after finishing the tests."""
        delete_orphans()

    def setUp(self):
        """Clean orphaned content before each test and initialize repositories."""
        delete_orphans()

        self.repo1 = self.repositories_api.create(gen_repo())
        #self.addCleanup(self.repositories_api.delete, self.repo1.pulp_href)

        body = gen_ostree_remote(depth=0, policy="immediate")
        self.remote = self.remotes_api.create(body)
        #self.addCleanup(self.remotes_api.delete, self.remote.pulp_href)

        self.assertEqual(self.repo1.latest_version_href, f"{self.repo1.pulp_href}versions/0/")
        repository_sync_data = RepositorySyncURL(remote=self.remote.pulp_href)
        response = self.repositories_api.sync(self.repo1.pulp_href, repository_sync_data)
        repo_version_href = monitor_task(response.task).created_resources[0]

        self.repo_version1 = self.versions_api.read(repo_version_href)

        self.repo2 = self.repositories_api.create(gen_repo())
        #self.addCleanup(self.repositories_api.delete, self.repo2.pulp_href)

    def test_add_commit_and_ref(self):
        """Copy one commit and one ref from an existing repository."""
        created_refs = self.refs_api.list(repository_version_added=self.repo_version1.pulp_href)
        ref = self.refs_api.read(created_refs.to_dict()["results"][0]["pulp_href"])
        latest_commit = self.commits_api.read(ref.commit)

        modify_repo(
            self.cfg, self.repo2.to_dict(), add_units=[ref.to_dict(), latest_commit.to_dict()]
        )

        distribution_data = OstreeOstreeDistribution(
            **gen_distribution(repository=self.repo2.pulp_href)
        )
        response = self.distributions_api.create(distribution_data)
        distribution = monitor_task(response.task).created_resources[0]
        #self.addCleanup(self.distributions_api.delete, distribution)

        ostree_repo_path = urljoin(
            self.distributions_api.read(distribution).base_url, self.remote.name
        )

        init_local_repo_with_remote(self.remote.name, ostree_repo_path)
        self.addCleanup(shutil.rmtree, self.remote.name)
        validate_repo_integrity(
            self.remote.name, f"pulpos:{ref.name}", commits_to_check={latest_commit.checksum}
        )

    '''
    def test_add_refs_commits(self):
        """Copy multiple refs and commits at once."""
        pass

    def test_copy_whole_repository(self):
        """Initialize a new repository from an existing repository."""
        pass

    def test_remove_commits_and_refs(self):
        """Remove multiple refs and commits at once."""
        pass

    def test_add_remove_obj(self):
        """Try to add/remove an object (e.g., dirtree, dirmeta, ...) from an existing repository."""
        created_objs = self.objs_api.list(repository_version_added=self.repo_version1.pulp_href)
        obj = created_objs.to_dict()["results"][0]

        with self.assertRaises(HTTPError):
            modify_repo(self.cfg, self.repo1.to_dict(), add_units=[obj])

        with self.assertRaises(HTTPError):
            modify_repo(self.cfg, self.repo1.to_dict(), remove_units=[obj])
    '''
