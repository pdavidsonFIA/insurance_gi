import setuptools
#from os import listdir

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as f:
    dependencies = f.read().splitlines()

setuptools.setup(
    name="insurance_gi",
    version="0.0.3",
    author="Peter Davidson",
    author_email="peterjd41@gmail.com",
    description="GI projection tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pdavidsonFIA/insurance_gi",
    project_urls={
        "Bug Tracker": "https://github.com/pdavidsonFIA/insurance_gi/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Financial and Insurance Industry"
    ],
    packages=setuptools.find_packages(include=['insurance_gi', 'insurance_gi.*']),
    python_requires='>=3.6',
    include_package_data=True,
    install_requires=dependencies,
)
