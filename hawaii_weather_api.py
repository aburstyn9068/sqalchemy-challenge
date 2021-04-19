# Import dependencies
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify
import datetime as dt

# Database setup
engine = create_engine("sqlite:///./Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurements = Base.classes.measurement
Stations = Base.classes.station

# Create an app
app = Flask(__name__)


# Define routes
@app.route("/")
def home():
    """Display the api routes"""
    return (
        f"Welcome to the Hawaii Weather API<br/>"
        "<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date<br/>"
        "<br/>"
        f"Date format: YYYY-MM-DD"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Convert the query results to a dictionary using `date` as the key and `prcp` as the value."""
    # Create a link to the session
    session = Session(engine)
    
    # Query all precipitation records
    results = session.query(Measurements.date, Measurements.prcp).all()
    
    session.close()

    # Create a dictionary from the query results
    all_prcp = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["prcp"] = prcp
        all_prcp.append(prcp_dict)
    
    return jsonify(all_prcp)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Create a link to the session
    session = Session(engine)
    
    # Query all station records
    results = session.query(Stations.station, Stations.name).all()
    
    session.close()

    # Create a dictionary from the query results
    all_stations = []
    for station, name in results:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        all_stations.append(station_dict)
    
    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    """Query the dates and temperature observations of the most active station for the last year of data."""
    """Return a JSON list of temperature observations (TOBS) for the previous year."""
    # Create a link to the session
    session = Session(engine)
    
    # Query temperature observations of the most active station for the last year of data

    # Find the date 1 year prior to the mose recent date in the database
    recent_date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()[0]
    date1 = recent_date.split("-")
    year_ago = dt.date(int(date1[0]), int(date1[1]), int(date1[2])) - dt.timedelta(days=365)
    # Find the most active station
    most_active_station = session.query(Measurements.station, func.count(Measurements.station)).\
        group_by(Measurements.station).\
        order_by(func.count(Measurements.station).desc()).first()[0]
    # Get the temperature data 
    results = session.query(Measurements.date, Measurements.tobs).\
        filter_by(station=most_active_station).\
        filter(Measurements.date >= year_ago).all()
    
    session.close()

    # Create a dictionary from the query results
    all_tobs = []
    for date, tobs in results:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        all_tobs.append(tobs_dict)
    
    return jsonify(all_tobs)

@app.route("/api/v1.0/<start>")
def date(start):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature"""
    """for all dates greater than and equal to the start date."""
    # Create a link to the session
    session = Session(engine)
    
    # Get the start and end date of the data
    final_date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()[0]
    first_date = session.query(Measurements.date).order_by(Measurements.date.asc()).first()[0]
    
    # Make sure date is in range of the available data
    if (start > final_date) or (start < first_date):
        return f"{start} is not a proper date.</br>Try dates between {first_date} - {final_date}"

    # Query the min, avg, and max temps for the given timeframe
    results = []
    while start <= final_date:
        min_temp = session.query(func.min(Measurements.tobs)).filter(Measurements.date==start).first()[0]
        avg_temp = session.query(func.avg(Measurements.tobs)).filter(Measurements.date==start).first()[0]
        max_temp = session.query(func.max(Measurements.tobs)).filter(Measurements.date==start).first()[0]
    
        # Store the information retrieved
        results.append([start, min_temp, avg_temp, max_temp])
        
        # Update the date to check the next record
        date1 = start.split("-")
        date1 = dt.date(int(date1[0]), int(date1[1]), int(date1[2])) + dt.timedelta(days=1)
        start = date1.strftime("%Y-%m-%d")

    session.close()

    # Create a dictionary from the query results
    date_temps = []
    for date, min_temp, avg_temp, max_temp in results:
        date_temps_dict = {}
        date_temps_dict["date"] = date
        date_temps_dict["min_temp"] = min_temp
        date_temps_dict["avg_temp"] = round(avg_temp, 2)
        date_temps_dict["max_temp"] = max_temp
        date_temps.append(date_temps_dict)
    
    return jsonify(date_temps)

@app.route("/api/v1.0/<start>/<end>")
def date_range(start, end):
    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature"""
    """between the start and end date inclusive."""
    # Create a link to the session
    session = Session(engine)
    
    # Get the start and end date of the data
    final_date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()[0]
    first_date = session.query(Measurements.date).order_by(Measurements.date.asc()).first()[0]
    
    # Make sure dates are in range of available data
    if (start > final_date) or (start < first_date) or (end > final_date) or (end < first_date) or (start>end):
        return f"{start} - {end} is not a proper date range.</br>Try dates between {first_date} - {final_date}"

    # Query the min, avg, and max temps for the given timeframe
    results = []
    while start <= end:
        min_temp = session.query(func.min(Measurements.tobs)).filter(Measurements.date==start).first()[0]
        avg_temp = session.query(func.avg(Measurements.tobs)).filter(Measurements.date==start).first()[0]
        max_temp = session.query(func.max(Measurements.tobs)).filter(Measurements.date==start).first()[0]
    
        # Store the information retrieved
        results.append([start, min_temp, avg_temp, max_temp])
        
        # Update the date to check the next record
        date1 = start.split("-")
        date1 = dt.date(int(date1[0]), int(date1[1]), int(date1[2])) + dt.timedelta(days=1)
        start = date1.strftime("%Y-%m-%d")

    session.close()

    # Create a dictionary from the query results
    date_temps = []
    for date, min_temp, avg_temp, max_temp in results:
        date_temps_dict = {}
        date_temps_dict["date"] = date
        date_temps_dict["min_temp"] = min_temp
        date_temps_dict["avg_temp"] = round(avg_temp, 2)
        date_temps_dict["max_temp"] = max_temp
        date_temps.append(date_temps_dict)
    
    return jsonify(date_temps)

if __name__ == "__main__":
    app.run(debug=True)

