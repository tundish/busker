Busker
======

Busker is a utility for testing [Balladeer](https://tundish.github.io/balladeer) projects.

It provides a graphical interface for interaction with a Balladeer host.

Busker also allows you to self-host the Balladeer application, simplifying the steps required:
+ Creating a Python virtual environment.
+ Installing the Balladeer package along with its dependencies.
+ Running the Balladeer server.

Operation
---------

* Busker works on Windows and UNIX systems.
* Python 3.11 or later is required.
* No installation is necessary. Simply run from the command line.

```
python3 -m busker.main --help

usage: busker.main [-h] [--with-automation] [--config CONFIG] [--url URL] [--number NUMBER]

options:
  -h, --help         show this help message and exit

Display:
  --with-automation  Show Automation tab in GUI [False].

Automation:
  --config CONFIG    Set a path to a configuration file [/home/user/busker.toml].
  --url URL          Set url path to begin session.
  --number NUMBER    Set the number of times to run the plugin.

```
