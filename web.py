from flask import Flask, render_template, request
from datetime import datetime
from dateutil.parser import parse

from bookings_db import daterange, BookingsDB


app = Flask(__name__)
bookings_db = BookingsDB()


@app.route('/')
def calendar():
  # TODO(AMK) infer from calendar
  min_checkin_date = datetime(2014, 9, 1)
  max_checkin_date = datetime(2014, 12, 1)
  calendar_date_range = list(daterange(min_checkin_date, max_checkin_date))
  dates_occupied_by_room = bookings_db.dates_occupied_by_room
  rooms = dates_occupied_by_room.keys()

  return render_template("calendar.html", **locals())


@app.route('/search')
def search():
  if 'start_date' in request.args:
    start_date = parse(request.args['start_date'])
    end_date = parse(request.args['end_date'])
    available_types = bookings_db.room_types_available(start_date, end_date)
    return render_template('search_results.html',
      available_types=available_types,
      daterange_human = "{start} to {end}".format(
        start=start_date.strftime("%b %d"),
        end=end_date.strftime("%b %d")
      )
    )
  else:
    return render_template('search.html')


if __name__ == '__main__':
  app.run(debug=True)
