#!/usr/bin/env python3
import re
import sys
import sqlite3
from base64 import b64encode
from urllib.parse import quote
from typing import List, Dict, Any, Iterable, Optional

ITEM_COUNTER = 0
rx_query = re.compile(r'SELECT([\s\S]*)FROM[\s]+([A-Z_]+)')
rx_cols = re.compile(r'[\s,;](Z[A-Z_]+)')
rx_tags = re.compile(r'\%\{[A-Za-z_]+?\}')

# ===============================
#   Helper methods
# ===============================

def incrItem(value: str, label: str) -> str:
    global ITEM_COUNTER
    ITEM_COUNTER += 1
    return 'item{0}.{1}\r\nitem{0}.X-ABLabel:{2}'.format(
        ITEM_COUNTER, value, label)


def x520(val: str) -> Optional[str]:
    if not val:
        return None
    return val.replace(';', '\\;').replace(',', '\\,')


def buildLabel(
    prefix: str,
    label: str,
    isFirst: bool,
    suffix: str,
    validOther: bool = False,
) -> str:
    typ = ''
    if label == '_$!<Home>!$_':
        typ = ';type=HOME'
    elif label == '_$!<Work>!$_':
        typ = ';type=WORK'
    elif validOther and label == '_$!<Other>!$_':
        typ = ';type=OTHER'

    value = prefix + typ + (';type=pref:' if isFirst else ':') + suffix
    if typ:
        return value
    else:
        return incrItem(value, label)


def sanitize(cursor: sqlite3.Cursor, query: str) -> str:
    cols, table = rx_query.findall(query)[0]
    sel_cols = {x for x in rx_cols.findall(cols)}
    all_cols = {x[1] for x in cursor.execute(f'PRAGMA table_info({table});')}
    missing_cols = sel_cols.difference(all_cols)
    for missing in missing_cols:
        print(f'WARN: column "{missing}" not found in {table}. Ignoring.',
              file=sys.stderr)
        query = query.replace(missing, 'NULL')
    return query

# ===============================
#   VCARD Attributes
# ===============================

class Queryable:  # Protocol
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Iterable['Queryable']:
        raise NotImplementedError()

    def __init__(self, row: List[Any]):
        self._parent = -1
        raise NotImplementedError()

    @property
    def parent(self) -> int:
        return self._parent

    def __repr__(self) -> str:
        return '<{} "{}">'.format(self.__class__.__name__, self.asPrintable())

    def asPrintable(self) -> str:
        return '?'

    def asVCard(self, markPref: bool) -> str:
        raise NotImplementedError()


class Email(Queryable):
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Iterable['Email']:
        return (Email(x) for x in cursor.execute(sanitize(cursor, '''
            SELECT ZOWNER, ZLABEL, ZADDRESS
            FROM ZABCDEMAILADDRESS
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;''')))

    def __init__(self, row: List[Any]):
        self._parent = row[0]  # type: int
        self.label = x520(row[1]) or ''  # type: str
        self.email = x520(row[2]) or ''  # type: str

    def asPrintable(self) -> str:
        return self.email

    def asVCard(self, markPref: bool) -> str:
        return buildLabel(
            'EMAIL;type=INTERNET', self.label, markPref, self.email)


class Phone(Queryable):
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Iterable['Phone']:
        return (Phone(x) for x in cursor.execute(sanitize(cursor, '''
            SELECT ZOWNER, ZLABEL, ZFULLNUMBER
            FROM ZABCDPHONENUMBER
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;''')))

    def __init__(self, row: List[Any]):
        self._parent = row[0]  # type: int
        self.label = x520(row[1]) or ''  # type: str
        self.number = x520(row[2]) or ''  # type: str

    def asPrintable(self) -> str:
        return self.number

    def asVCard(self, markPref: bool) -> str:
        mapping = {
            '_$!<Mobile>!$_': ';type=CELL;type=VOICE',
            'iPhone': ';type=IPHONE;type=CELL;type=VOICE',
            '_$!<Home>!$_': ';type=HOME;type=VOICE',
            '_$!<Work>!$_': ';type=WORK;type=VOICE',
            '_$!<Main>!$_': ';type=MAIN',
            '_$!<HomeFAX>!$_': ';type=HOME;type=FAX',
            '_$!<WorkFAX>!$_': ';type=WORK;type=FAX',
            '_$!<OtherFAX>!$_': ';type=OTHER;type=FAX',
            '_$!<Pager>!$_': ';type=PAGER',
            '_$!<Other>!$_': ';type=OTHER;type=VOICE'
        }
        value = (';type=pref:' if markPref else ':') + self.number
        if self.label in mapping.keys():
            return 'TEL' + mapping[self.label] + value
        else:
            return incrItem('TEL' + value, self.label)


