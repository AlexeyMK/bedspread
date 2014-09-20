from flask import Flask, render_template
from collections import defaultdict
from datetime import datetime, timedelta

import gspread


app = Flask(__name__)
print "loading spreadsheet..."
gc = gspread.login('hackerparadise2014@gmail.com', 'hacker2014')
print "done"


DATE_FORMAT = "%Y-%m-%d"


def daterange(start_date, end_date):
  for n in range(int((end_date - start_date).days)):
    yield start_date + timedelta(n)


@app.route('/')
def hello_world():
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


  # TODO(AMK) infer from calendar
  min_checkin_date = datetime(2014, 9, 1)
  max_checkin_date = datetime(2014, 12, 1)
  calendar_date_range = daterange(min_checkin_date, max_checkin_date)

  return render_template("calendar.html", **locals())


if __name__ == '__main__':
  app.run(debug=True)
