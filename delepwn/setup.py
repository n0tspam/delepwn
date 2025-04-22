from setuptools import setup, find_packages

setup(
    name="delepwn",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "google-auth>=2.0.0",
        "google-auth-oauthlib>=1.0.0",
        "google-auth-httplib2>=0.1.0",
        "google-api-python-client>=2.0.0",
        "pyyaml>=6.0.0",
        "requests>=2.0.0",
        "colorama>=0.4.6",
        "tqdm>=4.65.0",
    ],
    entry_points={
        "console_scripts": [
            "delepwn=delepwn.main:main",
        ],
    },
    python_requires=">=3.8",
) 