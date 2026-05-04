from setuptools import find_packages, setup

package_name = 'cop_sim_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
        'coppeliasim-zmqremoteapi-client',
    ],
    zip_safe=True,
    maintainer='icaro-adriano',
    maintainer_email='icaro.adriano.s.m@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "coppelia_com_node = cop_sim_pkg.coppelia_com_node:main",
            "control_node = cop_sim_pkg.controler:main",
            "input_node = cop_sim_pkg.input:main",
        ],
    },
)
