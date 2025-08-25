from setuptools import setup, find_packages

setup(
    name="flowdepot",
    version="2025.6.8.2343",
    packages=find_packages(),  # 掃描根目錄
    include_package_data=True,
    install_requires=[
        # 在這裡加入依賴，例如：
        # "paho-mqtt>=1.6.1",
        # "pyyaml>=6.0",
    ],
    entry_points={
        # 如需指令列工具：
        # 'console_scripts': [
        #     'flowdepot=agents.main:main',
        # ],
    },
    python_requires='>=3.11',
)
