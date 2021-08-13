"""Database monitoring tool that notifies when there are not expected new entries"""
import argparse
import importlib.util
import smtplib
import ssl
import sys
from datetime import datetime, timedelta
from importlib.abc import Loader
from pathlib import Path
from typing import List, TypedDict, Union

from loguru import logger
from sqlalchemy import create_engine, select, Column, DateTime, MetaData, Table  # type: ignore
from sqlalchemy.exc import OperationalError, ProgrammingError  # type: ignore
from sqlalchemy.orm import Session  # type: ignore


class ConfigType(TypedDict):  # pylint:disable=too-few-public-methods, inherit-non-class
    """Structure of the required config dict for typing only"""
    table_name: str
    date_col: str
    email: str
    notification_mins: int


class DBMonitor:
    """
    Connects to the database and checks that the database has updates in the expected timerange. Use with a task
    scheduler to repeatedly check for updates
    """

    def __init__(self, conn_str: str, email_user: str, email_pass: str,  # pylint:disable=too-many-arguments
                 smtp_server: str = "smtp.gmail.com", smtp_secure: bool = True):
        """
        :param conn_str: SqlAlchemy connection string
        :param email_user: Username for SMTP server
        :param email_pass: Password for SMTP server
        :param smtp_server: SMTP server to use for sending email
        :param smtp_secure: If true, use SMTPS for smtp_server. Otherwise, use SMTP.
        """
        self.engine = create_engine(conn_str, echo=True, future=True)
        self.email_user = email_user
        self.email_pass = email_pass
        self.smtp_server = smtp_server
        self.smtp_secure = smtp_secure

        if not self.email_user or not self.smtp_server:
            raise ValueError("Email address and SMTP server are required arguments")

    def check(self, configs: List[ConfigType]) -> None:
        """

        :param configs: Dictionaries with keys:
         table_name - name of the table to check
         date_col - datetime column to use as the critera
         email - email address to notify if it fails the check
         notification_mins - number of seconds of tolerance, outside of which will notify the email address
        :return:
        """
        for config in configs:
            with Session(self.engine) as session:
                table = self.table_generator(config['table_name'], config['date_col'])

                stmt = select(table).where(table.columns[config['date_col']] >=
                                           (datetime.now() - timedelta(minutes=config['notification_mins'])))
                try:
                    result = session.execute(stmt).fetchall()
                except (OperationalError, ProgrammingError):
                    # for no such table error
                    logger.exception("Error")
                    result = []

                if len(result) == 0:
                    self.send_notification([config['email']],
                                           config['table_name'],
                                           config['notification_mins'],
                                           self.smtp_secure)

    def table_generator(self, table_name: str, col_name: str) -> Table:
        """
        Creates a SQL Alchemy model
        :param table_name: Table name
        :param col_name: Column containing the DateTime field
        :return: SqlAlchemy Table object
        """
        metadata = MetaData(bind=self.engine)
        return Table(table_name,
                     metadata,
                     Column(col_name, DateTime))

    def send_notification(self, recipient_addresses: List[str], table_name: str, notification_mins: int,
                          secure: bool) -> None:
        """
        Sends a notification to the included email address
        :param recipient_addresses: List of email addresses to send the notification to
        :param table_name: Table that we were checking. This is only used for the email text.
        :param notification_mins: Number of minutes since we expected the last entry. This is only used for the email
        text
        :param secure: If true, use SMTPS (465). Otherwise use SMTP (port 25).
        """
        if secure:
            # Create a secure SSL context
            context = ssl.create_default_context()
            server: Union[smtplib.SMTP, smtplib.SMTP_SSL] = smtplib.SMTP_SSL(self.smtp_server, 465, context=context)
        else:
            server = smtplib.SMTP(self.smtp_server, 25)

        if self.email_pass:
            server.login(self.email_user, self.email_pass)

        for addr in recipient_addresses:
            server.sendmail(self.email_user, addr,
                            "Subject: Database dataflow failure: {table}\n\nDataflow failure in DOT_DATA.{table}. "
                            "No data in last {ns} minutes, which was unexpected".format(
                                table=table_name, ns=notification_mins))
        server.close()


def setup_logging(debug=False, info=False, path: Path = None):
    """
    Configures the logging level, and sets up file based logging. By default, the following logging levels are enabled:
    fatal, error, and warn. This optionally enables info and debug.

    :param debug: If true, the Debug logging level is used, and verbose is ignored
    :param info: If true and debug is false, then the info log level is used
    :param path: Base path where the logs folder should go. If not specified, then it uses the current dir
    """
    # Setup logging
    log_level = 'WARNING'
    if debug:
        log_level = 'DEBUG'
    elif info:
        log_level = 'INFO'

    if path:
        log_path = path / 'logs' / 'file-{time}.log'
    else:
        log_path = Path('logs') / 'file-{time}.log'

    handlers = [
        {'sink': sys.stdout, 'format': '{time} - {message}', 'colorize': True, 'backtrace': True, 'diagnose': True,
         'level': log_level},
        {'sink': log_path, 'serialize': True, 'backtrace': True,
         'diagnose': True, 'rotation': '1 week', 'retention': '3 months', 'compression': 'zip', 'level': log_level},
    ]

    logger.configure(handlers=handlers)


def setup_parser(help_str="Driver for the transitstat scripts"):
    """Factory that creates the base argument parser"""
    parser = argparse.ArgumentParser(description=help_str)
    parser.add_argument('-v', '--verbose', action='store_true', help='Increased logging level')
    parser.add_argument('-vv', '--debug', action='store_true', help='Print debug statements')
    parser.add_argument('-c', '--conn_str', help='Database connection string',
                        default='mssql+pyodbc://balt-sql311-prd/DOT_DATA?driver=ODBC Driver 17 for SQL Server')

    return parser


def parse_args(_args):
    """Handles argument parsing"""
    parser = setup_parser('Monitors databases and sends a notification email if there have not been '
                          'recent enough updates')

    parser.add_argument('-e', '--email_address', required=True,
                        help='Email address to use to authenticate to the SMTP server and the source email address of '
                             'notification emails.')
    parser.add_argument('-p', '--email_password',
                        help='Email password for the --emailaddress. If not provided, then the SMTP server wont be '
                             'given creds')
    parser.add_argument('-m', '--smtp_server', required=True,
                        help='The SMTP server to use for sending notification emails')
    parser.add_argument('-s', '--secure', action='store_true', help='Use SMTPS instead of SMTP')
    parser.add_argument('-o', '--config', required=True, help='Config file with the dictionary of databases to check. '
                                                              'see config.py in the root for an example')

    return parser.parse_args(_args)


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])

    setup_logging(args.debug, args.verbose)

    cls = DBMonitor(args.conn_str, args.email_address, args.email_password, args.smtp_server, args.secure)

    spec = importlib.util.spec_from_file_location('module', args.config)
    if not spec or not spec.loader:
        logger.error('--config argument not set')
    else:
        if not isinstance(spec.loader, Loader):
            raise AssertionError('Expected spec to be a Loader type')
        cnfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cnfg)
        cls.check(cnfg.config)  # type: ignore
