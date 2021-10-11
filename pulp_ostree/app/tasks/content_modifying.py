from collections import namedtuple

from django.db.models import Q

from pulpcore.plugin.models import Repository, RepositoryVersion, Content

from pulp_ostree.app.models import (
    OstreeCommit,
    OstreeConfig,
    OstreeObject,
    OstreeRef,
    OstreeSummary,
)

ModifyContentData = namedtuple("ModifyContentData", "to_add, to_remove")


def modify_content(repository_pk, add_content_units, remove_content_units, base_version_pk=None):
    """TODO."""
    repository = Repository.objects.get(pk=repository_pk).cast()

    summary_data = get_content_data_by_model(OstreeSummary, add_content_units, remove_content_units)
    config_data = get_content_data_by_model(OstreeConfig, add_content_units, remove_content_units)

    commit_data = get_content_data_by_model(OstreeCommit, add_content_units, remove_content_units)
    ref_data = get_content_data_by_model(OstreeRef, add_content_units, remove_content_units)

    content_to_add = recursively_get_content_to_add(commit_data.to_add, ref_data.to_add)
    content_to_remove = recursively_get_content_to_remove(commit_data.to_remove, ref_data.to_remove)

    # TODO: decide whether to add support for specifying the depth for parent commits referenced
    #   by a specific ref (currently we go only for the first commit)

    if base_version_pk:
        base_version = RepositoryVersion.objects.get(pk=base_version_pk)
    else:
        base_version = None

    # TODO: handle the '*' wildcard

    with repository.new_version(base_version=base_version) as new_version:
        new_version.remove_content(content_to_remove)
        new_version.remove_content(summary_data.to_remove)
        new_version.remove_content(config_data.to_remove)
        new_version.add_content(content_to_add)
        new_version.add_content(summary_data.to_add)
        new_version.add_content(config_data.to_add)


def get_content_data_by_model(model_type, add_content_units, remove_content_units):
    """TODO."""
    to_add = model_type.objects.filter(pk__in=add_content_units)
    to_remove = model_type.objects.filter(pk__in=remove_content_units)
    return ModifyContentData(to_add, to_remove)


def recursively_get_content_to_add(commit_data, ref_data):
    """TODO."""
    ref_commits_pks = ref_data.values_list("commit", flat=True)

    commit_data = commit_data.union(OstreeCommit.objects.filter(pk__in=ref_commits_pks))
    commit_data_pks = commit_data.values_list("pk", flat=True)
    objects = OstreeObject.objects.filter(commit__in=commit_data_pks)

    return Content.objects.filter(
        Q(pk__in=commit_data_pks) | Q(pk__in=ref_data) | Q(pk__in=objects)
    )


def recursively_get_content_to_remove(commit_data, ref_data):
    """TODO."""
    objects = []
    return objects
