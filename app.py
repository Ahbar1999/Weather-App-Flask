import requests
from flask import Flask, render_template, request, redirect, flash, get_flashed_messages
import sys
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

app = Flask(__name__)
key = os.urandom(24)
app.config['SECRET_KEY'] = key
api_key = "45ad015e75571f1e0f8b95649fe39a2a"
# create our weather database
engine = create_engine('sqlite:///weather.db.sqlite', echo=True, connect_args={"check_same_thread": False})
Base = declarative_base()


class WeatherCard(Base):
    __tablename__ = 'Weather'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True, nullable=False)
    temperature = Column(Integer)
    description = Column(String(30))


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


@app.route('/delete/<card_id>')
def delete(card_id):
    session.query(WeatherCard).filter(WeatherCard.id == card_id).delete()
    session.commit()
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # If the given location is not in the database then add it
        city_data = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={request.form.get('input-city')}&limit=1&appid={api_key}").json()
        if not city_data:
            flash("The city doesn't exist!")
            return redirect("/")

        data = requests.post(f"https://api.openweathermap.org/data/2.5/weather?lat={city_data[0]['lat']}&lon={city_data[0]['lon']}&appid={api_key}").json()
        if not session.query(WeatherCard).filter(WeatherCard.name == data['name']).all():
            # add our data to our database
            session.add(WeatherCard(
                name=data['name'],
                temperature=int(-273.15 + data['main']['temp']),
                description=data['weather'][0]['description']
            ))
            session.commit()
        else:
            flash("The city has already been added to the list!")
    # add our weather card objects to be sent to the template
    weather_data = []
    for row in session.query(WeatherCard).all():
        weather_data.append(row)
    return render_template('index.html', data=weather_data)


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run(port=8080)
