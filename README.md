## pip-safe

`pip-safe` is the *safe* and easy pip package manager for command-line apps from PyPi.

    pip-safe install lastversion
    lastversion linux
    
### Why

Using `pip install ...` outside virtualenv [can simply break your system](https://www.getpagespeed.com/server-setup/do-not-run-pip-as-root).
So many tutorials out there blindly recommend that without any note of having to use virtualenvs,
and so many people *do* just run that without any knowledge of *what* a virtualenv is.

If you run an OS which distributes Python packages via `yum`, `apt`, etc. you *will* break your 
system sooner or later, if you keep using `pip` as root or sudo.

You either have to package the Python-based program yourself, or have to use a virtualenv for 
installing it. Everything else is a risk of breakage.

`pip-safe` is here to make it *very easy* to install command-line apps from PyPi without having to 
package anything.

## Installation    

### Pre-Requisites

Configure your `PATH` to execute stuff from `~/.local/bin` and `/usr/local/bin`.

Place `export PATH=$PATH:$HOME/.local/bin:/usr/local/bin` in your `~/.bashrc` 
then run `source ~/.bashrc` to apply to current shell. 

### CentOS/RHEL  7, 8

    sudo yum install https://extras.getpagespeed.com/release-latest.rpm
    sudo yum install pip-safe
    
Using `pip-safe` command installs stuff using Python 3.

You can additionally `yum install pip2-safe` to have `pip2-safe` 
(would be required for installing apps which support only Python 2).
    
### Other systems

#### Install `pip-safe` for current user

If you install `pip-safe` using this method, you can only install packages for current user,
but this method does not require root. 

Ensure `virtualenv-3` is installed and `~/.local/bin` is in your `PATH`, then: 
   
    mkdir -p ~/.virtualenvs
    virtualenv-3 ~/.virtualenvs/pip-safe
    ~/.virtualenvs/pip-safe/bin/pip install pip-safe
    ln -s $HOME/.virtualenvs/pip-safe/bin/pip-safe $HOME/.local/bin/pip-safe

#### System-wide installation of `pip-safe`    

When `pip-safe` is installed system-wide, you can install both system-wide and user packages with it.
    
Ensure `virtualenv-3` is installed and `/usr/local/bin` is in your `PATH`, then:

    mkdir -p /opt/pip-safe
    virtualenv-3 /opt/pip-safe/pip-safe
    /opt/pip-safe/pip-safe/bin/pip install pip-safe
    ln -s /opt/pip-safe/pip-safe/bin/pip-safe /usr/local/bin/pip-safe



## Usage

``` 
usage: pip-safe [-h] [-v] [-y] [--system] <command> [package-name]

positional arguments:
  <command>
  package-name

optional arguments:
  -h, --help       show this help message and exit
  -v, --verbose
  -y, --assumeyes
  --system
```

### Installing a program

    pip-safe install <name>
    
To see what's going on under the hood, pass `--verbose` flag. 

There is limited support for installing directly from Git URLs, e.g.:

    pip-safe install git+https://github.com/dvershinin/lastversion.git 

#### Global installation

By default, programs are installed to `~/.local/bin/<package>` (for current user).
For a system-wide installation, use `--system`:

    sudo pip-safe install --system lastversion  
    
This installs a package to `/opt/pip-safe/<package>` and symlinks its executable to `/usr/local/bin`,
so it's still safe :-)    
    
### Removing a program

    pip-safe remove <name>
    
### Listing installed packages

    pip-safe list    

With `pip-safe`, you can easily install command line programs from PyPi,
while not worrying about breaking your system.

## How

it installs each program into its own virtualenv, and symlinks whichever
executables it has over to `~/.local/bin/`

It is that easy and I don't know why nobody did this before.

## Caveats

* Only pure Python apps will work absolutely reliably, because others might require *system* libraries
and we can't decipher what are those
* Tested only with Python 3.6

### Helpful stuff used while creating pip-safe

* [Invoking virtualenv from Python](http://jelly.codes/articles/python-virtualenv-from-within-python/)
