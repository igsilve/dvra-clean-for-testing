# RESTaurant API

RESTaurant API is a restaurant ordering and menu management service built with
Python and FastAPI, backed by PostgreSQL. It provides endpoints for managing
menu items, placing and tracking orders, user accounts and authentication,
referrals and discount coupons, and basic administrative utilities.

## Development Stack

- Python 3.10
- FastAPI
- PostgreSQL 15.4
- SQLAlchemy + Alembic (migrations)
- Pytest
- Docker / Docker Compose

## Running the Application

1. Install [Docker](https://www.docker.com/get-started/) and [Docker Compose V2](https://docs.docker.com/compose/install/).

2. Start the application:

```sh
./start_app.sh
```

3. The API service is exposed at [http://localhost:8091](http://localhost:8091) by default. API documentation is available at:
   - Swagger - [http://localhost:8091/docs](http://localhost:8091/docs)
   - Redoc - [http://localhost:8091/redoc](http://localhost:8091/redoc)

4. To stop the application:

```sh
./stop_app.sh
```

Data persists between stops and starts.

## Running Tests

```sh
docker compose build
docker compose run web pytest .
```

## License

This project is distributed under the terms of the GNU General Public License
version 3.0 (GNU GPL v3.0). See the [LICENSE](LICENSE) file for details.
