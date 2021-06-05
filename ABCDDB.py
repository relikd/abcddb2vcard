#!/usr/bin/env python3
import sys
import sqlite3
from base64 import b64encode
from urllib.parse import quote

PROD_ID = '-//Apple Inc.//Mac OS X 10.15.7//EN'
ITEM_COUNTER = 0


class ABCDDB(object):
    @staticmethod
    def load(db_path):
        db = sqlite3.connect(db_path)
        cur = db.cursor()

        records = Record.queryAll(cur)

        # query once, then distribute
        for x in Email.queryAll(cur):
            records[x.parent].email.append(x)

        for x in Phone.queryAll(cur):
            records[x.parent].phone.append(x)

        for x in Address.queryAll(cur):
            records[x.parent].address.append(x)

        for x in SocialProfile.queryAll(cur):
            records[x.parent].socialprofile.append(x)

        for x in Note.queryAll(cur):
            records[x.parent].note = x.text

        for x in URL.queryAll(cur):
            records[x.parent].urls.append(x)

        for x in Service.queryAll(cur):
            records[x.parent].service.append(x)

        db.close()
        return records.values()


def incrItem(value, label):
    global ITEM_COUNTER
    ITEM_COUNTER += 1
    return 'item{0}.{1}\r\nitem{0}.X-ABLabel:{2}'.format(
        ITEM_COUNTER, value, label)


def x520(val):
    if not val:
        return None
    return val.replace(';', '\\;').replace(',', '\\,')


def buildLabel(prefix, label, isFirst, suffix, validOther=False):
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


class Record(object):
    @staticmethod
    def queryAll(cursor):
        return {x[0]: Record(x) for x in cursor.execute('''
            SELECT Z_PK,
                ZFIRSTNAME, ZLASTNAME, ZMIDDLENAME, ZTITLE, ZSUFFIX,
                ZNICKNAME, ZMAIDENNAME,
                ZPHONETICFIRSTNAME, ZPHONETICMIDDLENAME, ZPHONETICLASTNAME,
                ZPHONETICORGANIZATION, ZORGANIZATION, ZDEPARTMENT, ZJOBTITLE,
                strftime('%Y-%m-%d', ZBIRTHDAY + 978307200, 'unixepoch'),
                ZTHUMBNAILIMAGEDATA, ZDISPLAYFLAGS
            FROM ZABCDRECORD
            WHERE ZCONTAINER1 IS NOT NULL;''')}

    def __init__(self, row):
        self.id = row[0]
        self.firstname = x520(row[1]) or ''
        self.lastname = x520(row[2]) or ''
        self.middlename = x520(row[3]) or ''
        self.nameprefix = x520(row[4]) or ''
        self.namesuffix = x520(row[5]) or ''
        self.nickname = x520(row[6])
        self.maidenname = x520(row[7])
        self.phonetic_firstname = x520(row[8])
        self.phonetic_middlename = x520(row[9])
        self.phonetic_lastname = x520(row[10])
        self.phonetic_org = x520(row[11])
        self.organization = x520(row[12]) or ''
        self.department = x520(row[13]) or ''
        self.jobtitle = x520(row[14])
        self.bday = row[15]
        self.email = []
        self.phone = []
        self.address = []
        self.socialprofile = []
        self.note = None
        self.urls = []
        self.service = []
        self.image = row[16]
        self.iscompany = row[17] & 1

    def __repr__(self):
        return self.makeVCard()

    def makeVCard(self):
        global ITEM_COUNTER
        ITEM_COUNTER = 0
        t = 'BEGIN:VCARD\r\nVERSION:3.0'
        t += '\r\nPRODID:' + PROD_ID

        def optional(key, value):
            nonlocal t
            if value:
                t += '\r\n' + key + ':' + value

        def optionalArray(arr):
            nonlocal t
            isFirst = True
            for x in arr:
                t += '\r\n' + x.asStr(markPref=isFirst)
                isFirst = False

        t += '\r\nN:' + ';'.join((self.lastname, self.firstname,
                                  self.middlename, self.nameprefix,
                                  self.namesuffix))
        if self.iscompany:
            fullname = self.organization
        else:
            fullname = ' '.join(filter(None, [
                self.nameprefix, self.firstname, self.middlename,
                self.lastname, self.namesuffix]))

        t += '\r\nFN:' + fullname
        optional('NICKNAME', self.nickname)
        optional('X-MAIDENNAME', self.maidenname)
        optional('X-PHONETIC-FIRST-NAME', self.phonetic_firstname)
        optional('X-PHONETIC-MIDDLE-NAME', self.phonetic_middlename)
        optional('X-PHONETIC-LAST-NAME', self.phonetic_lastname)

        if self.organization or self.department:
            t += '\r\nORG:' + self.organization + ';' + self.department

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
            t += '\r\n' + key + ':' + self.bday

        for kind in ['Jabber', 'MSN', 'Yahoo', 'ICQ']:
            isFirst = True
            for x in self.service:
                if x.service == kind:
                    t += '\r\n' + x.asSpecialStr(markPref=isFirst)
                    isFirst = False
        optionalArray(self.service)

        if self.image:
            try:
                t += '\r\n' + self.imageAsBase64()
            except NotImplementedError:
                print('''Image format not supported.
 Could not extract image for contact: {}
 @: {}...
 skipping.'''.format(fullname, self.image[:20]), file=sys.stderr)
        if self.iscompany:
            t += '\r\nX-ABShowAs:COMPANY'
        return t + '\r\nEND:VCARD\r\n'

    def imageAsBase64(self):
        if not self.image:
            return
        img = self.image[1:]  # why does Apple prepend \x01 to all images?!
        t = 'PHOTO;ENCODING=b;TYPE='
        if img[6:10] == b'JFIF':
            t += 'JPEG:' + b64encode(img).decode('ascii')
        else:
            raise NotImplementedError(
                'Image types other than JPEG are not supported yet.')
        # place 'P' manually for nice 75 char alignment
        return t[0] + '\r\n '.join(t[i:i + 74] for i in range(1, len(t), 74))


