"""
This file contains code which mimics a class that represents a pure python interface with the database.

This is a good example of how our business logic can be completely seperate from our API.
"""
import json, time
from typing import Self
from pydantic import EmailStr, BaseModel


class Contact:
    # Mocks the database connection
    # This is a class variable that all instantiations have access to
    db: dict[int, Self] = {}

    def __init__(self, id_=None, first=None, last=None, phone=None, email=None):
        self.id = id_
        self.first = first
        self.last = last
        self.phone = phone
        self.email = email
        self.errors = {}


    def update(self, first, last, phone, email):
        self.first = first
        self.last = last
        self.phone = phone
        self.email = email


    def validate(self):
        self.errors.pop('email', None)
        if not self.email:
            self.errors['email'] = "Email Required"
        class Email(BaseModel):
            email: EmailStr
        try:
            temp = Email(email=self.email)
        except Exception as e:
            print(e)
            self.errors['email'] = 'Not Valid Email'
        existing_contact = next(filter(lambda c: c.id != self.id and c.email == self.email, Contact.db.values()), None)
        if existing_contact:
            self.errors['email'] = "Email Must Be Unique"
        return len(self.errors) == 0


    def save(self):
        if not self.validate():
            return False
        if self.id is None:
            if len(Contact.db) == 0:
                max_id = 1
            else:
                max_id = max(contact.id for contact in Contact.db.values())
            self.id = max_id + 1
            Contact.db[self.id] = self
        Contact.save_db()
        return True


    def delete(self):
        del Contact.db[self.id]
        Contact.save_db()


    # Search Functions

    @classmethod
    def all(cls):
        return list(cls.db.values())

    @classmethod
    def search(cls, text):
        result = []
        for c in cls.db.values():
            match_first = c.first is not None and text in c.first
            match_last = c.last is not None and text in c.last
            match_email = c.email is not None and text in c.email
            match_phone = c.phone is not None and text in c.phone
            if match_first or match_last or match_email or match_phone:
                result.append(c)
        return result

    @classmethod
    def find(cls, id_):
        id_ = int(id_)
        c = cls.db.get(id_)
        if c is not None:
            c.errors = {}

        return c

    @classmethod
    def count(cls):
        time.sleep(2)
        return len(cls.db)

    # Mock persistent storage
    @classmethod
    def load_db(cls):
        with open('contacts.json', 'r') as contacts_file:
            contacts = json.load(contacts_file)
            cls.db.clear()
            for c in contacts:
                cls.db[c['id']] = Contact(c['id'], c['first'], c['last'], c['phone'], c['email'])

    @staticmethod
    def save_db():
        out_arr = [c.__dict__ for c in Contact.db.values()]
        with open("contacts.json", "w") as f:
            json.dump(out_arr, f, indent=2)
