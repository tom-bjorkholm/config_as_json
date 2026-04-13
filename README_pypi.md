# config-as-json

## What is it

The `config-as-json` package provides a base class Config with functionality to read all member variables of a derived class object from a JSON file with helpful error messages to user who created the config file. It provides also functionality to write all member variables of derived class object to a JSON file.

## Installing config-as-json

### Installing config-as-json on mac and Linux

````sh
pip3 install --upgrade config-as-json
````

### Installing config-as-json on Microsoft Windows

````sh
pip install --upgrade config-as-json
````


## Example programs (to be created)

The best way to learn to use this package is to use the provided
example programs:
[https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/README.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/example/src/example/README.md).

## API documentation

You can find the public API documentation at [https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/doc/api.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/doc/api.md)

You can find the protected API documentation at [https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/doc/protected_api.md](https://bitbucket.org/tom-bjorkholm/config_as_json/src/master/doc/protected_api.md)

Even though the API documentation exists, most users and programmers probably
get a better start by reading the examples.

## Version history

| Version | Date        | Python version | Comment                     |
|---------|-------------|----------------|-----------------------------|
| 0.1     | ? soon ?    | 3.12 or newer  | First released version      |

## Test summary

- Test result: 1 warning, 1 error in 2s
- No flake8 warnings.
- mypy errors.
- Built version(s): 0.0.1
- Build and test using Python 3.14.3
