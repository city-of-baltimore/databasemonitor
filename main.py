"""Main driver code for dbmonitor"""
import argparse
from typing import List

from dbmonitor import ConfigType, DBMonitor

config: List[ConfigType] = [
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

    # dataflow runs from 6:30am-12:30am every 1 minute
    {
        'table_name': 'ccc_arrival_times',
        'date_col': 'date',
        'email': 'brian.seel@baltimorecity.gov',
        'notification_mins': 15
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
        'date_col': 'Export_Date',
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

parser = argparse.ArgumentParser(description='Monitors databases and sends a notification email if there have not been '
                                             'recent enough updates')
parser.add_argument('-e', '--email_address', required=True,
                    help='Email address to use to authenticate to the SMTP server and the source email address of '
                         'notification emails.')
parser.add_argument('-p', '--email_password',
                    help='Email password for the --emailaddress. If not provided, then the SMTP server wont be given '
                         'creds')
parser.add_argument('-m', '--smtp_server', required=True, help='The SMTP server to use for sending notification emails')
parser.add_argument('-c', '--conn_str', required=True, help='Custom database connection string')
parser.add_argument('-s', '--secure', action='store_true', help='Use SMTPS instead of SMTP')

args = parser.parse_args()

cls = DBMonitor(args.conn_str, args.email_address, args.email_password, args.smtp_server, args.secure)
cls.check(config)
