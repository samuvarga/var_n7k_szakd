from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'var_n7k_szakd'

robot_description_files = []
for root, _, filenames in os.walk('robot_description'):
    relative_root = os.path.relpath(root, 'robot_description')
    target_root = os.path.join('share', package_name, 'robot_description')
    if relative_root != '.':
        target_root = os.path.join(target_root, relative_root)
    files_in_root = [os.path.join(root, filename) for filename in filenames]
    if files_in_root:
        robot_description_files.append((target_root, files_in_root))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'world'), glob('world/*')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),
        *robot_description_files,
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='todo',
    maintainer_email='todo@todo.com',
    description='TODO: Package description',
    license='GNU General Public License v3.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # 'control_vehicle = var_n7k_szakd.control_vehicle:main',
        ],
    },
)
