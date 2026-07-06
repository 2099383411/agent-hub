from setuptools import setup, find_packages

setup(
    name="agent-hub-sdk",
    version="0.1.0",
    description="Agent Hub Python SDK - 智能体中台 Agent 接入库",
    packages=find_packages(),
    install_requires=["httpx>=0.28.0", "pydantic>=2.7.0"],
    python_requires=">=3.10",
)
