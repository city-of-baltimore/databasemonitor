"""Pytest fixtures"""
from datetime import datetime, timedelta
import pytest

from sqlalchemy import Column, create_engine  # type: ignore
from sqlalchemy.ext.declarative import DeclarativeMeta  # type: ignore
from sqlalchemy.ext.declarative import declarative_base  # type: ignore
from sqlalchemy.types import DateTime, Integer  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

Base: DeclarativeMeta = declarative_base()


class TestTableGood(Base):  # pylint:disable=too-few-public-methods
    """Table used for the successful test case with recent activity"""
    __tablename__ = 'testtablegood'

    ID = Column(Integer, primary_key=True)
    DATETIME = Column(DateTime)


class TestTableFail(Base):  # pylint:disable=too-few-public-methods
    """Table used for the unsuccessful test case with no recent activity"""
    __tablename__ = 'testtablefail'

    ID = Column(Integer, primary_key=True)
    DATETIME = Column(DateTime)


def pytest_addoption(parser):
    """Adds command line options"""
    # this account is only used for testing, so hard coding creds is fine
    parser.addoption('--email_username', action='store')
    parser.addoption('--email_password', action='store')
    parser.addoption('--pop_server', action='store')
    parser.addoption('--smtp_server', action='store')


@pytest.fixture(name='email_username')
def email_username_fixture(request):
    """email username fixture (smtp and pop)"""
    return request.config.getoption('email_username', skip=True)


@pytest.fixture(name='email_password')
def email_password_fixture(request):
    """email password fixture (smtp and pop)"""
    return request.config.getoption('email_password', skip=True)


@pytest.fixture(name='smtp_server')
def smtp_server_fixture(request):
    """SMTP password fixture"""
    return request.config.getoption('smtp_server')


@pytest.fixture(name='pop_server')
def pop_server_fixture(request):
    """POP password fixture"""
    return request.config.getoption('pop_server')


@pytest.fixture(name='notification_window')
def notification_window_fixture():
    """Constant used as the notification_mins value in tests"""
    return 30000


@pytest.fixture()
def test_db(notification_window, tmp_path_factory):
    """Fixture that sets up test database"""
    conn_str = 'sqlite:///{}.db'.format(str(tmp_path_factory.mktemp('data') / 'database.db'))
    engine = create_engine(conn_str, echo=True, future=True)

    with engine.begin() as connection:
        Base.metadata.create_all(connection)

    with Session(bind=engine, future=True) as session:
        for i in range(10):
            # add data for passing test
            session.add(TestTableGood(DATETIME=datetime.now() - timedelta(minutes=240 + (60 * i))))

        for i in range(10):
            # add data for failing test
            session.add(TestTableFail(DATETIME=datetime.now() - timedelta(minutes=notification_window + (60 * i))))

        session.commit()

    yield conn_str
