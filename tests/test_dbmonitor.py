"""Test suite for dbmonitor.py"""
import poplib
import uuid
from email import parser

import pytest

from dbmonitor import DBMonitor


def test_check_db_success(test_db, email_username, notification_window):
    """Test case where a notification should not be generated"""
    table_config = [
        {'table_name': 'testtablegood',
         'date_col': 'DATETIME',
         'notification_mins': notification_window,
         'email': email_username
         }
    ]

    # this should not send an email, and will fail with these creds if it tries
    cls = DBMonitor(conn_str=test_db, email_user='xxx', email_pass='xxx')
    cls.check(configs=table_config)


def test_check_db_failure(test_db, email_username, email_password, notification_window):
    """Test case where a notification should be generated"""
    table_config = [
        {'table_name': 'testtablefail',
         'date_col': 'DATETIME',
         'notification_mins': notification_window,
         'email': email_username
         }
    ]
    cls = DBMonitor(conn_str=test_db, email_user=email_username, email_pass=email_password)
    cls.check(configs=table_config)


def send_notification(email_username, email_password, smtp_server, pop_server,  # pylint:disable=too-many-arguments
                      notification_window, secure: bool):
    """Helper for test_send_notification_secure and test_send_notification_unsecure"""
    cls = DBMonitor('sqlite://', email_username, email_password, smtp_server)

    # send a unique id so we make sure we get the right email
    unique_id = str(uuid.uuid4())
    cls.send_notification([email_username], unique_id, notification_window, secure)

    pop_conn = poplib.POP3_SSL(pop_server)
    pop_conn.user(email_username)
    pop_conn.pass_(email_password)

    # Get messages from server:
    messages = [parser.BytesParser().parsebytes(mssg)
                for mssg in [b"\n".join(mssg[1])
                             for mssg in [pop_conn.retr(i)
                                          for i in range(1, len(pop_conn.list()[1]) + 1)]]]

    exp_subj = 'Database dataflow failure: {table}'.format(table=unique_id)
    assert messages[-1]['subject'] == exp_subj, "Unexpected email subject.\nExpected: {}.\nActual: {}".format(
        exp_subj, messages[-1]['subject']
    )
    pop_conn.quit()


def test_send_notification_secure(email_username, email_password, smtp_server, pop_server, notification_window):
    """Sends a test notification and checks the test email account for the notification using SMTPS"""
    send_notification(email_username, email_password, smtp_server, pop_server, notification_window, True)


@pytest.mark.skip(reason="Gmail doesn't support unsecure protocols")
def test_send_notification_unsecure(email_username, email_password, smtp_server, pop_server, notification_window):
    """Sends a test notification and checks the test email account for the notification using SMTP"""
    send_notification(email_username, email_password, smtp_server, pop_server, notification_window, False)


def test_check_required_arguments(test_db):
    """Tests that an exception is thrown when missing arguments are missing"""
    with pytest.raises(ValueError):
        DBMonitor(conn_str=test_db, email_user=None, email_pass=None, smtp_server=None)
