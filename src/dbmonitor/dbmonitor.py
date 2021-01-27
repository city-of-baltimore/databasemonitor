"""Database monitoring tool that notifies when there are not expected new entries"""
import logging
import smtplib
import ssl
from datetime import datetime, timedelta
from typing import List, TypedDict

from sqlalchemy import create_engine, select, Column, DateTime, MetaData, Table  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

LOGGER = logging.getLogger(__name__)


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

    def __init__(self, conn_str: str, email_user: str, email_pass: str, smtp_server: str = "smtp.gmail.com"):
        """
        :param conn_str: SqlAlchemy connection string
        :param email_user: Username for SMTP server
        :param email_pass: Password for SMTP server
        """
        self.engine = create_engine(conn_str, echo=True, future=True)
        self.email_user = email_user
        self.email_pass = email_pass
        self.smtp_server = smtp_server

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

                stmt = select(table).where(table.columns[config['date_col']] >=  # pylint:disable=unsubscriptable-object
                                           (datetime.now() - timedelta(seconds=config['notification_mins'])))
                result = session.execute(stmt).fetchall()

                if len(result) == 0:
                    self.send_notification([config['email']],
                                           config['table_name'],
                                           config['notification_mins'])

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

    def send_notification(self, recipient_addresses: List[str], table_name: str, notification_mins: int) -> None:
        """
        Sends a notification to the included email address
        :param recipient_addresses: List of email addresses to send the notification to
        :param table_name: Table that we were checking. This is only used for the email text.
        :param notification_mins: Number of minutes since we expected the last entry. This is only used for the email
        text
        :return:
        """
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL(self.smtp_server, 465, context=context) as server:
            server.login(self.email_user, self.email_pass)
            for addr in recipient_addresses:
                server.sendmail(self.email_user, addr,
                                "Subject: Database dataflow failure: {table}\n\nDataflow failure in DOT_DATA.{table}. "
                                "No data in last {ns} seconds, which was unexpected".format(
                                    table=table_name, ns=notification_mins))
