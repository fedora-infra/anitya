# -*- coding: utf-8 -*-
"""sourceforge_git"""

from bs4 import BeautifulSoup

from anitya.lib.backends import REQUEST_HEADERS, BaseBackend, http_session
from anitya.lib.exceptions import AnityaPluginException


class SourceforgeGitBackend(BaseBackend):
    """The custom class for projects hosted on sourceforge.net
    that use git tags.

    This backend allows to specify a version_url that will
    be used to retrieve the git tags. Otherwise it tries to guess
    the version_url from sourceforge.net homepage of the project or
    project name.
    """

    name = "Sourceforge (git)"
    default_version_scheme = "RPM"
    is_repo = True
    examples = [
        "https://sourceforge.net/p/ubuntuzilla/ubuntuzilla/ref/master/tags/",
        "https://sourceforge.net/p/flightgear/flightgear/ref/next/tags/",
        "https://sourceforge.net/p/eclipse-cs/git/ref/master/tags/",
    ]

    prefix = "https://sourceforge.net/p/"
    suffix = "/ref/master/tags/"

    @classmethod
    def get_version_url(cls, project):
        """Method called to retrieve the url used to check for new version
        of the project provided, project that relies on the backend of this plugin.

        :arg Project project: project (:obj:`anitya.db.models.Project`):
        Project object whose backend corresponds to the current plugin.

        :Returns: str: url used for version checking
        """

        namespace = repo = url = ""

        if project.version_url:
            version_url = project.version_url.replace("+", r"\+")
            url = (
                version_url
                if version_url.startswith((cls.prefix, "http://sourceforge.net/p/"))
                else f"{cls.prefix}{version_url}/git{cls.suffix}"
            )

        else:
            namespace, repo = cls.get_namespace_repo(project)
            url = f"https://sourceforge.net/p/{namespace}/{repo}/ref/master/tags/"  # noqa: E231

        return url

    @classmethod
    def get_namespace_repo(cls, project):
        """Method called to retrieve namespace and repo.
        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
            corresponds to the current plugin.
        :return: string namespace and string repo
        :return type: two strings
        """

        namespace = repo = ""
        raw_url = ""

        if project.version_url:
            raw_url = project.version_url
        elif project.homepage:
            raw_url = project.homepage

        url_path = ""
        for pfx in (
            cls.prefix,
            "http://sourceforge.net/p/",
            "sourceforge.net/p/",
        ):
            if raw_url.startswith(pfx):
                url_path = raw_url[len(pfx) :]
                break

        if url_path:
            clean = url_path.split("?")[0].split("#")[0].strip("/")
            for subpath in ("/ci/", "/ref/"):
                if subpath in clean:
                    clean = clean.split(subpath)[0].strip("/")
            parts = [p for p in clean.split("/") if p]
            if len(parts) >= 2:
                namespace = parts[0]
                repo = parts[1]
            elif len(parts) == 1:
                namespace = parts[0]
                repo = "git"

        if not namespace:
            namespace = project.name if project.name else ""

        namespace = namespace.replace("+", r"\+")
        repo = "git" if repo in ["", "ci"] else repo

        return namespace, repo

    @classmethod
    def get_versions(cls, project):
        """Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        """
        namespace, repo = cls.get_namespace_repo(project)
        url = project.get_version_url()
        git_tag_request = http_session.get(
            url, headers=REQUEST_HEADERS, timeout=60, verify=True
        )  # pylint: disable=W3101

        if git_tag_request.status_code == 404:
            raise AnityaPluginException(
                f'Could not call : "{url}" of "{project.name}", with error: '
                f"{git_tag_request.status_code}"
            )

        soup = BeautifulSoup(git_tag_request.content, "html.parser")

        def is_release_tag_link(tag):
            link_prefix = f"/p/{namespace}/{repo}/ci/"
            return (
                tag.has_attr("href")
                and tag.attrs["href"].startswith(link_prefix)
                and len(tag.contents) == 1
            )

        release_tags = []

        for release_tag in soup.find_all(is_release_tag_link):
            release_tag_text = release_tag.contents[0]
            release_tags.append(release_tag_text)

        return release_tags

    @classmethod
    def is_url_valid(cls, url: str) -> bool:
        """
        Used to recognize if the URL is valid for the backend.

        Attributes:
            url (str): URL to check

        Returns:
            True if the URL is valid or false.
        """
        return url.startswith(
            (
                "https://sourceforge.net/p/",
                "http://sourceforge.net/p/",
            )
        ) or (
            not url.startswith(("http://", "https://"))
            and url.startswith("sourceforge.net/p/")
        )

    @classmethod
    def parse_url(cls, url: str) -> dict:
        """
        Parse url to obtain project related data.

        Attributes:
            url (str): URL to check

        Returns:
            Dictionary containing project related data.

        Raises:
            AnityaPluginException: If URL cannot be parsed into a valid project.
        """
        orig_url = url
        if not cls.is_url_valid(orig_url):
            raise AnityaPluginException(
                f"Could not extract project name from {orig_url}"
            )

        clean = orig_url.split("?")[0].split("#")[0].rstrip("/")
        path_clean = clean
        if "/ref/" in path_clean:
            path_clean = path_clean.split("/ref/")[0]
        if "/ci/" in path_clean:
            path_clean = path_clean.split("/ci/")[0]
        for subpath in ("/tree", "/log", "/commit", "/tags"):
            if subpath in path_clean:
                path_clean = path_clean.split(subpath)[0]

        for pfx in (
            "https://sourceforge.net/p/",
            "http://sourceforge.net/p/",
            "sourceforge.net/p/",
            "https://sourceforge.net/p",
            "http://sourceforge.net/p",
            "sourceforge.net/p",
        ):
            if path_clean.startswith(pfx):
                path_clean = path_clean[len(pfx) :]
                break

        parts = [x for x in path_clean.strip("/").split("/") if x]
        if not parts:
            raise AnityaPluginException(
                f"Could not extract project name from {orig_url}"
            )

        if parts[-1] == "git" and len(parts) > 1:
            name = parts[0]
        else:
            name = parts[-1]

        version_url = (
            orig_url
            if "/git/" not in orig_url and (len(parts) == 1 or parts[1] != "git")
            else name
        )
        version_scheme = cls.default_version_scheme
        backend = cls.name
        return {
            "name": name,
            "homepage": orig_url,
            "backend": backend,
            "version_url": version_url,
            "version_scheme": version_scheme,
        }

    @classmethod
    def check_feed(cls):  # pragma: no cover
        """Method called to retrieve the latest uploads to a given backend,
        via, for example, RSS or an API.

        Not Supported

        Returns:
            :obj:`list`: A list of 4-tuples, containing the project name, homepage, the
            backend, and the version.

        Raises:
             NotImplementedError: If backend does not
                support batch updates.

        """
        raise NotImplementedError()
