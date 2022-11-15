from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in feeds/__init__.py
from feeds import __version__ as version

setup(
	name="feeds",
	version=version,
	description="Frappe App for Animal Feeds",
	author="254 ERP",
	author_email="254businessservices@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
