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
    self.room_properties = {}

    self.gc = gspread.login('hackerparadise2014@gmail.com', 'hacker2014')
    self.spreadsheet = self.gc.open("Bookings")
    self._load_bookings()
    self._load_rooms()

  def _load_rooms(self):
    rooms = self.spreadsheet.worksheet("Rooms")
    room_cells = rooms.get_all_values()
    room_property_names = room_cells[0]
    for room_details_raw in room_cells[1:]:
      self.room_properties[room_details_raw[0]] = \
          dict(zip(room_property_names, room_details_raw))

  def _load_bookings(self):
    bookings = self.spreadsheet.worksheet("Bookings")

    for room_id, name, checkin_date, checkout_date in bookings.get_all_values()[1:]:
      self.bookings_by_room[room_id].append({
        "name": name,
        "checkin_date": datetime.strptime(checkin_date, DATE_FORMAT),
        "checkout_date": datetime.strptime(checkout_date, DATE_FORMAT),
        "room_name": room_id
      })

    for room_id, bookings in self.bookings_by_room.iteritems():
      for booking in bookings:
        # TODO(AMK) error handling for double-booking
        for booked_date in daterange(booking["checkin_date"],
                                     booking["checkout_date"]):
          self.dates_occupied_by_room[room_id].add(booked_date)

  def room_details(self, room_id):
    return self.room_properties[room_id]

  def room_available_during_range(self, room, start_date, end_date):
    return all(date not in self.dates_occupied_by_room[room]
               for date in daterange(start_date, end_date))
