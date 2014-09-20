from flask import Flask, render_template
from collections import defaultdict

import gspread


app = Flask(__name__)
print "loading spreadsheet..."
gc = gspread.login('hackerparadise2014@gmail.com', 'hacker2014')
print "done"


@app.route('/')
def hello_world():
  # Open a worksheet from spreadsheet with one shot
  wks = gc.open("Bookings").sheet1
  bookings_by_room = defaultdict(list)
  for name, checkin_date, checkout_date, room_id in wks.get_all_values()[1:]:
    bookings_by_room[room_id].append({
      "name": name,
      "checkin_date": checkin_date,
      "checkout_date": checkout_date,
      "room_id": room_id
    })

  return render_template("calendar.html", bookings_by_room=bookings_by_room)


if __name__ == '__main__':
  app.run(debug=True)
