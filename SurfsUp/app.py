# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from pathlib import Path
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta
import numpy as np


#################################################
# Database Setup
#################################################

# reflect an existing database into a new model
database_path = Path(r"Resources/hawaii.sqlite")
engine = create_engine(f"sqlite:///{database_path}")
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect= True)

# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
Session = Session(engine)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################

# Start at homepage
@app.route('/')

def homepage():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )


@app.route('/api/v1.0/precipitation') 
def precipitation():
    #Retrieve the last 12 months of precipitation data
    last_year = datetime.now() - timedelta(days=365)
    date_filter = dt.date(2017, 8, 23) - dt.timedelta(days=365)
    results = Session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= date_filter).all()

    Session.close()

    # Convert the results to a dictionary
    prcp_dict = {date: prcp for date, prcp in results}

    # Return the JSON representation of the dictionary
    return jsonify(prcp_dict)

@app.route('/api/v1.0/stations') 
def stations():
    results = Session.query(Station.station, Station.name).all()
    
    Session.close()

    # Convert the results to a list of dictionaries
    stations_list = [{'station': station, 'name': name} for station, name in results]

    # Return the JSON representation of the list
    return jsonify(stations_list)


@app.route('/api/v1.0/tobs') 
def tobs():
    # Retrieve the previous year of data
    last_year = datetime.now() - timedelta(days=365)
    active_station_query = Session.query(Measurement.station).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()
    active_station = active_station_query[0]

    # Query temperature observations for the most active station
    results = Session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == active_station,
        Measurement.date >= last_year
    ).all()

    Session.close()

    # Convert the results to a list of dictionaries
    tobs_list = [{'date': date, 'temperature': tobs} for date, tobs in results]

    # Return the JSON representation of the list
    return jsonify(tobs_list)


@app.route('/api/v1.0/<start>') 
@app.route('/api/v1.0/<start>/<end>')
def temperature_range(start, end=None):
    try:
        start_date = dt.datetime.strptime(start, '%Y-%m-%d')
        if end:
            end_date = dt.datetime.strptime(end, '%Y-%m-%d')
        else:
            end_date = datetime.now()  # Use current date if no end date is provided
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    query = Session.query(
        func.min(Measurement.tobs).label('MIN'),
        func.avg(Measurement.tobs).label('AVG'),
        func.max(Measurement.tobs).label('MAX')
    ).join(Station, Measurement.station == Station.station)

    # Add filters based on the presence of end date
    if end:
        query = query.filter(
            Measurement.date >= start_date,
            Measurement.date <= end_date
        )
    else:
        query = query.filter(
            Measurement.date >= start_date
        )

    results = query.all()
    Session.close()

    # Prepare the response
    temperature_stats = []
    for min_temp, avg_temp, max_temp in results:
        temperature_stats.append({
            'MIN': min_temp,
            'AVG': avg_temp,
            'MAX': max_temp
        })

    # Return the JSON representation of the temperature stats
    return jsonify(temperature_stats)

if __name__ == '__main__':
    app.run(debug=True)



