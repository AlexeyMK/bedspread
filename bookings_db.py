from collections import defaultdict, Counter
from datetime import datetime, timedelta

import gspread
import os


DATE_FORMAT = "%Y-%m-%d"
ROOM_TYPES = ['single', 'shared', 'suite']


def daterange(start_date, end_date):
  for n in range(int((end_date - start_date).days)):
    yield start_date + timedelta(n)


def weekrange(start_date, num_weeks):
  SATURDAY = 5
  while start_date.weekday() != SATURDAY: start_date -= timedelta(days=1)
  for weeks_ahead in xrange(num_weeks):
    yield start_date + timedelta(weeks=weeks_ahead)


class BookingsDB(object):
  def __init__(self, need_to_load=None):
    if need_to_load == None:
      need_to_load = ["bookings", "rooms"]
    elif isinstance(need_to_load, basestring):
      need_to_load = [need_to_load]

    # { "double 2": [booking, booking, booking...]}
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

  def _load_worksheet(self, wksht_name, spreadsheet="Hacker Paradise Booking System"):
    sheet = self.gc.open(spreadsheet)
    wksht = sheet.worksheet(wksht_name)
    wksht_cells = wksht.get_all_values()
    wksht_property_names = wksht_cells[0]
    output_dict = defaultdict(list)
    for wksht_details_raw in wksht_cells[1:]:
      output_dict[wksht_details_raw[0]].append(
        dict(zip(wksht_property_names, wksht_details_raw)))
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

  def capacity_by_week(self):
    # { datetime(2/15): { single: {min: 4, max: 6} } }
    capacity_by_week_by_room_type = defaultdict(lambda: defaultdict(Counter))

    for name, hotel in self.hotel_capacity().iteritems():
      for start_date in weekrange(hotel["date_start"], hotel["num_weeks"]):
        for room_type in ROOM_TYPES:
          capacity_by_week_by_room_type[start_date][room_type]["min"] += \
            hotel["capacity"][room_type][0]
          capacity_by_week_by_room_type[start_date][room_type]["max"] += \
            hotel["capacity"][room_type][1]

    return capacity_by_week_by_room_type

  def hotel_capacity(self):
    capacity_wksht = self._load_worksheet("Sheet1", spreadsheet="HP SE Asia 2015 Hotel Availability")
    capacities = {}
    for name, hotels in capacity_wksht.iteritems():
      for hotel in hotels:
        intf = lambda field_name: int(hotel[field_name])
        capacities[name] = dict(
          date_start=datetime.strptime(hotel["Start Date"], DATE_FORMAT),
          num_weeks=intf("# Weeks"),
          capacity=dict(
            single=(intf("Min Single"), intf("Max Single")),
            shared=(intf("Min Shared"), intf("Max Shared")),
            suite=(intf("Min Suite"), intf("Max Suite"))
          )
        )

    return capacities


  def se_asia_bookings_by_week(self):
    # {email:  [{"Start Date", "Room Type", "# Weeks"}]
    confirmations_by_user = self._load_worksheet("Form Responses 1",
      spreadsheet="Deposit Confirmation - Hacker Paradise Spring 2015 SE Asia   (Responses)")

    # {datetime(2/15/2015): {"Single": set("jon@jon.com", ...)}}
    bookings_by_week_by_type = defaultdict(lambda: defaultdict(set))

    for email, confirmations in confirmations_by_user.iteritems():
      for confirmation in confirmations:
        if "@" in email: # real users only, we have a bunch of meta-rows
          # TODO move date to nearest saturday before the date.
          for date in weekrange(datetime.strptime(
                        confirmation["Start Date"], "%m/%d").replace(year=2015),
                                int(confirmation["# Weeks"])):
            bookings_by_week_by_type[date][confirmation["Room Type"].lower()].add(email)

    return bookings_by_week_by_type


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