class Address(Queryable):
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Iterable['Address']:
        return (Address(x) for x in cursor.execute(sanitize(cursor, '''
            SELECT ZOWNER, ZLABEL,
                ZSTREET, ZCITY, ZSTATE, ZZIPCODE, ZCOUNTRYNAME
            FROM ZABCDPOSTALADDRESS
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;''')))

    def __init__(self, row: List[Any]):
        self._parent = row[0]  # type: int
        self.label = x520(row[1]) or ''  # type: str
        self.street = x520(row[2]) or ''  # type: str
        self.city = x520(row[3]) or ''  # type: str
        self.state = x520(row[4]) or ''  # type: str
        self.zip = x520(row[5]) or ''  # type: str
        self.country = x520(row[6]) or ''  # type: str

    def asPrintable(self) -> str:
        return ', '.join(filter(None, (
            self.street, self.city, self.state, self.zip, self.country)))

    def asVCard(self, markPref: bool) -> str:
        value = ';'.join((
            self.street, self.city, self.state, self.zip, self.country))
        return buildLabel(
            'ADR', self.label, markPref, ';;' + value, validOther=True)


class SocialProfile(Queryable):
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Iterable['SocialProfile']:
        return (SocialProfile(x) for x in cursor.execute(sanitize(cursor, '''
            SELECT ZOWNER, ZSERVICENAME, ZUSERNAME
            FROM ZABCDSOCIALPROFILE;''')))

    def __init__(self, row: List[Any]):
        self._parent = row[0]  # type: int
        self.service = row[1] or ''  # type: str
        # no x520(); actually, Apple does that ... and it breaks on reimport
        self.user = row[2] or ''  # type: str

    def asPrintable(self) -> str:
        return self.service + ':' + self.user

    def asVCard(self, markPref: bool) -> str:
        # Apple does some x-user, x-apple, and url stuff that is wrong
        return 'X-SOCIALPROFILE;type=' + self.service.lower() + ':' + self.user


class Note(Queryable):
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Iterable['Note']:
        return (Note(x) for x in cursor.execute(sanitize(cursor, '''
            SELECT ZCONTACT, ZTEXT
            FROM ZABCDNOTE
            WHERE ZTEXT IS NOT NULL;''')))

    def __init__(self, row: List[Any]):
        self._parent = row[0]  # type: int
        self.text = x520(row[1]) or ''  # type: str

    def asPrintable(self) -> str:
        return self.text

    def asVCard(self, markPref: bool) -> str:
        return self.text


class URL(Queryable):
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Iterable['URL']:
        return (URL(x) for x in cursor.execute(sanitize(cursor, '''
            SELECT ZOWNER, ZLABEL, ZURL
            FROM ZABCDURLADDRESS
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;''')))

    def __init__(self, row: List[Any]):
        self._parent = row[0]  # type: int
        self.label = x520(row[1]) or ''  # type: str
        self.url = x520(row[2]) or ''  # type: str

    def asPrintable(self) -> str:
        return self.url

    def asVCard(self, markPref: bool) -> str:
        return buildLabel('URL', self.label, markPref, self.url)


