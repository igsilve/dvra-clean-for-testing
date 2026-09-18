# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the owners of this repository before making a change.

Please note we have a code of conduct, please follow it in all your interactions with the project.

# Development

## Configuring the project
The project is developed with the following frameworks and technologies:
* [Python 3.10](https://www.python.org/downloads/release/python-380/)
* [Docker](https://www.docker.com/) as a platform for containerisation
* [FastAPI](https://github.com/tiangolo/fastapi) as easy to learn and fast to code web framework
* [PostgreSQL 15.4](https://www.postgresql.org/) as a database
* [Pytest](https://docs.pytest.org/) for code testing
* [pre-commit](https://pre-commit.com/) for maintaining hooks for code style and tests

Configuring a development environment is a straightforward process assuming that `Python>=3.10`, `pip` and `Docker` are already installed:

1. Install `psycopg2` prerequisites as described in the [official documentation](https://www.psycopg.org/install/). For "*nix" distributions, the following command can be used:
    ```sh
    sudo apt install python3-dev libpq-dev
    ```


2. Clone the repository and change directory to the project root.

3. Install Poetry:
    ```sh
    pip3 install poetry
    ```

4. Install project dependencies and spawn shell within the created environment:
    ```sh
    poetry install
    poetry shell
    ```

5. Setup [pre-commit](https://pre-commit.com/):
    ```sh
    pre-commit install
    ```

6. Validate that tests are passing locally:
    ```sh
    pytest .
    ```
7. Develop API endpoints by following the already existing files structure.

## Running Tests
```sh
docker compose build
docker compose run web pytest .
```


## Generating Alembic Migrations
Changes in database models need to be reflected in migrations via Alembic. Migrations can be created via:
```sh
docker compose build
docker compose run web alembic revision --autogenerate -m 'changes description'
```

## Security Review Checklist
Before merging any change, reviewers should confirm the following:

1. Authentication and authorization are enforced server-side for new or modified endpoints.
2. Input is validated with schema constraints and output does not expose secrets or internal-only fields.
3. SQL access uses bound parameters and avoids string-built queries with untrusted input.
4. State-changing operations use POST, PUT, PATCH, or DELETE and are covered by CSRF controls where applicable.
5. Docker and deployment changes preserve least privilege (non-root, no-new-privileges, capability drop, and restricted network/port exposure).
6. Any security-relevant changes include or update tests for negative/abuse-path behavior.
