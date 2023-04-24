from distutils.core import setup

setup(name='server_state_dashboard',
      version='1.0.0',
      description='Webserver that displays and monitors the state of ip by pinging them.',
      author='Phillip Thomas',
      install_requires=[
          "pandas",
          "nicegui"
      ],
      # entry_points={"console_scripts": ["server_state_dashboard=server_state_dashboard.dashboard"]},
)
