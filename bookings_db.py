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
    print "Started loading DB..."
    self.bookings_by_room = defaultdict(list)
    # { "double 2": {datetime(2014,09,12):{booking details}}}
    self.dates_occupied_by_room = defaultdict(dict)
    self.room_properties = {}

    self.gc = gspread.login('hackerparadise2014@gmail.com', 'hacker2014')
    self.spreadsheet = self.gc.open("Bookings")
    self._load_bookings()
    self._load_rooms()
    print "Finished loading DB"

  def _load_rooms(self):
    rooms = self.spreadsheet.worksheet("Rooms")
    room_cells = rooms.get_all_values()
    room_property_names = room_cells[0]
    for room_details_raw in room_cells[1:]:
      self.room_properties[room_details_raw[0]] = \
          dict(zip(room_property_names, room_details_raw))

  def _load_bookings(self):
    bookings = self.spreadsheet.worksheet("Bookings")

    for room_id, name, checkin_date, checkout_date, status in bookings.get_all_values()[1:]:
      self.bookings_by_room[room_id].append({
        "name": name,
        "checkin_date": datetime.strptime(checkin_date, DATE_FORMAT),
        "checkout_date": datetime.strptime(checkout_date, DATE_FORMAT),
        "room_name": room_id,
        "status": status
      })

    for room_id, bookings in self.bookings_by_room.iteritems():
      for booking in bookings:
        # TODO(AMK) error handling for double-booking
        for booked_date in daterange(booking["checkin_date"],
                                     booking["checkout_date"]):
          self.dates_occupied_by_room[room_id][booked_date] = booking

  def room_details(self, room_id):
    return self.room_properties[room_id]

  def room_types_available(self, start_date, end_date):
    rooms = self.bookings_by_room.keys()
    available_rooms = [room for room in rooms
        if self.is_room_available(room, start_date, end_date)]
    return set(self.room_details(room)['category'] \
        for room in available_rooms)

  def is_room_available(self, room, start_date, end_date):
    return all(date not in self.dates_occupied_by_room[room]
               for date in daterange(start_date, end_date))
