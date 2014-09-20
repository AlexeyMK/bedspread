from collections import defaultdict
from datetime import datetime, timedelta

import gspread


DATE_FORMAT = "%Y-%m-%d"


def daterange(start_date, end_date):
  for n in range(int((end_date - start_date).days)):
    yield start_date + timedelta(n)


class BookingsDB(object):
  def __init__(self):
    # { "double 2": [booking, booking, booking...]}
    self.bookings_by_room = defaultdict(list)
    # { "double 2": [12/01/2014, 13/01/2014...]} (datetime objects)
    self.dates_occupied_by_room = defaultdict(set)

    self.gc = gspread.login('hackerparadise2014@gmail.com', 'hacker2014')
    self._load_bookings()

  def _load_bookings(self):
    # Open a worksheet from spreadsheet with one shot
    spreadsheet = self.gc.open("Bookings")
    bookings = spreadsheet.worksheet("Bookings")

    for room_id, name, checkin_date, checkout_date in bookings.get_all_values()[1:]:
      self.bookings_by_room[room_id].append({
        "name": name,
        "checkin_date": datetime.strptime(checkin_date, DATE_FORMAT),
        "checkout_date": datetime.strptime(checkout_date, DATE_FORMAT),
        "room_id": room_id
      })

    for room_id, bookings in self.bookings_by_room.iteritems():
      for booking in bookings:
        # TODO(AMK) error handling for double-booking
        for booked_date in daterange(booking["checkin_date"],
                                     booking["checkout_date"]):
          self.dates_occupied_by_room[room_id].add(booked_date)

  def room_details(self, room_id):
    return dict(name=room_id, category="single")

  def room_available_during_range(self, room, start_date, end_date):
    return all(date not in self.dates_occupied_by_room[room]
               for date in daterange(start_date, end_date))
