# Radiation Map Project

A web application that visualizes radiation data from Safecast devices on an interactive map. This project fetches real-time radiation measurements and displays them using a heatmap overlay.

## Features

- Real-time radiation data visualization
- Interactive map with zoom and pan capabilities
- Historical data tracking
- Multiple device support
- Responsive design for desktop and mobile

## Prerequisites

- Python 3.8+  (Interpreted scripting language)
- PostgreSQL 16.9+  (Object-relational database engine)
- Supervisor (Python package to manage tasks)
- Git (for version control)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Safecast/rt-ca-map.git
   cd radiation-map
   ```
2. Initialize the database (as a PostgreSQL user e.g. role 'admin'):
   ```bash
   misc/postgresql-initialize-mapsdb.sh
   ```

3. Create and activate a virtual environment (recommended):
   ```sh
   python -m venv venv
   . venv/bin/activate  # On Linux with bash: source venv/bin/activate
   ```

4. Install the required packages:
   ```bash
   python3 -m pip install pip --upgrade  # Get latest installation utility
   pip install -r requirements.txt
   ```

## Configuration

Edit the file `constants.py` to add the PostgreSQL `mapsdb` connection parameters:
   ```python
   # PostgreSQL on Grendel
   DB_HOST = 'localhost'
   DB_PORT = '5432'
   DB_NAME = 'mapsdb'
   DB_USER = 'mapsuser'
   DB_PASS = ''  # Add your secret password (may be blank if you ssh tunnel)
   ```

## Testing the Application

1. Start the ASGI server:
   ```bash
   ./uvicorn_start.sh
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:8000
   ```

## Production
   Launch the start script with Supervisor. The daemon takes care of restarting the application if it quits unexpectedly.

## Project Structure

```
maps_application/
├── maps/              # Main ASGI application module
│   ├── app.py         # Main ASGI application
│   ├── asgi.py        # Main ASGI wrapper
│   ├── templates/     # Jinja2 HTML templates
│       ├── admin.html # Form for /admin end points
│       └── index.html # Map starting point
├── admin.py           # Manage /admin end points
├── database.py        # Interface to PostgreSQL database
├── devices.py         # Manage the devices and /devices end point
├── fetcher.py         # Utilities to fetch from Safecast database
├── requirements.txt   # Python dependencies (install in venv)
├── misc/              # Installation support
│   ├── postgresql-initialize-mapsdb.sh  # Inintialize mapsdb database
│   └── postgresql-schema.sql  # PostgreSQL database schema
├── static/             # Static files (CSS, JS, images)
│   ├── css/
│   └── js/
```

## API Endpoints
   - `/map` GET the map and markers
   - `/devices` GET the list of devices with latitude, longitude, when_captured and uSv/h
   - `/measurements/{device_urn}` GET latest measurements since (time span TBD)

- `GET /map` - Map and markers, main application interface
- `GET /devices` - list of devices with latitude, longitude, when_captured and uSv/h
- `GET /measurements/{device_urn}` - latest measurements since (time span TBD)
- `POST /api/fetch-data` - Trigger data fetch from Safecast API
- `GET /admin` - Admin interface form
- `POST /admin` - With command=..., administer devices

## Data Sources

This application uses data from the [Safecast API](https://safecast.org/).

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Safecast](https://safecast.org/) for providing the radiation data
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Leaflet](https://leafletjs.com/) for the interactive maps
