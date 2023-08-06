# Requirements CLI

This is a command line application designed to manage `requirements.txt` files in a Python project, particularly useful for monorepo style projects. It provides functionalities to add, update, remove, and view packages in `requirements.txt` files over specified path(s) in a monorepo style project.

## Features

- **Add**: Add a new package to `requirements.txt` files.
- **Find**: Find a package from `requirements.txt` files.
- **Update**: Update an existing package in `requirements.txt` files to a new version.
- **Remove**: Remove a package from `requirements.txt` files.
- **Cat**: View the contents of `requirements.txt` files.

## Installation

This project uses Python 3.12. Make sure you have the correct version installed. Clone the repository and install the project:

```bash
git clone https://github.com/CaptainDriftwood/requirements.git
cd requirements
pip install ./
```

To install the project via GitHub:

```bash
pip install git+https://github.com/CaptainDriftwood/requirements.git
```

## Usage

### Output contents of `requirements.txt` files

```bash
requirements cat
```
outputs the contents of `requirements.txt` files in the current and all subdirectories.


### Find a `requirements.txt` file that contains a specific package name

```bash
requirements find <package_name>
```

### Add a package to `requirements.txt` files

```bash
requirements add <package_name>
```
