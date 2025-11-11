from setuptools import setup

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='PLVision',
    url='https://github.com/Dani01UNIPlovdiv/23615_LinuxCNC_UI',
    author='AtD',
    author_email='',
    # Needed to actually package something
    packages=['PLVision'],
    # Needed for dependencies
    install_requires=['numpy','opencv-python'],
    # *strongly* suggested for sharing
    version='0.1',
    # The license can be anything you like
    license='MIT',
    description='An SocketRequestSender of a python package from pre-existing code',
    # We will also need a readme eventually (there will be a warning)
    # long_description=open('README.txt').read(),
)