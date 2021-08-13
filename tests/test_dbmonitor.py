"""Test suite for dbmonitor.py"""
import os
import poplib
import uuid
from email import parser
from unittest import mock

import pytest
from loguru import logger

from dbmonitor import DBMonitor
from dbmonitor.dbmonitor import parse_args, setup_logging


def test_check_db_success(test_db, notification_window):
    """Test case where a notification should not be generated"""
    table_config = [
        {'table_name': 'testtablegood',
         'date_col': 'DATETIME',
         'notification_mins': notification_window,
         'email': 'dummyusername'
         }
    ]

    with mock.patch('dbmonitor.DBMonitor.send_notification') as send_notification_mock:
        # this should not send an email, and will fail with these creds if it tries
        cls = DBMonitor(conn_str=test_db, email_user='xxx', email_pass='xxx')
        cls.check(configs=table_config)
        send_notification_mock.assert_not_called()


def test_check_db_failure(test_db, notification_window):
    """Test case where a notification should be generated"""
    table_config = [
        {'table_name': 'testtablefail',
         'date_col': 'DATETIME',
         'notification_mins': notification_window,
         'email': 'dummyusername'
         }
    ]

    with mock.patch('dbmonitor.DBMonitor.send_notification') as send_notification_mock:
        cls = DBMonitor(conn_str=test_db, email_user='dummyusername', email_pass='dummypassword')
        cls.check(configs=table_config)
        send_notification_mock.assert_called_once()


def test_check_db_dne(test_db, notification_window):
    """Test case where the table doesn't exist"""
    table_config = [
        {'table_name': 'table_dne',
         'date_col': 'DATETIME',
         'notification_mins': notification_window,
         'email': 'dummyusername'
         }
    ]

    with mock.patch('dbmonitor.DBMonitor.send_notification') as send_notification_mock:
        cls = DBMonitor(conn_str=test_db, email_user='dummyusername', email_pass='dummypassword')
        cls.check(configs=table_config)
        send_notification_mock.assert_called_once()


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


def test_setup_logging(tmp_path_factory):
    """Tests setup_logging"""
    def verify_log_size(log_path, size):
        logs = log_path.glob('logs/file-*.log')
        for log in logs:
            assert os.path.getsize(log) >= size * .9
            assert os.path.getsize(log) <= size * 1.1

    # test to make sure warning logs, but not info or debug
    path = tmp_path_factory.getbasetemp() / 'warn'
    setup_logging(False, False, path)
    logger.warning('Test log')
    logger.info('Test log')
    logger.debug('Test log)')
    verify_log_size(path, 700)

    # test to make sure warning and info logs, but not debug
    path = tmp_path_factory.getbasetemp() / 'info'
    setup_logging(False, True, path)
    logger.warning('Test log')
    logger.info('Test log')
    logger.debug('Test log)')
    verify_log_size(path, 1400)

    # test to make sure everything up to debug logs
    path = tmp_path_factory.getbasetemp() / 'debug'
    setup_logging(True, True, path)
    logger.warning('Test log')
    logger.info('Test log')
    logger.debug('Test log)')
    verify_log_size(path, 2100)


def test_parse_args():
    """Tests parse_args"""
    conn_str = 'conn_str'
    email_addr = 'email_addr'
    email_password = 'email_password'
    smtp_server = 'smtp_server'
    config = 'config.py'

    args = parse_args(['-v', '-vv', '-s', '--conn_str', conn_str, '--email_address', email_addr, '--smtp_server',
                       smtp_server, '--config', config])

    assert args.debug
    assert args.verbose
    assert args.conn_str == conn_str
    assert args.email_address == email_addr
    assert args.smtp_server == smtp_server
    assert args.secure
    assert args.config == config

    args = parse_args(['--conn_str', conn_str, '--email_address', email_addr, '--email_password', email_password,
                       '--smtp_server', smtp_server, '--config', config])

    assert not args.debug
    assert not args.verbose
    assert args.conn_str == conn_str
    assert args.email_address == email_addr
    assert args.smtp_server == smtp_server
    assert not args.secure
    assert args.config == config
    assert args.email_password == email_password
