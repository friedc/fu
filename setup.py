def configuration(parent_package = '', top_path = None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('fu-10Aug2015', parent_package, top_path)
    config.add_extension('fortlib', ['Source/f77/fortlib.f'])
    config.add_extension('fmopdb', ['Source/f77/fmopdb.f', 'Source/f77/fmopdb_sub.f'])
    config.add_extension('fucubelib', ['Source/f90/fucubelib.f90'])
    config.add_data_files(('Scripts','Scripts'))
    config.add_data_files(('Tools','Tools'))
    return config

def setup_package():
    from numpy.distutils.core import setup
    import __version__
    metadata = dict(
        version = __version__.__version__,
        author = __version__.__author__,
        maintainer = __version__.__author__,
        license = __version__.__license__,
        configuration = configuration,
    )
    setup(**metadata)

if __name__ == '__main__':
    setup_package()
