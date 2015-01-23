from collections import defaultdict
from datetime import datetime, timedelta

import gspread
import os


DATE_FORMAT = "%Y-%m-%d"


def daterange(start_date, end_date):
  for n in range(int((end_date - start_date).days)):
    yield start_date + timedelta(n)


class BookingsDB(object):
  def __init__(self, need_to_load=None):
    if need_to_load == None:
      need_to_load = ["bookings", "rooms"]
    elif isinstance(need_to_load, basestring):
      need_to_load = [need_to_load]

    # { "double 2": [booking, booking, booking...]}
    if need_to_load != []:
      print "Started loading DB..."
      self.gc = gspread.login('hackerparadise2014@gmail.com', os.environ["GOOGLE_PASS"])
      self.spreadsheet = self.gc.open("Hacker Paradise Booking System")

    if "bookings" in need_to_load:
      self.all_bookings = []
      self.bookings_by_room = defaultdict(list)
      # { "double 2": {datetime(2014,09,12):{booking details}}}
      self.dates_occupied_by_room = defaultdict(dict)
      self._load_bookings()

    if "rooms" in need_to_load:
      self.room_properties = self._load_worksheet('Rooms')
      self.category_properties = self._load_worksheet('Categories')
    print "Finished loading DB"

  def _load_worksheet(self, wksht_name):
    wksht = self.spreadsheet.worksheet(wksht_name)
    wksht_cells = wksht.get_all_values()
    wksht_property_names = wksht_cells[0]
    output_dict = {}
    for wksht_details_raw in wksht_cells[1:]:
      output_dict[wksht_details_raw[0]] = \
        dict(zip(wksht_property_names, wksht_details_raw))
    return output_dict

  def _load_bookings(self):
    bookings = self.spreadsheet.worksheet("Bookings")

    for room_id, name, checkin_date, checkout_date, status in bookings.get_all_values()[1:]:
      booking_dict = {
        "name": name,
        "checkin_date": datetime.strptime(checkin_date, DATE_FORMAT),
        "checkout_date": datetime.strptime(checkout_date, DATE_FORMAT),
        "room_name": room_id,
        "status": status
      }

      self.bookings_by_room[room_id].append(booking_dict)
      self.all_bookings.append(booking_dict)

    for room_id, bookings in self.bookings_by_room.iteritems():
      for booking in bookings:
        # TODO(AMK) error handling for double-booking
        for booked_date in daterange(booking["checkin_date"],
                                     booking["checkout_date"]):
          self.dates_occupied_by_room[room_id][booked_date] = booking

      self.all_bookings.sort(key=lambda b: b["checkin_date"])


  def hotel_capacity(self):
    # hotel_name: {date_start, num_weeks, capacity: {singles: [min, max], ...}}
    return {"Grand Mango Hotel": dict(
      date_start=datetime(2014,2,15),
      capacity=dict(
        single=[10,15],
        shared=[8,16],
        suite=[0,20]
      )
    )}

  def dates_by_room(self):
    # basically dates_occupied_by_room, but include rooms
    # that are 100% not booked
    return dict((room_id, self.dates_occupied_by_room.get(room_id, dict()))
                 for room_id in self.room_properties.keys())

  def upcoming_arrivals(self, days=1):
    # find everybody who is coming in the next seven days
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    day_range = list(daterange(today, today + timedelta(days=days)))
    return [b for b in self.all_bookings if b["checkin_date"] in day_range]

  def arrivals_this_week(self):
    return self.upcoming_arrivals(days=7)

  def room_types_available(self, start_date, end_date):
    rooms = self.bookings_by_room.keys()
    available_rooms = [room for room in rooms
        if self.is_room_available(room, start_date, end_date)]
    room_types_available = set(self.room_properties[room]['category'] \
        for room in available_rooms)
    return [self.category_properties[rt] for rt in room_types_available]

  def is_room_available(self, room, start_date, end_date):
    return all(date not in self.dates_occupied_by_room[room]
               for date in daterange(start_date, end_date))
