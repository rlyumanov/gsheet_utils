from setuptools import setup, find_packages

# Читаем описание из README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gsheet_utils",
    version="0.1.3",
    author="r.lyumanov",
    author_email="rlyumanov@gmail.com",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rlyumanov/data-utils",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.12",
    install_requires=[                          
        "google-api-core==2.25.1",
        "google-api-python-client==2.179.0",
        "google-auth==2.40.3",
        "google-auth-httplib2==0.2.0",
        "googleapis-common-protos==1.70.0"
    ],

    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.6.0",
            "pytest-cov>=4.0.0",
            "moto>=4.0.0",
            "black",
            "flake8",
        ]
    },
)