class Email(object):
    @staticmethod
    def queryAll(cursor):
        return (Email(x) for x in cursor.execute('''
            SELECT ZOWNER, ZLABEL, ZADDRESS
            FROM ZABCDEMAILADDRESS
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;'''))

    def __init__(self, row):
        self.parent = row[0]
        self.label = x520(row[1])
        self.email = x520(row[2])

    def asStr(self, markPref):
        return buildLabel('EMAIL;type=INTERNET', self.label, markPref,
                          self.email)


class Phone(object):
    @staticmethod
    def queryAll(cursor):
        return (Phone(x) for x in cursor.execute('''
            SELECT ZOWNER, ZLABEL, ZFULLNUMBER
            FROM ZABCDPHONENUMBER
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;'''))

    def __init__(self, row):
        self.parent = row[0]
        self.label = x520(row[1])
        self.number = x520(row[2])

    def asStr(self, markPref):
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


class Address(object):
    @staticmethod
    def queryAll(cursor):
        return (Address(x) for x in cursor.execute('''
            SELECT ZOWNER, ZLABEL,
                ZSTREET, ZCITY, ZSTATE, ZZIPCODE, ZCOUNTRYNAME
            FROM ZABCDPOSTALADDRESS
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;'''))

    def __init__(self, row):
        self.parent = row[0]
        self.label = x520(row[1])
        self.street = x520(row[2]) or ''
        self.city = x520(row[3]) or ''
        self.state = x520(row[4]) or ''
        self.zip = x520(row[5]) or ''
        self.country = x520(row[6]) or ''

    def asStr(self, markPref):
        value = ';'.join((self.street, self.city, self.state, self.zip,
                          self.country))
        return buildLabel('ADR', self.label, markPref, ';;' + value,
                          validOther=True)


class SocialProfile(object):
    @staticmethod
    def queryAll(cursor):
        return (SocialProfile(x) for x in cursor.execute('''
            SELECT ZOWNER, ZSERVICENAME, ZUSERNAME
            FROM ZABCDSOCIALPROFILE;'''))

    def __init__(self, row):
        self.parent = row[0]
        self.service = row[1]
        # no x520(); actually, Apple does that ... and it breaks on reimport
        self.user = row[2]  # Apple: x520()

    def asStr(self, markPref):
        # Apple does some x-user, x-apple, and url stuff that is wrong
        return 'X-SOCIALPROFILE;type=' + self.service.lower() + ':' + self.user


class Note(object):
    @staticmethod
    def queryAll(cursor):
        return (Note(x) for x in cursor.execute('''
            SELECT ZCONTACT, ZTEXT
            FROM ZABCDNOTE
            WHERE ZTEXT IS NOT NULL;'''))

    def __init__(self, row):
        self.parent = row[0]
        self.text = x520(row[1])


class URL(object):
    @staticmethod
    def queryAll(cursor):
        return (URL(x) for x in cursor.execute('''
            SELECT ZOWNER, ZLABEL, ZURL
            FROM ZABCDURLADDRESS
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;'''))

    def __init__(self, row):
        self.parent = row[0]
        self.label = x520(row[1])
        self.url = x520(row[2])

    def asStr(self, markPref):
        return buildLabel('URL', self.label, markPref, self.url)


class Service(object):
    @staticmethod
    def queryAll(cursor):
        return (Service(x) for x in cursor.execute('''
            SELECT ZOWNER, ZSERVICENAME, ZLABEL, ZADDRESS
            FROM ZABCDMESSAGINGADDRESS
            INNER JOIN ZABCDSERVICE ON ZSERVICE = ZABCDSERVICE.Z_PK
            ORDER BY ZOWNER, ZISPRIMARY DESC, ZORDERINGINDEX;'''))

    def __init__(self, row):
        self.parent = row[0]
        self.service = row[1]
        if self.service.endswith('Instant'):
            self.service = self.service[:-7]  # drop suffix
        self.label = x520(row[2])
        self.username = x520(row[3])

    def isSpecial(self):
        return self.service in ['Jabber', 'MSN', 'Yahoo', 'ICQ']

    def asSpecialStr(self, markPref):
        return buildLabel('X-' + self.service.upper(), self.label, markPref,
                          self.username)

    def asStr(self, markPref):
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
