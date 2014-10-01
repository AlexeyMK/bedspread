from flask import Flask, render_template, request, send_from_directory, jsonify
from datetime import datetime
from dateutil.parser import parse

from bookings_db import daterange, BookingsDB


app = Flask(__name__)


@app.route('/')
def calendar():
  bookings_db = BookingsDB(need_to_load="bookings")
  now = datetime.now()
  # TODO(AMK) infer from calendar
  min_checkin_date = datetime(now.year, now.month, now.day)
  max_checkin_date = datetime(2014, 11, 29)
  calendar_date_range = list(daterange(min_checkin_date, max_checkin_date))
  dates_occupied_by_room = bookings_db.dates_occupied_by_room
  rooms = sorted(dates_occupied_by_room.keys())

  return render_template("calendar.html",
    calendar_date_range=calendar_date_range,
    dates_occupied_by_room=dates_occupied_by_room,
    rooms=rooms,
  )


@app.route('/arrivals')
def arrivals():
  bookings_db = BookingsDB(need_to_load="bookings")
  return render_template("arrivals.html",
      arrivals=bookings_db.arrivals_this_week(),
      today_weekday=datetime.now().strftime("%A"))


@app.route('/arrivals.json')
def arrivals_json():
  bookings_db = BookingsDB(need_to_load="bookings")
  return jsonify(arrivals=bookings_db.upcoming_arrivals(
      days=int(request.args.get('days', 7))))


@app.route('/search')
def search():
  if 'start_date' in request.args:
    bookings_db = BookingsDB()
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


@app.route('/bower_components/<path:filename>')
def custom_static(filename):
    return send_from_directory('bower_components', filename)

if __name__ == '__main__':
  app.run(debug=True)
