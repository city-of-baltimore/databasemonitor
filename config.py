"""Configuration file for each database"""

config = [
    # dataflow runs daily at 12am +4 hours
    {
        'table_name': 'acrs_crash',
        'date_col': 'ACRSREPORTTIMESTAMP',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 2880  # 48 hours
    },

    # dataflow runs daily at 12am +4 hours
    {
        'table_name': 'atves_amber_time_rejects',
        'date_col': 'violation_date',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 2880  # 48 hours
    },

    # dataflow runs from 6:30am-12:30am every 5 minutes
    {
        'table_name': 'ccc_bus_runtimes',
        'date_col': 'starttime',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 720  # 12 hours
    },

    # dataflow runs daily at 12am +4 hours
    {
        'table_name': 'ccc_arrival_times',
        'date_col': 'date',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 2880  # 48 hours
    },

    # dataflow runs daily at 12am +4 hours
    {
        'table_name': 'atves_approval_by_review_date_details',
        'date_col': 'review_datetime',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 2880  # 48 hours
    },

    # dataflow runs daily at 12am +4 hours
    {
        'table_name': 'atves_by_location',
        'date_col': 'date',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 2880  # 48 hours
    },

    # dataflow runs daily at 12am +4 hours
    {
        'table_name': 'atves_traffic_counts',
        'date_col': 'date',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 2880  # 48 hours
    },

    # dataflow runs daily at 12am +4 hours
    {
        'table_name': 'ticketstat',
        'date_col': 'Infraction_Datetime',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 2880  # 48 hours
    },

    # dataflow runs daily at 12am +4 hours
    {
        'table_name': 'towstat_agebydate',
        'date_col': 'date',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 2880  # 48 hours
    },
]
