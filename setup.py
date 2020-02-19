from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(name='slackbot-cloudgenix',
      version='0.5.0b2',
      description='CloudGenix AppFabric plugin functions for lins05/slackbot.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/ebob9/slackbot-cloudgenix',
      author='Aaron Edwards',
      author_email='cloudgenix-slackbot@ebob9.com',
      license='MIT',
      install_requires=[
            'cloudgenix >= 5.2.1b1, < 5.3.1b1',
            'cloudgenix_idname >= 2.0.0',
            'slackbot',
            'tabulate',
            'idna',
            'fuzzywuzzy',
            'pandas'
      ],
      packages=['slackbot_cloudgenix'],
      classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8"
      ]
      )