class Service(Queryable):
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Iterable['Service']:
        return (Service(x) for x in cursor.execute(sanitize(cursor, '''
            SELECT ZOWNER, ZSERVICENAME, ZLABEL, ZADDRESS
            FROM ZABCDMESSAGINGADDRESS
            INNER JOIN ZABCDSERVICE ON ZSERVICE = ZABCDSERVICE.Z_PK
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;''')))

    def __init__(self, row: List[Any]):
        self._parent = row[0]  # type: int
        self.service = row[1] or ''  # type: str
        if self.service.endswith('Instant'):
            self.service = self.service[:-7]  # drop suffix
        self.label = x520(row[2]) or ''  # type: str
        self.username = x520(row[3]) or ''  # type: str

    def asPrintable(self) -> str:
        return ', '.join((self.service, self.label, self.username))

    def isSpecial(self) -> bool:
        return self.service in ['Jabber', 'MSN', 'Yahoo', 'ICQ']

    def asSpecialStr(self, markPref: bool) -> str:
        return buildLabel('X-' + self.service.upper(), self.label, markPref,
                          self.username)

    def asVCard(self, markPref: bool) -> str:
        if self.service in ['Jabber', 'GoogleTalk', 'Facebook']:
            typ = 'xmpp'
        elif self.service in ['GaduGadu', 'QQ']:
            typ = 'x-apple'
        elif self.service == 'ICQ':
            typ = 'aim'
        elif self.service == 'MSN':
            typ = 'msnim'
        elif self.service == 'Skype':
            typ = 'skype'
        elif self.service == 'Yahoo':
            typ = 'ymsgr'
        else:
            raise NotImplementedError('Unkown Service: ' + self.service)

        # Dear Apple, why do you do such weird shit, URL encoding? bah!
        # Even worse, you break it so that reimport fails.
        # user = quote(self.username, safe='!/()=_:.\'$&').replace('%2C', '\\,')
        user = self.username
        return buildLabel('IMPP;X-SERVICE-TYPE=' + self.service, self.label,
                          markPref, typ + ':' + user)


# ===============================
#   VCARD main
# ===============================

