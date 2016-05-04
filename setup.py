#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = "marketwebsocket",
    version = "0.0.1",
    description = "websocket support for tos market",
    long_description = "websocket support for tos market",
    license = "MIT Licence",

    url = "http://172.16.1.41:10080/yizhen.fan/market-websocket",
    author = "yizhen.fan",
    author_email = "yizhen.fan@transwarp.io",

    packages = find_packages(),
    include_package_data = True,
    zip_safe = True,
    install_requires = ['setuptools', 'six']
)