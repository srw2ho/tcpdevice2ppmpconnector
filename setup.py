import os
import setuptools

NAME = "tcpdevice2ppmpconnector"

DEPENDENCIES_ARTIFACTORY = []

DEPENDENCIES_SOCIALCODING = {
    # "https://sourcecode.socialcoding.bosch.com/scm/mh_ees1/mhopcua.git": "",
    "https://sourcecode.socialcoding.bosch.com/scm/mh_ees1/ppmp.git": "",
    # "https://sourcecode.socialcoding.bosch.com/scm/mh_ees1/permitverify.git": "",
    "https://sourcecode.socialcoding.bosch.com/scm/mh_ees1/config.git": "",
}


def generate_pip_links_from_url(url, version):
    """ Generate pip compatible links from Socialcoding clone URLs

    Arguments:
        url {str} -- Clone URL from Socialcoding
    """
    package = url.split('/')[-1].split('.')[0]
    url = url.replace("https://", f"{package} @ git+https://")
    if version:
        url = url + f"@{version}"

    return url

# create pip compatible links
DEPENDENCIES_SOCIALCODING = [generate_pip_links_from_url(url, version) for url, version in DEPENDENCIES_SOCIALCODING.items()]
DEPENDENCIES = DEPENDENCIES_ARTIFACTORY + DEPENDENCIES_SOCIALCODING

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setuptools.setup(
    name=NAME,
    version_format='{tag}.dev{commitcount}+{gitsha}',
    author="srw2ho",
    author_email="",
    description="",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    package_data={},
    install_requires=DEPENDENCIES,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License"
        "Operating System :: OS Independent",
    ],
)