class Record:
    @staticmethod
    def queryAll(cursor: sqlite3.Cursor) -> Dict[int, 'Record']:
        # get z_ent id that is used for contact cards
        z_ent = cursor.execute(
            'SELECT Z_ENT FROM Z_PRIMARYKEY WHERE Z_NAME == "ABCDContact"'
        ).fetchone()[0]
        # find all records that match this id
        return {x[0]: Record(x) for x in cursor.execute(sanitize(cursor, '''
            SELECT Z_PK,
                ZFIRSTNAME, ZLASTNAME, ZMIDDLENAME, ZTITLE, ZSUFFIX,
                ZNICKNAME, ZMAIDENNAME,
                ZPHONETICFIRSTNAME, ZPHONETICMIDDLENAME, ZPHONETICLASTNAME,
                ZPHONETICORGANIZATION, ZORGANIZATION, ZDEPARTMENT, ZJOBTITLE,
                strftime('%Y-%m-%d', ZBIRTHDAY + 978307200, 'unixepoch'),
                ZTHUMBNAILIMAGEDATA, ZDISPLAYFLAGS
            FROM ZABCDRECORD
            WHERE Z_ENT = ?;'''), [z_ent])}

    @staticmethod
    def initEmpty(id: int) -> 'Record':
        return Record([id] + [None] * 17)

    def __init__(self, row: List[Any]) -> None:
        self.id = row[0]  # type: int
        self.firstname = x520(row[1]) or ''  # type: str
        self.lastname = x520(row[2]) or ''  # type: str
        self.middlename = x520(row[3]) or ''  # type: str
        self.nameprefix = x520(row[4]) or ''  # type: str
        self.namesuffix = x520(row[5]) or ''  # type: str
        self.nickname = x520(row[6])  # type: Optional[str]
        self.maidenname = x520(row[7])  # type: Optional[str]
        self.phonetic_firstname = x520(row[8])  # type: Optional[str]
        self.phonetic_middlename = x520(row[9])  # type: Optional[str]
        self.phonetic_lastname = x520(row[10])  # type: Optional[str]
        self.phonetic_org = x520(row[11])  # type: Optional[str]
        self.organization = x520(row[12]) or ''  # type: str
        self.department = x520(row[13]) or ''  # type: str
        self.jobtitle = x520(row[14])  # type: Optional[str]
        self.bday = row[15]  # type: Optional[str]
        self.email = []  # type: List[Email]
        self.phone = []  # type: List[Phone]
        self.address = []  # type: List[Address]
        self.socialprofile = []  # type: List[SocialProfile]
        self.note = None  # type: Optional[str]
        self.urls = []  # type: List[URL]
        self.service = []  # type: List[Service]
        self.image = row[16]  # type: Optional[bytes]
        display_flags = row[17] or 0  # type: int
        self.iscompany = bool(display_flags & 1)  # type: bool
        self.fullname = self.organization if self.iscompany else ' '.join(
            filter(None, [self.nameprefix, self.firstname, self.middlename,
                          self.lastname, self.namesuffix]))

    def __repr__(self) -> str:
        return self.makeVCard()

    def formatFilename(self, format: str) -> str:
        matches = rx_tags.findall(format)
        for tag in matches:
            value = getattr(self, tag[2:-1])
            if isinstance(value, list):
                value = value[0] if len(value) else None
            if isinstance(value, Queryable):
                value = value.asPrintable()
            format = format.replace(tag, str(value or '').replace('/', ':'))
        return format

    def makeVCard(self) -> str:
        global ITEM_COUNTER
        ITEM_COUNTER = 0

        # rquired fields: BEGIN, END, VERSION, N, FN
        data = [
            'BEGIN:VCARD',
            'VERSION:3.0',
            'N:' + ';'.join((self.lastname, self.firstname, self.middlename,
                             self.nameprefix, self.namesuffix)),
            'FN:' + self.fullname,
        ]

        def optional(key: str, value: Optional[str]) -> None:
            if value:
                data.append(key + ':' + value)

        def optionalArray(arr: Iterable[Queryable]) -> None:
            isFirst = True
            for x in arr:
                data.append(x.asVCard(markPref=isFirst))
                isFirst = False

        optional('NICKNAME', self.nickname)
        optional('X-MAIDENNAME', self.maidenname)
        optional('X-PHONETIC-FIRST-NAME', self.phonetic_firstname)
        optional('X-PHONETIC-MIDDLE-NAME', self.phonetic_middlename)
        optional('X-PHONETIC-LAST-NAME', self.phonetic_lastname)
        if self.organization or self.department:
            optional('ORG', self.organization + ';' + self.department)
        optional('X-PHONETIC-ORG', self.phonetic_org)
        optional('TITLE', self.jobtitle)
        optionalArray(self.email)
        optionalArray(self.phone)
        optionalArray(self.address)
        optionalArray(self.socialprofile)
        optional('NOTE', self.note)
        optionalArray(self.urls)

        if self.bday:
            key = 'BDAY'
            if self.bday.startswith('1604'):
                key += ';X-APPLE-OMIT-YEAR=1604'
            optional(key, self.bday)

        for kind in ['Jabber', 'MSN', 'Yahoo', 'ICQ']:
            isFirst = True
            for x in self.service:
                if x.service == kind:
                    data.append(x.asSpecialStr(markPref=isFirst))
                    isFirst = False
        optionalArray(self.service)

        if self.image:
            try:
                data.append(self.imageAsBase64(self.image))
            except NotImplementedError:
                print('''Image format not supported.
 Could not extract image for contact: {}
 @: {!r}...
 skipping.'''.format(self.fullname, self.image[:20]), file=sys.stderr)
        if self.iscompany:
            data.append('X-ABShowAs:COMPANY')
        data.append('END:VCARD')
        return '\r\n'.join(data) + '\r\n'

    def imageAsBase64(self, image: bytes) -> str:
        img = image[1:]  # why does Apple prepend \x01 to all images?!
        t = 'PHOTO;ENCODING=b;TYPE='
        if img[6:10] == b'JFIF':
            t += 'JPEG:' + b64encode(img).decode('ascii')
        else:
            raise NotImplementedError(
                'Image types other than JPEG are not supported yet.')
        # place 'P' manually for nice 75 char alignment
        return t[0] + '\r\n '.join(t[i:i + 74] for i in range(1, len(t), 74))


# ===============================
#   Main Entry
# ===============================

class ABCDDB:
    @staticmethod
    def load(db_path: str) -> List['Record']:
        db = sqlite3.connect(db_path)
        cur = db.cursor()

        records = Record.queryAll(cur)

        def _getOrMake(attr: Queryable) -> Record:
            rec = records.get(attr.parent)
            if not rec:
                rec = Record.initEmpty(attr.parent)
                records[attr.parent] = rec
                print('Found unreferenced data field:', attr, file=sys.stderr)
            return rec

        # query once, then distribute
        for email in Email.queryAll(cur):
            _getOrMake(email).email.append(email)

        for phone in Phone.queryAll(cur):
            _getOrMake(phone).phone.append(phone)

        for address in Address.queryAll(cur):
            _getOrMake(address).address.append(address)

        for social in SocialProfile.queryAll(cur):
            _getOrMake(social).socialprofile.append(social)

        for note in Note.queryAll(cur):
            _getOrMake(note).note = note.text

        for url in URL.queryAll(cur):
            _getOrMake(url).urls.append(url)

        for service in Service.queryAll(cur):
            _getOrMake(service).service.append(service)

        db.close()
        return list(records.values())
