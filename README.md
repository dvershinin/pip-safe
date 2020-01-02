## pip-safe

`pip-safe` is the *safe* and easy pip package manager for command-line Python apps.

    pip-safe install lastversion
    lastversion kernel
    
### Why

Using `pip install ...` outside virtualenv can simply break your system.
So many tutorials out there blindly recommend that without any note of having to use virtualenvs,
and so many people *do* just run that without any knowledge of *what* virtualenv is.

If you run an OS which distributes Python package via RPM, apt, etc. you *will* break your system
sooner or later, if you keep using `pip` as root/sudo.

You either package required Python-base software yourself, or use virtualenv for each 
non-packaged Python software you intend to use. Everything else is a risk of breakage.

`pip-safe` is here to make it *very easy* to install stuff from PyPi
without having to package it.

## Installation    

### Pre-Requisites

Configure your `PATH` to execute stuff from `~/.local/bin` and `/usr/local/bin`.

Place `export PATH=$PATH:$HOME/.local/bin:/usr/local/bin` in your `~/.bashrc` 
then run `source ~/.bashrc` to apply to current shell. 

### CentOS/RHEL  7, 8 (pending)

    sudo yum install https://extras.getpagespeed.com/release-el$(rpm -E %{rhel})-latest.rpm
    sudo yum install pip-safe
    
### Other systems

    mkdir -p ~/.virtualenvs
    
Ensure `virtualenv-3` is installed, then:

    virtualenv-3 ~/.virtualenvs/pip-safe
    ~/.virtualenvs/pip-safe/bin/pip install pip-safe
    ln -s $HOME/.virtualenvs/pip-safe/bin/pip-safe $HOME/.local/bin/pip-safe

## Usage

### Installing a program

    pip-safe install <name>
    
### Removing a program

    pip-safe remove <name>
    
### Listing installed packages

    pip-safe list    

With `pip-safe`, you can easily install command line programs from PyPi,
while not worrying about breaking your system.

## How

it installs each program into its own virtualenv, and symlinks whichever
executables it has over to ~/.local/bin/

It is that easy and I don't know why nobody did this before.


### Helpful stuff used while creating pip-safe

* [Invoking virtualenv from Python](http://jelly.codes/articles/python-virtualenv-from-within-python/)
