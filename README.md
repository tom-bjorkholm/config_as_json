# config-as-json

> **👤 Looking to use this in your program**  
> This repository is for developers of the package. If you want to install
> and use `config-as-json` including writing programs that use them, please visit
> the **PyPI project page [https://pypi.org/project/config-as-json](https://pypi.org/project/config-as-json)
> for installation instructions and user documentation.

## What is it

The `config-as-json` package provides a base class Config with functionality to read all member variables of a derived class object from a JSON file with helpful error messages to user who created the config file. It provides also functionality to write all member variables of derived class object to a JSON file.

## For developers

### Cloning

The version-reporter repo uses submodules. To clone it use the command:

````sh
git clone --recurse-submodules git@bitbucket.org:tom-bjorkholm/version-reporter.git
````

If you forgot to include the `--recurse-submodules` in your `git clone` command
you can fix it later with the command:

````sh
git submodule update --init --recursive 
````

To update the version of thr submodule repo that you see in the main repo use the command:

````sh
git submodule update --remote --merge
````

### Needed environment

#### OS

For running the script and running the test suite you need a mac or a Linux computer.
Even if the resulting package can be installed and used on Windows, the scripts for
building and testing are only implemented for mac and Linux.

#### Python version

Please see README_pypi.md for information on needed python version.
Main development is on newest Python version.

### Quick start

1. Clone this repository
2. Run `./run_setup_build_environment.py` to set up the build environment
3. Run `./run_build.py`  to build and test the package

### Building application

There are 3 main scripts (and 2 extra convinience scripts) for building the application:

- `run_setup_build_environment.py` Run this script first to get the
  environment set up for building.
- `run_build.py` Run this script to build an installation package (.whl) and
  to run the tests on it in a venv (virtual environment).
- `run_clean.py` Deletes all files that was produced by the build to start
  over from a clean state.
- `run_clean_build.py` Combines the use of `run_clean.py`,
  `run_setup_build_environment.py` and `run_build.py` into one script.
  Pylint discover some duplicate code warnings only on a clean build so this
  is useful.
- `run_pypi_build.py` Builds for PyPI upload and can do the upload too.

The "testing" includes pytest, pylint, flake8 and mypy.

After running `run_build.py` you can open `reports/index.html` to see all test
reports.

### More build system information

The file `./common_build_tools/README.md` (in git submodule - see above) contains more
information about the build system. This README can also be viewed at
[https://bitbucket.org/tom-bjorkholm/common_build_tools/src/master/README.md](https://bitbucket.org/tom-bjorkholm/common_build_tools/src/master/README.md)

## Test summary

- Test result: 1 warning, 1 error in 2s
- No flake8 warnings.
- mypy errors.
- Built version(s): 0.0.1
- Build and test using Python 3.14.3
