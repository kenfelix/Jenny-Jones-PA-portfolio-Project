#!/usr/bin/env python3
"""Auth Module"""

from db.db import DB
from model.model import User, PA, Schedule
from typing import Union
from bcrypt import hashpw, gensalt, checkpw
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid4


def _hash_password(password: str) -> bytes:
    """Returns a salted hash of
    the input password"""
    hashed_password = hashpw(password.encode('utf-8'), gensalt())

    return hashed_password


def _generate_uuid() -> str:
    """return a string representation of a new UUID"""
    uid = str(uuid4())
    return uid


class Auth:
    """Auth class to interact with the authentication database.
    """

    def __init__(self):
        self._db = DB()

    def register_user(self, email: str, password: str, \
        first_name: str, last_name: str, date_of_birth: str) -> User:
        """creates a new user"""
        custom_url = _generate_uuid()
        try:
            user = self._db.find_user_by(email=email)
            if user:
                raise ValueError("User {} already exists".format(email))
        except NoResultFound:
            hashed_password = _hash_password(password)
            new_user = self._db.add_user(email, hashed_password, first_name, last_name, date_of_birth, custom_url)
            return new_user

    def create_session(self, email: str) -> str:
        """returns the session ID as a string."""
        try:
            user = self._db.find_user_by(email=email)
        except NoResultFound:
            return None

        session_id = _generate_uuid()
        self._db.update_user(user.id, session_id=session_id, login=True)

        return session_id

    def valid_login(self, email: str, password: str) -> bool:
        """returns true if user is valid"""
        try:
            user= self._db.find_user_by(email=email)
            return checkpw(
                    password.encode('utf-8'),
                    user.hashed_password
                    )
        except NoResultFound:
            return False

    def get_user_from_session_id(self, session_id: str) -> Union[User, None]:
        """
        finds a user using the session id
        """
        if session_id is None:
            return None
        
        try:
            user = self._db.find_user_by(session_id=session_id)
            return user
        except NoResultFound:
            return None

    def destroy_session(self, user_id: int) -> None:
        """updates the corresponding user’s session ID to None"""
        if user_id is None:
            return None

        try:
            user = self._db.find_user_by(id=user_id)
            self._db.update_user(user.id, session_id=None, login=False)
            return None
        except NoResultFound:
            return None

    def get_reset_password_token(self, email: str) -> str:
        """
        Generates a reset password token for a user
        """
        try:
            user = self._db.find_user_by(email=email)
        except NoResultFound:
            raise ValueError

        reset_token = _generate_uuid()
        self._db.update_user(user.id, reset_token=reset_token)
        return reset_token

    def update_password(self, reset_token: str, password: str) -> None:
        """Updates a user's password"""
        if reset_token is None or password is None:
            return None

        try:
            user = self._db.find_user_by(reset_token=reset_token)
        except NoResultFound:
            raise ValueError

        hashed_password = _hash_password(password)
        self._db.update_user(user.id,
                             hashed_password=hashed_password,
                             reset_token=None)

    def create_schedule(self, session_id: str, title : str, description: str, start_date: str, \
        end_date: str, start_time: str, end_time: str, venue: str):
        user = self._db.find_user_by(session_id=session_id)
        schedule = Schedule(title=title, description=description,\
            start_date=start_date, end_date=end_date, start_time=start_time, end_time=end_time, venue=venue)
        user.schedules.append(schedule)
        self._db._session.commit()
        return schedule

    def remove_schedule(self, session_id: str, id: int):
        user = self._db.find_user_by(session_id=session_id)
        schedule = self._db.find_schedule_by(user_id=user.id, id=id)
        self._db._session.delete(schedule)
        self._db._session.commit()