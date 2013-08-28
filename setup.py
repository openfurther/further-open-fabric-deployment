# Copyright (C) [2013] [The FURTHeR Project]
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import distribute_setup
distribute_setup.use_setuptools()
from setuptools import setup, find_packages

setup(
    name = "further-deployment",
    version = "0.1",
    packages = find_packages(),
    install_requires=['fabric>=1.6.0'],
    # metadata for upload to PyPI
    author = "Dustin Schultz",
    author_email = "dustin.schultz@utah.edu",
    description = "Reusable FURTHeR Deployment functions",
    license = "Apache License 2.0",
    keywords = "FURTHeR Project"
)
