from flask import Flask, render_template, request
from collections import defaultdict
from datetime import datetime, timedelta
from dateutil.parser import parse

import gspread


app = Flask(__name__)
print "loading spreadsheet..."
gc = gspread.login('hackerparadise2014@gmail.com', 'hacker2014')
print "done"


DATE_FORMAT = "%Y-%m-%d"


def daterange(start_date, end_date):
  for n in range(int((end_date - start_date).days)):
    yield start_date + timedelta(n)


def load_bookings():
  # Open a worksheet from spreadsheet with one shot
  wks = gc.open("Bookings").sheet1
  bookings_by_room = defaultdict(list)

  for name, checkin_date, checkout_date, room_id in wks.get_all_values()[1:]:
    bookings_by_room[room_id].append({
      "name": name,
      "checkin_date": datetime.strptime(checkin_date, DATE_FORMAT),
      "checkout_date": datetime.strptime(checkout_date, DATE_FORMAT),
      "room_id": room_id
    })

  # { "double 2": [12/01/2014, 13/01/2014...]} (datetime objects)
  dates_occupied_by_room = defaultdict(set)
  for room_id, bookings in bookings_by_room.iteritems():
    for booking in bookings:
      # TODO(AMK) error handling for double-booking
      for booked_date in daterange(booking["checkin_date"],
                                   booking["checkout_date"]):
        dates_occupied_by_room[room_id].add(booked_date)

  return dates_occupied_by_room


@app.route('/')
def calendar():
  # TODO(AMK) infer from calendar
  min_checkin_date = datetime(2014, 9, 1)
  max_checkin_date = datetime(2014, 12, 1)
  calendar_date_range = list(daterange(min_checkin_date, max_checkin_date))
  dates_occupied_by_room = load_bookings()
  rooms = dates_occupied_by_room.keys()

  return render_template("calendar.html", **locals())


def room_available_during_range(room, start_date, end_date, dates_occupied_by_room):
  return all(date not in dates_occupied_by_room[room]
             for date in daterange(start_date, end_date))


@app.route('/search', methods=['GET', 'POST'])
def search():
  dates_occupied_by_room = load_bookings()
  rooms = dates_occupied_by_room.keys()
  if request.method == 'POST':
    start_date = parse(request.form['start_date'])
    end_date = parse(request.form['end_date'])
    available_rooms = [room for room in rooms
      if room_available_during_range(room, start_date, end_date,
                                     dates_occupied_by_room)
    ]

    return render_template('search_results.html', available_rooms=available_rooms)
  else:
    return render_template('search.html')

if __name__ == '__main__':
  app.run(debug=True)
