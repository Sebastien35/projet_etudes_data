# To work on this project :
## Regarding dependencies:

### Necessary dependencies :
- Python 3.12
- Make
- Docker

### Install python dependencies using
```
make install-all
```

- Add dependencies in pyproject.toml then run
```
make requirements-all
```
to register new dependencies. then you will probably need to remove the version number for prompt-toolkit in requirements.txt
