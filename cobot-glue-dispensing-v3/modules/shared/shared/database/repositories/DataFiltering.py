# from shared.shared.database.repositories.csvRepository.Constants import DATE, TIME, REGISTRATION_NUMBER, DIRECTION, EVENT_TYPE
#
#
# def filterByDateRange(data, start_date, end_date):
#     """
#     Filter data by date range.
#     """
#     return data[(data[DATE] >= start_date) & (data[DATE] <= end_date)]
#
#
# def filterByTimeRange(data, start_time, end_time):
#     """
#     Filter data by time range.
#     """
#     return data[(data[TIME] >= start_time) & (data[TIME] <= end_time)]
#
#
# def filterByDirection(data, direction):
#     """
#     Filter data by direction.
#     """
#     return data[data[DIRECTION] == direction]
#
#
# def filterByAccessStatus(data, access_status):
#     """
#     Filter data by access status or event type.
#     """
#     return data[data[EVENT_TYPE] == access_status]
#
#
# def filterByRegistrationNumber(data, reg):
#     """
#     Filter data by registration number.
#     """
#     return data[data[REGISTRATION_NUMBER].str.upper() == reg.upper()]
#
#
# def filterByUsername(data, username):
#     """
#     Filter data by username.
#     """
#     return data[data['User'].str.upper() == username.upper()]
#
#
# def filterByRole(data, role):
#     """
#     Filter data by role.
#     """
#     return data[data['Role'] == role]
#
#
# def filterByEmail(data, email):
#     """
#     Filter data by email.
#     """
#     return data[data['Email'].str.upper() == email.upper()]
#
#
# def filterByAccessLevel(data, value):
#     """
#     Filter data by access level.
#     """
#     print("Filtering",data)
#     return data[data['Access Level'] == value]
#
#
# def filterData(data, filters):
#     """
#     Filter data based on a dictionary of filters.
#
#     Available filters:
#     - date_range: (start_date, end_date)
#     - time_range: (start_time, end_time)
#     - direction: 'IN' or 'OUT'
#     - access_status: 'GRANTED' or 'DENIED'
#     - registration_number: string registration number
#     - username: string username
#     - role: string user role
#     - email: string email
#     """
#     for key, value in filters.items():
#         if value:
#             if key == 'date_range':
#                 data = filterByDateRange(data, value[0], value[1])
#             elif key == 'time_range':
#                 data = filterByTimeRange(data, value[0], value[1])
#             elif key == 'direction':
#                 data = filterByDirection(data, value)
#             elif key == 'access_status':
#                 data = filterByAccessStatus(data, value)
#             elif key == 'registration_number':
#                 data = filterByRegistrationNumber(data, value)
#             elif key == 'username':
#                 data = filterByUsername(data, value)
#             elif key == 'role':
#                 data = filterByRole(data, value)
#             elif key == 'email':
#                 data = filterByEmail(data, value)
#             elif key == 'registration_number':
#                 data = filterByRegistrationNumber(data, value)
#             elif key == 'access_level':
#                 data = filterByAccessLevel(data, value)
#             else:
#                 raise ValueError(f"Invalid filter key: {key}")
#     return data