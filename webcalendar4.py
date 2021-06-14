from flask import Flask
from flask_restful import Api
from flask_restful import Resource
from flask_restful import reqparse
from flask_restful import inputs
from flask_sqlalchemy import SQLAlchemy
from flask import abort
from flask import request
import sys
import datetime

app = Flask(__name__)
api = Api(app)

db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webcalendar.db'

class WebCalendar(db.Model):
    __tablename__ = 'webcalendar'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False)

db.create_all()

parser = reqparse.RequestParser()

parser.add_argument(
    'date',
    type=inputs.date,
    help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
    required=True
)

parser.add_argument(
    'event',
    type=str,
    help="The event name is required!",
    required=True
)

def to_date(yyyy_mm_dd):
    year = int(yyyy_mm_dd[0:4])
    month = int(yyyy_mm_dd[5:7])
    day = int(yyyy_mm_dd[8:10])
    return datetime.datetime(year, month, day)

class WebCalendarEvent(Resource):
    def post(self):
        args = parser.parse_args()
        event = args["event"]
        date = args["date"]

        wc = WebCalendar(event=event, date=date)
        db.session.add(wc)
        db.session.commit()

        dict = {}
        dict["message"] = "The event has been added!"
        dict["event"] = event
        dict["date"] = date.strftime("%Y-%m-%d")
        return dict       

    def get(self):
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        if start_time and end_time:        
            start_time = to_date(start_time)
            end_time = to_date(end_time)
            rows = WebCalendar.query.filter(WebCalendar.date >= start_time, WebCalendar.date <= end_time).all()
        else:
            rows = WebCalendar.query.all()
        wclist = []
        for row in rows:
            dict = {}
            dict["id"] = row.id
            dict["event"] = row.event
            dict["date"] = row.date.strftime("%Y-%m-%d")
            wclist.append(dict)
        return wclist

class WebCalendarToday(Resource):
    def get(self):
        rows = WebCalendar.query.filter(WebCalendar.date == datetime.date.today()).all()
        wclist = []
        for row in rows:
            dict = {}
            dict["id"] = row.id
            dict["event"] = row.event
            dict["date"] = row.date.strftime("%Y-%m-%d")
            wclist.append(dict)
        return wclist

class EventByID(Resource):
    def get(self, event_id):
        row = WebCalendar.query.filter(WebCalendar.id == event_id).first()
        if  row is None:
            abort(404, "The event doesn't exist!")
        dict = {}
        dict["id"] = row.id
        dict["event"] = row.event
        dict["date"] = row.date.strftime("%Y-%m-%d")
        return dict
        
    def delete(self, event_id):
        row = WebCalendar.query.filter(WebCalendar.id == event_id).first()
        dict = {}
        if row is None:
            abort(404, "The event doesn't exist!")
        else:
            db.session.delete(row)
            db.session.commit()
            dict["message"] = "The event has been deleted!"
        return dict
    
api.add_resource(EventByID, '/event/<int:event_id>')
api.add_resource(WebCalendarEvent, '/event')
api.add_resource(WebCalendarToday, '/event/today')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()