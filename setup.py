import setuptools


packages = setuptools.find_namespace_packages(
    include=[
        'twecs.*',
    ],
)

setuptools.setup(
    install_requires=[
        'requests == 2.25.1',
    ],
    name='twecs.wise',
    packages=packages,
    python_requires='>= 3.8',
    version='0.1',
    zip_safe=False, # due to namespace package
)
