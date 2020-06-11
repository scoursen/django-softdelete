from setuptools import setup, find_packages

setup(name='django-softdelete',
      version='0.9.1',
      description='Soft delete support for Django ORM, with undelete.',
      author='Steve Coursen',
      author_email='smcoursen@gmail.com',
      maintainer='Steve Coursen',
      maintainer_email='smcoursen@gmail.com',
      license="BSD",
      zip_safe=True,
      url="https://github.com/scoursen/django-softdelete",
      packages=find_packages(),
      install_requires=['setuptools', 'six'],
      include_package_data=True,
      setup_requires=['setuptools_hg',],
      classifiers=[
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Environment :: Web Environment',
        ]
)
