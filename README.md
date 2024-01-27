# abcddb2vcard

This python script reads an AddressBook database file (`AddressBook-v22.abcddb`) and export its content to a vCard file (`.vcf`).

I created this script to automate my contacts backup procedure.
The output of this script should be exactly the same as dragging and dropping the “All Contacts” card.


### Usage

```sh
python3 abcddb2vcard.py backup/contacts_$(date +"%Y-%m-%d").vcf
```

> assuming db is located at "~/Library/Application Support/AddressBook/AddressBook-v22.abcddb"

#### Export into individual files

```sh
python3 abcddb2vcard.py outdir -s 'path/%{fullname}.vcf'
```

#### Extract contact images

```sh
python3 vcard2image.py AllContacts.vcf ./profile_pics/
```


### Supported data fields

`firstname`, `lastname`, `middlename`, `nameprefix`, `namesuffix`, `nickname`, `maidenname`, `phonetic_firstname`, `phonetic_middlename`, `phonetic_lastname`, `phonetic_organization`, `organization`, `department`, `jobtitle`, `birthday`, `[email]`, `[phone]`, `[address]`, `[socialprofile]`, `note`, `[url]`, `[xmpp-service]`, `image`, `iscompany`


### Limitations

The `image` field currently only supports JPG images.
I have honestly no idea where PNG images are stored.
For PNGs the database only stores a UUID instead of the file itself.
If you happen to know where I can find these, open an issue or pull request.


### Disclaimer

You should check the output for yourself before using it in a production environment.
I have tested the script with many arbitrary fields, however there may be some edge cases missing.
Feel free to create an issue for missing or wrong field values.

**Note:** The output of `diff` or `FileMerge.app` can be different to this output.
Apples does some weird transformations on vcf export that are not only unnecessary but in many cases break the re-import of the file.