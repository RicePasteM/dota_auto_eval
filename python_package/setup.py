from setuptools import setup, find_packages

setup(
    name="dota_auto_eval",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "python-dateutil>=2.8.0"
    ],
    author="DOTA Auto Eval Team",
    author_email="",
    description="DOTA自动评估客户端",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
) 