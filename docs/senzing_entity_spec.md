---
title: "Senzing Entity Specification"
linkTitle: "Entity Specification"
weight: 15
no_list: true
---

This document defines the Senzing Entity Specification — a detailed guide for mapping source data into Senzing’s entity resolution engine. 

The process of mapping is taking a source field name, like CustomerName, and transforming it into a target field name, by applying specific rules, such as renaming, reformatting, or combining fields based on predefined logic or conditions. It’s like creating a bridge where data from one system is reshaped to fit the structure of another system, guided by those rules.

# Key Terms

![Screenshot](images/ges-image1-key_terms.jpg)

Entities, Features and Attributes:

- **Entity** — Records of real-life persons, organizations, or things in your data sources.  These are your customers, your employees, your vendors, your subjects of interest.  
- **Features** — Details that describe an entity, such as a name, a phone number, or an address.
- **Attributes** — Specific components of features. For instance, a name feature might include first and last name. Addresses can have multiple lines, a city, and a state. Even driver’s licenses and passports have a number and an issuing authority.

# What Features to Map

Entity resolution works best when you have a name and one or more of the desired features outlined below.  The more features on each record, the better the entity resolution!

## Desired Features For Persons
- All names including nicknames and aliases.
- Date of birth and gender
- Passport, driver’s license, social security number, national insurance number
- Home and mailing addresses
- Home and cell phone numbers
- Email and social media handles
- Groups that they are associated with, such as their employer name
- Relationships such as:
  - Familial
  - Joint accounts, co-signers
  - Beneficial ownership
  - Principal role in a company

## Desired Features For Organizations
- All names
- Tax ID numbers
- Any ID numbers assigned by governments, agencies, or data providers
- Physical and mailing addresses
- All phone numbers
- Website and social media handles
- Relationships between them such as:
  - Direct and Ultimate parents 
  - Subsidiaries
  - Branches

## Payload Attributes

The use of payload attributes is optional.  In fact, it adds procssessing time and disk storage that strictly speaking isn't necessary for Entity Resolution.  

However, mapping a few key dates, statuses, and categories can help you quickly understand a match.  For instance:
  - If a duplicate customer was found, are they both active?  Which customer record came first? 
  - If you matched a subject record to a watchlist, what type of risk do they carry and where did that data come from?
  - If you matched a customer to a data provider, what did you learn?  What industry are they in?  How long have they been in business?

Think of Senzing as a pointer system to where you can find a person or company in your source systems or data warehouse.  All of the data about them exists there and can be looked up when needed. You wouldn't load it all into Senzing.  In fact, on very large systems, the use of payload attributes is discouraged.

# Examples of Senzing JSON

In prior versions we recommended a flat JSON structure with a separate sublist for each feature that had multiple values.  While we still support that, we now recommend the following JSON structure that has just one list for all features.  It is much cleaner and if you standardize on it, you can write one parser to pull values back out of it if needed by downstream processes.

## Recommended JSON Structure

```JSON
{
    "DATA_SOURCE": "CUSTOMERS",
    "RECORD_ID": "1001",
    "FEATURES":
    [
        {
            "RECORD_TYPE": "PERSON"
        },
        {
            "NAME_LAST": "Smith",
            "NAME_FIRST": "Robert",
        },
        {
            "DATE_OF_BIRTH": "12/11/1978"
        },
        {
            "ADDR_TYPE": "HOME",
            "ADDR_LINE1": "123 Main Street",
            "ADDR_CITY": "Las Vegas",
            "ADDR_STATE": "NV",
            "ADDR_POSTAL_CODE": "89132"
        },
        {
            "ADDR_TYPE": "MAILING",
            "ADDR_LINE1": "1515 Adela Lane",
            "ADDR_CITY": "Las Vegas",
            "ADDR_STATE": "NV",
            "ADDR_POSTAL_CODE": "89111"
        },
        {
            "PHONE_TYPE": "MOBILE",
            "PHONE_NUMBER": "702-919-1300"
        },
        {
            "DRIVERS_LICENSE_NUMBER": "112233",
            "DRIVERS_LICENSE_STATE": "NV"
        },
        {
            "EMAIL_ADDRESS": "bsmith@work.com"
        }, 
        {
            "REL_ANCHOR_DOMAIN": "CUSTOMERS",
            "REL_ANCHOR_KEY": "1001"
        },
        {
            "REL_POINTER_DOMAIN": "CUSTOMERS",
            "REL_POINTER_KEY": "1005",
            "REL_POINTER_ROLE": "SON_OF"
        }
    ],
    "CUSTOMER_SINCE": "06/15/2020",
    "STATUS": "Active"
}
```

### **Mapping Rules (for Recommended JSON Structure)**
1. DATA_SOURCE and RECORD_ID must be at the root level and DATA_SOURCE is required.
2. There should only be one sublist named FEATURES that contains all mapped features.
3. All **Payload Attributes** should be placed at the root level.
4. Because a feature in Senzing *can* have multiple attributes, you cannot supply a JSON list even if there is only one.

#### Examples

##### ✅ Correct JSON
```json
{
    "DATA_SOURCE": "CUSTOMERS",
    "RECORD_ID": "1001",
    "FEATURES":
    [
        {
            "PHONE_TYPE": "WORK",
            "PHONE_NUMBER": "800-101-1111"
        },
        {
            "PHONE_TYPE": "MOBILE",
            "PHONE_NUMBER": "702-202-2222"
        }
    ],
    "CUSTOMER_SINCE": "06/15/2020",
    "STATUS": "Active"
}

##### ❌ Incorrect JSON
```json
{
    "FEATURES":
    [
        {
            "PHONE_NUMBER":  // ❌ Do not use a list structure for multiple attributes
            [
                "800-101-1111",
                "800-202-2222"
            ]
        }
    ],
    "PAYLOAD": { // ❌ Do not nest payload attributes inside another object
        "CUSTOMER_SINCE": "06/15/2020",
        "STATUS": "Active"
    }
}
```

## Flat JSON Structure

We still support flat JSON which can be tempting when the source data is flat. Just remember, you have to use distinct attribute names for when you have more than one of a feature.

```JSON
{
    "DATA_SOURCE": "CUSTOMERS",
    "RECORD_ID": "1001",
    "RECORD_TYPE": "PERSON",
    "NAME_LAST": "Fletcher",
    "NAME_FIRST": "Irwin",
    "NAME_MIDDLE": "Maurice",
    "DATE_OF_BIRTH": "10/08/1943",
    "HOME_ADDR_LINE1": "123 Main Street",
    "HOME_ADDR_CITY": "Las Vegas",
    "HOME_ADDR_STATE": "NV",
    "HOME_ADDR_POSTAL_CODE": "89132",
    "MAILING_ADDR_LINE1": "3 Underhill Way",
    "MAILING_ADDR_LINE2": "#7",
    "MAILING_ADDR_CITY": "Las Vegas",
    "MAILING_ADDR_STATE": "NV",
    "MAILING_ADDR_POSTAL_CODE": "89101",
    "MOBILE_PHONE_NUMBER": "702-919-1300",
    "EMAIL_ADDRESS": "babar@work.com",
    "CUSTOMER_SINCE": "06/15/2020",
    "STATUS": "Active"
}
```

In this case the flat source record likely had a set of fields for a home address and another set for a mailing address.  The address type can be derived from source field's name and used as a prefix for each set of address attributes.  This is necessary because attributes at the same level must be unique.  The Senzing parser will assign this prefix to the features's usage type field.  In the above case HOME and MAILING will become ADDR_TYPEs.

### **Mapping Rules (for Flat JSON Structure)**
1. If you have to use a prefix, it must be a single token with no punctuation for the Senzing parser to recognize it.

# Source Schema Types

Data sources you will be asked to map to Senzing range from the very simple to the very complex. Here are some of the schema types we have run into so far and some instructions on how to map them.

## **Schema Type 1** 

A single flat table that seemingly contains one line per entity.  There is usually a unique key, and columns that contain names, addresses, phone numbers, etc.  

## **Schema Type 2** 

A single flat table with multiple rows per entity.  Usually there are only one set of name fields, address fields, etc.  But if an entity has more than one address, it will have multiple rows. Sometimes there is a secondary key that can be used to find all the rows for an entity.  Sometimes you have to derive one from multiple fields. Certain watch lists are like this because they are designed for ease of searching rather than for entity resolution.

## **Schema Type 3**

A single seemingly flat table, but the columns might contain lists:  Many XML, JSON or Parquet files are like this. There will only be one row per entity, but the name field(s) may have a list of names, the address field(s) a list of addresses, etc.

## **Schema Type 4** 

Multiple tables or files per entity.  This is often the case when pulling entities out of a normalized database, but can also occur when you receive a dump of a database in a single JSON or XML source file.

- You will find there is usually a master table or schema and one or more child tables or schemas, such as a list of addresses, phone numbers, identifiers, relationships, etc.   

- Sometimes there are even code files that contain a code and a description for things like name types, address types, country ids, etc.  Often these codes are small integers to minimize storage requirements. In this case you will want to look up the id to get the more descriptive value.   For instance, if the country code on the source address record is a number rather than a code.  Look for a codes table that contains the actual country code or name.

- Since Senzing requires one message per entity, you have to join all the master and child tables together. A good approach here is to map each file and join them together for the final step. Spark is a good candidate for this source type.

## **Schema Type 5** 

Transaction table with embedded entities.  Wire transfers are a good example of this as they reference external accounts with an account number, name and address that aren't well controlled.  Furthermore, there may be thousands with the exact same values.  A good approach here is to extract the identifying fields and dedupe them before sending to Senzing.  You can create a unique key by hashing the identifying fields to use as a RECORD_ID in Senzing and also stamp it on the transaction record itself so that you can join the transaction to its resolved entity in Senzing for analysis.

# General mapping guidance

## Feature Usage Types

There are certain features that source records may have more than one of.  Most notably, these are:

- The NAME feature has a NAME_TYPE attribute for noting if its the primary name, an AKA for a person, a DBA for a company and so on.  Some data providers even provide original script name, low quality aka names, etc. 

- The ADDRESS feature has an ADDR_TYPE attribute for noting if its the  business address, the home, mailing, or any other type of address.  

- The PHONE feature has a PHONE_TYPE attribute for noting if its the home phone, mobile or cell, fax, or any other type of phone.

- Some data sources have fieldnames like NICKNAME, MAILING_ADDR, and HOME_PHONE.  You can derive the type from the source fieldname.  

- Some data sources have a sublist of names, addresses, and/or phone numbers each with their own type field.  Trying to standarize those types across data sources is difficult at best.  You can map these as is if you like, but it is a good idea to truncate them to 50 characters as they can be a comma delimited list and be quite long.  

Senzing always matches features across these types for the following reasons:
- Some sources don't even specify the type.
- The home address for one entity might be the mailing address for another.
- Different sources either have no or different codification standards. 

Most of these types have no meaning for Senzing.  It will be your choice if you choose to map them or not.  Much like payload attributes above, they can be helpful to understand a match, but they do add to processing time.

That being said there are three usage types that do have meaning in Senzing.  They are:

- The NAME_TYPE: "PRIMARY" is used in the calculation to determine the best name to display for the resolved entity. Otherwise, the most common name across all the source records that make up the resolved entity will be selected.  

- The ADDR_TYPE: "BUSINESS" should be assigned to the physical location of an organization.  This adds weight to the address and helps break matches between chains where everything is the same except the address. People often move, companies rarely change physical locations.  

- The PHONE_TYPE: "MOBILE" can be assigned to add weight to the mobile or cell phone.  All the members of a household may report the same home phone.  But people don;t normally share their cell phone number.

### **Mapping Rules (for Feature Usage Types)**

1. For NAME_TYPE, only use PRIMARY for the main name when there is more than one name on the source record.

2. For ADDR_TYPE on ORGANIZATION records, assign BUSINESS on at least one of their addresses, even if a type is not specified.

3. For PHONE_TYPE, use MOBILE for any of its obvious variations: Cell, Mobile, etc.

4. Aside from the 3 rules above, never assign a usage type (e.g., ADDR_TYPE, PHONE_TYPE, NAME_TYPE) unless the source clearly specifies one.


## Mapping Identifiers

Some data sources have fields named SSN, DL_NUM, PASSPRT, etc.  This is a simple field name mapping to the appropriate Senzing feature.  Other data sources, especially data providers, have a sublist of identifiers with an identifier type that can be used to determine the appropriate Senzing feature.

### **Mapping Guidance (for Mapping Identifiers)**

#### Mapping from Source Field Names

When mapping from a source field name, always look for and map the corresponding field that indicates who issued the identifier.  For example:
- country for a passport 
- state or country for a drivers license
- country for a national_id or a tax_id

#### Mapping from a Sublist of Identifiers

When there is a sublist of identifiers, there may be 3 fields:
- an id_type field such as: PASSPORT, DRIVERS_LICENSE, SSN, EIN, TIN, VAT, CEDULA, SIREN, CUI, NIT. 
- the id_number field
- an id_country: can be a country, state or province.  When this is missing, it may be part of the id_type (e.g., AUS-PASSPORT, RU-INN).

There are many different identifier types and different sources don't follow the same codification standandards. For instance "EIN" and "FEIN" may both used as the type for the US Employer Identification Number used for Tax purposes.  Mapping to one of the Senzing features is the way to standardize them so they can be matched.

Sometimes the only way to know what type of identifier it is to look it up on the internet.  You are trying to determine:
1. If it is truly an identifier.  Sometimes data sources use this as a dumping ground for other kinds of information such as industry classification codes like "NAICS" or even "registration date".  You might even find "phone number" as a type which of course should be mapped to the PHONE feature.
2. Who issues it: Usually a country, state or province, or organization such D&B's DUNS number or GLEIF's LEI number.

### **Mapping Rules (for Mapping Identifiers)**

There are 3 non-specific identifier features: They are: NATIONAL_ID, TAX_ID and OTHER_ID.  All other features in the identifier sections (e.g., PASSPORT, SSN, LEI_NUMBER) should be considered specific features.

1. Map to the the specific feature attributes when the source field or id_type indicates it is one of those.

2. Map to the NATIONAL_ID feature attributes when the identifier type indicates it is issued by a country and the entity is usually only ever issued one.  (e.g., National Corporate ID in Japan, Companies House Registration Number in the UK, SIREN Business Registration ID in France).  This is the strongest identifier and will break matches between companies that might otherwise resolve.

3. Map to the TAX_ID feature attributes when the identifier type indicates it is issued by a country and used to collect taxes. (e.g., VAT Number in many countries, EIN or Federal Tax ID in the US),  It is the second strongest identifier and will break matches unless another strong feature confirms it.

4. Optionally, you can map to both NATIONAL_ID and TAX_ID feature attributes if it qualifies as both. You may want to do this if all of your data sources don't follow this specification and you continually find the same value mapped two different ways.

5. Known identifiers not issued by a country, that are used a lot, are candidates for having a new feature created for them.  (e.g., MEDICARE_ID in data source about patients)

6. Only map to OTHER_ID feature attributes when it is a known identifier not issued by a country that you don't want to create a feature for.  Always map the source id_type to the OTHER_ID_TYPE attribute to prevent overmatching as the country of the issuer is not always known or its international/

7. Do not map the source id_type to NATIONAL_ID_TYPE or TAX_ID_TYPE when country is known to prevent undermatching due to different codification standards.

8. Map all identifiers that aren't mapped by any of these rules as Payload Attributes so that you have visibility to them as you look them up in Senzing.  Through time, you may discover what they are and decide to map them 

## Mapping Relationships

There are two scenarios you may find on source records that seemingly only contain one entity.

1. Look for fields that reference other entities by their ID.  
    - Organization records may have fields like: parent_id, a child_id, etc.  These relationships should become REL_POINTERS and the REL_POINTER_ROLE can be derived from the source field name.
    - Person records may have fields like: company_id or employer_id and job title.  
    - These should all be mapped as a REL_POINTERs if the other ID of the related record is also going to be mapped to Senzing.  Otherwise these should be mapped as payload.

2. Sometimes the source record contains multiple values about the referenced entity, but no key.  
    - For example, a contact list has the contact and the company they work for.  If there are enough features about the company, see [What Features to Map](#what-features-to-map), it should be mapped as its own entity and related back to the contact. 
    - This can also happen on transactions such as a wire transfers where the sender and receiver contain features but no reliable unique ID.
    - When you do create an entity like this, there will be no unique ID to map to, so use a hash of its features as RECORD_ID. 
    - This will likely create many duplicate records.  If this is a large data source, the duplicates should be removed from the resulting output.

3. For multi-schema data sources, look for a relationship schema that has fields like id1, id2 and a relationship type or role. Relationships **MUST** be considered a child schema for source entity based on whatever the id1 field is.

### **Mapping Rules (for Relationships)**

1. **Always** analyze the schema for possible relationship fields or schemas and explicitly suggest how to map them as Senzing relationships, even if they are not obvious."

2. **Always** map the relationship as if it will be unidirectional.  You will need to decide which entity record to point to the other.   Usually, but not always, the primary entity the source record is about points to the other entity or entities.

3. The entity you point to must have a REL_ANCHOR feature.  A good rule of thumb is to **always** map a REL_ANCHOR feature to any entity record that *could be* pointed to.  

4. Any given record should only ever have one REL_ANCHOR feature, but can have multiple REL_POINTER features.

## Updating vs Replacing Records

Senzing always replaces records rather than keep any prior values as history. This is because it is impossible for Senzing to know:
1. Was the prior address corrected or did they move?
2. If there is no phone number on the new record, but there was on the prior, did they tell you to remove it?
3. Are you contractually allowed to keep the prior values?  The answer is no for many data providers and watchlists.

### **Mapping Rules (for Updating vs Replacing Records)**

1. All the features of an entity must be presented in a single JSON document including any historical values you wish to keep.  
2. Many source systems already keep such history, so be sure to map those to Senzing as well.  
3. If there is not a history table in the source, you can keep a simple table of your own with at least these fields: DATA_SOURCE, RECORD_ID,  FEATURE type, and the feature JSON that you want to keep as history.  Later when you are creating JSON from the new record, you can see if there are prior features for that record that you want to include.

# Dictionary of Pre-configured Attributes

## Attributes for the Record Key

These attributes are required to tie records in Senzing back to the source.  They must be placed at the root level in the JSON document.

| Attribute | Type | Required | Example | Notes |
| --- | --- | --- | --- |  --- |
| DATA_SOURCE | String | Required | CUSTOMERS | This is the code for the data source.|
| RECORD_ID | String | Strongly Desired | 1001 | This value must be unique within the DATA_SOURCE and is used to determine if Senzing needs to add or replace the record.|

### **Mapping Rules for (Attributes for the record key)**

1. DATA_SOURCE is required and should be a simple code describing the type of entities in it. For instance a set of customer records could simply be assigned the code CUSTOMERS. If you have two customer sources, you must be more specific.  For instance, BANKING_CUSTOMERS and MORTGAGE_CUSTOMERS.

2. Always look for a unique or primary key for the source record to map to RECORD_ID.  While you can, you do not also have to map this value to a feature.  Records in Senzing can always be retreived by DATA_SOURCE and RECORD_ID with a "get" call in the Senzing SDK.

3. If there is not a primary key for the source record, you *should* create one by computing a hash of the source values you mapped to Senzing JSON using: SHA1, MD5, etc. Ideally, you stamp this hash on your source record as well.

### **Mapping Guidance for (RECORD_ID)**

- If you do not supply a RECORD_ID, one will be generated based on a hash of the features.  This effectively renders updates impossible since any change to one of its features would generate a new hash.

### FEATURE: RECORD_TYPE

| Attribute | Type | Required | Example | Notes |
| --- | --- | --- |  --- | --- |
| RECORD_TYPE | String | Strongly Desired | PERSON, ORGANIZATION | Prevents records of different types from resolving.  Leave blank if not known so it can match any type.|

#### **Standardized RECORD_TYPES**
Senzing has developed mappers from a number of different data providers and have standardized on the following RECORD_TYPEs:
- PERSON
- ORGANIZATION
- ADDRESS
- VESSEL
- AIRCRAFT

#### **Mapping Guidance (for RECORD_TYPE)**

- RECORD_TYPE prevents records of different types from resolving together while still allowing them to be related.  You likely wouldn't want Joe Smith and Joe Smith, LLC to resolve even if they are at the same address. 

- RECORD_TYPE is also useful in designating the node shape if you visually render entities and their relationships in a graph!

- You can add additional RECORD_TYPEs when appropriate based on this mapping guidance.  You do not need to register them in the Senzing configuration.

#### **Mapping Rules (for RECORD_TYPE)**

1. If the whole file is obviously about PERSONs or ORGANIZATIONs, etc, then give every record that RECORD_TYPE.

2. Otherwise, look for a source field that tells you what kind of entity the record is for and attempt to standardize it to one of the **Standardized RECORD_TYPES** listed above.

3. If there is no source field you can use to determine record type and the list of source fields is ambiguous in that it could be either a PERSON or an ORGANIZATION, you could look at what field values are populated and decide based on that.  If still not clear, you should leave the RECORD_TYPE field blank.

## Names of Persons or Organizations

There are three ways to map names:

### Feature: NAME (parsed fields)

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| NAME_TYPE | String | PRIMARY, AKA | Optional designation when there are multiple.  See [Feature Usage Types](#feature-usage-types)|
| NAME_LAST | String | Smith | This is the last or surname of an individual. |
| NAME_FIRST | String | Robert | This is the first or given name of an individual. |
| NAME_MIDDLE | String | J | This is the middle name of an individual. |
| NAME_PREFIX | String | Mr | This is a prefix for an individual's name such as the titles: Mr, Mrs, Ms, Dr, etc. |
| NAME_SUFFIX | String | MD | This is a suffix for an individual's name and may include generational references such as: JR, SR, I, II, III and/or professional designations such as: MD, PHD, PMP, etc. |

#### Examples

##### ✅ Correct JSON
```json
{
  "FEATURES": [
    {"NAME_LAST": "Smith", "NAME_FIRST": "Robert", "NAME_MIDDLE": "A"}
  ]
}
```

##### ❌ Incorrect JSON
```json
{
  "FEATURES": [
    {"NAME_LAST": "Smith"}, 
    {"NAME_FIRST": "Robert"}, 
    {"NAME_MIDDLE": "A"}
  ]
}
```


### Feature: NAME (organization)

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| NAME_TYPE | String | PRIMARY, DBA | Optional designation when there are multiple. See [Feature Usage Types](#feature-usage-types)|
| NAME_ORG | String | Acme Tire Inc. | This is the organization name. |

### Feature: NAME (could be either)

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| NAME_TYPE | String | PRIMARY, OTHER | Optional designation when there are multiple. See [Feature Usage Types](#feature-usage-types)|
| NAME_FULL | String | Robert J Smith, Trust | This is either a person or organization name.| 

### **Mapping Rules (for Feature: NAME)**

1. If parsed name fields like first name and last name are available and populated, map to the **NAME (parsed fields)** example above.

2. If there is just a single source field containing the name, and you know its an ORGANIZATION, map to the **NAME (organization)** example above.

2. If there is just a single source field containing the name, and you know don't know if its a PERSON or an ORGANIZATION, map to the **NAME (could be either)** example above.

3. Sometimes a source system keeps both the parsed version of a person's name as well as the concatenated version on the same record.  The parsed version is preferred because you can get both given and surname scores as well.

4. Sometimes there is both a person name and an organization name on a record, such as a contact list where you have the person and who they work for. In this case you would map the person's name as shown above. But the name of the organization they work for should be mapped as **EMPLOYER_NAME**.  See the section on [Group Associations](#group-associations).

5. Sometimes there are name fields that don't actually belong to the entity the record is for.  Whenever there are multiple names, you have to decide which ones actually belongs to that entity and which ones belong to people they are related to.  You can decide base on the source field name or the source name type value if the names are in a sublist. Terms like alias, aka, and DBA belong to that entity.  Terms like: parent_name, child_name, employer name, etc belong to people they are related to and should be mapped as payload.

## Addresses

There are two ways to map addresses:

### Feature: ADDRESS (parsed)

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| ADDR_TYPE | String | HOME | Optional designation. See [Feature Usage Types](#feature-usage-types)|
| ADDR_LINE1 | String | 111 First St | This is the first line of the address.|
| ADDR_LINE2 | String | Suite 101 | This is the second address line if needed. |
| ADDR_LINE3 | String |  | This is a third address line if needed. |
| ADDR_LINE4 | String |  | This is a fourth address line if needed. |
| ADDR_LINE5 | String |  | This is a fifth address line if needed. |
| ADDR_LINE6 | String |  | This is a sixth address line if needed. |
| ADDR_CITY | String | Las Vegas | This is the city of the address. |
| ADDR_STATE | String | NV | This is the state or province of the address. |
| ADDR_POSTAL_CODE | String | 89111 | This is the zip or postal code of the address. |
| ADDR_COUNTRY | String | US | This is the country of the address. |

### Feature: ADDRESS (single field)

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| ADDR_TYPE | String | HOME | Optional designation.  See [Feature Usage Types](#feature-usage-types)|
| ADDR_FULL | String |  | This is a single string containing all address lines plus city, state, zip and country.|

### **Mapping Rules (for Feature: ADDRESS)**

1. Sometimes the parsed version of the address include fields like street number, street name, pre-directional, post-directional, but no address line fields.  In this case you need to re-construct the address lines from the parsed fields.

2. If both the parsed and the concatenated versions of the address exist on the same source record, you should map the concatenated version as some sources may have only extracted what they could into the parsed fields, potentially losing some meaning.

## Phone numbers

### Feature: PHONE

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| PHONE_TYPE | String | MOBILE | Optional designation.  See [Feature Usage Types](#feature-usage-types)|
| PHONE_NUMBER | String | 111-11-1111 | This is the actual phone number. |

## Physical and other attributes

### Feature: GENDER

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| GENDER | String | M | This is the gender such as M for Male and F for Female. |

### Feature: DOB

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| DATE_OF_BIRTH | String | 1980-05-14 | This is the date of birth for a person. Partial dates such as just month and day or just month and year are acceptable.|

### Feature: DOD

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| DATE_OF_DEATH | String | 2010-05-14 | This is the date of death for a person. Partial dates are acceptable. |

### Feature: NATIONALITY

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| NATIONALITY | String | US | This is where the person was born and usually contains a country name or code |

### Feature: CITIZENSHIP

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| CITIZENSHIP | String | US | This is the country the person is a citizen of and usually contains a country name or code. |

### Feature: POB

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| PLACE_OF_BIRTH | String | US | This is where the person was born. Ideally it is a country name or code. However, it often contain city names as well. |

### Feature: REGISTRATION_DATE

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| REGISTRATION_DATE | String | 2010-05-14 | This is the date the organization was registered, like date of birth is to a person. |

### Feature: REGISTRATION_COUNTRY

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| REGISTRATION_COUNTRY | String | US | This is the country the organization was registered in, like place of birth is to a person. |

## Identifiers

### Feature: PASSPORT

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- |
PASSPORT_NUMBER | String | 123456789 | This is the passport number. |
PASSPORT_COUNTRY | String | US | This is the country that issued it. |

### Feature: DRLIC 

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- |
| DRIVERS_LICENSE_NUMBER | String | 123456789 | This is the driver’s license number. |
| DRIVERS_LICENSE_STATE | String | NV | This is the state, province, or country that issued it. |

### Feature: SSN 

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- |
| SSN_NUMBER | String | 123-12-1234 | This is the US Social Security number.  Partial SSNs are acceptable.|

### Feature: NATIONAL_ID 

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- |

| NATIONAL_ID_TYPE | String | CEDULA | Optional: use with caution! see the section on mapping identifiers above.|
| NATIONAL_ID_NUMBER | String | 123121234 | This is the national ID number issued by many countries. It is similar to an SSN in the US. |
| NATIONAL_ID_COUNTRY | String | CA | This is the country that issued it.|

### Feature: TAX_ID 

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- |
| TAX_ID_TYPE | String | EIN | Optional: use with caution! see the section on mapping identifiers above.|
| TAX_ID_NUMBER | String | 123121234 | This is the actual ID number. |
| TAX_ID_COUNTRY | String | US | This is the country that issued the it.|


### Feature: OTHER_ID 

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- |
| OTHER_ID_TYPE | String | ISIN | Highly Desired: see the section on mapping identifiers above.|
| OTHER_ID_NUMBER | String | 123121234 | This is the actual ID number. |
| OTHER_ID_COUNTRY | String | MX | This is the country that issued it.|

#### **Mapping Guidance (for Feature: OTHER_ID)**

* Use OTHER_ID sparingly! It is a catch-all for identifiers you don't know much about. It is always better to add a new feature rather than just putting a lot of different identifiers in this one feature. One reason is you might get cross type false positives!

### Feature: TRUSTED_ID 

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- |
| TRUSTED_ID_TYPE | String | FORCE_MERGE | The type of ID that is to be trusted. See the note below |
| TRUSTED_ID_NUMBER | String | 123-45-1234 | The trusted unique ID. |

#### **Mapping Guidance (for Feature: TRUSTED_ID)**

* Trusted IDs are primarily used to manually force records together or apart as described here … [https://senzing.zendesk.com/hc/en-us/articles/360023523354-How-to-force-records-togetheror-apart](https://senzing.zendesk.com/hc/en-us/articles/360023523354-How-to-force-records-together-or-apart)

### Feature: ACCOUNT

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| ACCOUNT_NUMBER | String | 1234-1234-1234-1234 | This is an account number such as a bank account, credit card number, etc. |
| ACCOUNT_DOMAIN | String | VISA | This is the domain the account number is valid in. |


### Feature: DUNS_NUMBER

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| DUNS_NUMBER | String | 123123 | The unique identifier for a company.  https://www.dnb.com/duns-number.html |


### Feature: NPI_NUMBER

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| NPI_NUMBER | String | 123123 | A unique ID for covered health care providers. https://www.cms.gov/Regulations-and-Guidance/Administrative-Simplification/NationalProvIdentStand/ |


### Feature: LEI_NUMBER

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| LEI_NUMBER | String | 123123 | A unique ID for entities involved in financial transactions. https://en.wikipedia.org/wiki/Legal_Entity_Identifier |

## Websites, email addresses, and other social handles

The following social media attributes are available.

### Feature: WEBSITE

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| WEBSITE_ADDRESS | String | somecompany.com | This is a website address, usually only present for organization entities. |

### Feature: EMAIL

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| EMAIL_ADDRESS | String | someone@somewhere.com | This is the actual email address. |

### Features for Social Media Handles

Social media attributes have the same name as their feature.

| Feature/Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| LINKEDIN | String | xxxxx | This is the unique identifier in this domain. |
| FACEBOOK | String | xxxxx | This is the unique identifier in this domain. |
| TWITTER | String | xxxxx | This is the unique identifier in this domain. |
| SKYPE | String | xxxxx | This is the unique identifier in this domain. |
| ZOOMROOM | String | xxxxx | This is the unique identifier in this domain. |
| INSTAGRAM | String | xxxxx | This is the unique identifier in this domain. |
| WHATSAPP | String | xxxxx | This is the unique identifier in this domain. |
| SIGNAL | String | xxxxx | This is the unique identifier in this domain. |
| TELEGRAM | String | xxxxx | This is the unique identifier in this domain. |
| TANGO | String | xxxxx | This is the unique identifier in this domain. |
| VIBER | String | xxxxx | This is the unique identifier in this domain. |
| WECHAT | String | xxxxx | This is the unique identifier in this domain. |

## Group Associations

Groups a person belongs to can also be useful for resolving entities. Consider two contact lists that only have name and who they work for as useful attributes.

### Feature: EMPLOYER

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| EMPLOYER | String | ABC Company | This is the name of the organization the person is employed by. |

### Feature: GROUP_ASSOCIATION

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| GROUP_ASSOCIATION_TYPE | String | MEMBER | This is the type of group an entity belongs to. |
| GROUP_ASSOCIATION_ORG_NAME | String | Group name | This is the name of the organization an entity belongs to. |

### Feature: GROUP_ASSN_ID

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| GROUP_ASSN_ID_TYPE | String | DUNS | When the group a person is associated with has a registered identifier, place the type of identifier here. |
| GROUP_ASSN_ID_NUMBER | String | 12345 | When the group a person is associated with has a registered identifier, place the identifier here. |

#### **Mapping Guidance (for Group Associations)**

* Group associations should not be confused with disclosed relationships described later in this document. Group associations help resolve entities whereas disclosed relationships help relate them.

* If all you have in common between two data sources are name and who they work for, a group association can help resolve the Joe Smiths that work at ABC company together.

* Group associations are subject to generic thresholds to help reduce false positives and keep the system fast. Therefore they will not help resolve _all_ the employees of a large company across data sources. But they could help to resolve the smaller groups of executives,  contacts, or owners of large companies across data sources.

## Disclosed relationships

Some data sources keep track of known relationships between entities. Look for a table within the source system that defines such relationships and include them here.

A relationship can either be unidirectional where one record points to the other or bidirectional where they each point to the other.

![Screenshot](images/ges-image3-relationship.png)

This is accomplished by giving a REL_ANCHOR feature to any record that can be related to and a REL_POINTER feature to each record that relates to it.   A record should only ever have one REL_ANCHOR feature, but may have zero or more REL_POINTER features.  For instance, several people may be related to a company so the company only needs one REL_ANCHOR feature they all point to.  But a single person may be related to more than one company so that person can have several REL_POINTER features. 

### Feature: REL_ANCHOR

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| REL_ANCHOR_DOMAIN | String | CUSTOMERS | This code helps keep the REL_ANCHOR_KEY unique.  This is a code (without dashes) for the data source or source field that is contributing the relationship.  
| REL_ANCHOR_KEY | String | 1001 | This key should be a unique value for the record within the REL_ANCHOR_DOMAIN.  You can just use the current record's RECORD_ID here.|

#### **Mapping Guidance (for Feature: REL_ANCHOR)**

- Some sources do not have disclosed relationships so no need to add a REL_ANCHOR to any records, but when they do it is hard to know if a record will be in a relationship and need one.  In this case, you can give one to every company record so that other companies can point to it as a parent or subsidiary as well as people who work for it or own it.   When people may point to each other, every person should get one as well.

- The REL_ANCHOR_DOMAIN should not contain any dashes as it appears in the MATCH_KEY for the relationship it creates.  The MATCH_KEY uses pluses and minuses to show features that added to the match and features that detracted and the dash looks like a minus which makes it more difficult to parse.


### Feature: REL_POINTER

| Attribute | Type | Example | Notes |
| --- | --- | --- | --- | 
| REL_POINTER_DOMAIN | String | CUSTOMERS | See REL_ANCHOR_DOMAIN above. |
| REL_POINTER_KEY | String | 1001 | See REL_ANCHOR_KEY above.
| REL_POINTER_ROLE | String | SPOUSE | This is the role the pointer record has to the anchor record.  Such as OFFICER_OF, SON_OF, SUBSIDIARY_OF, etc.  It is best to standardize these role codes for display and filtering. |

# Additional configuration

Senzing comes pre-configured with all the features, attributes, and settings you will likely need to begin resolving persons and organizations immediately. The only configuration that really needs to be added is what you named your data sources.

Email support@senzing.com for assistance with custom attributes.

## How to add a data source

On your Senzing project's bin directory is an application called sz_configtool.

Adding a new data source is as simple as registering the code you want to use for it. Most of the reporting you will want to do is based on matches within or across data sources.

* If you want to know when a customer record matches a watchlist record, you should have a data source named `CUSTOMERS` and another named `WATCHLIST`.
* If you are matching two customer data sources to find the overlap, you could have one data source named `SOURCE1-CUSTOMERS` and another named `SOURCE2-CUSTOMERS` substituting SOURCE1 and SOURCE2 with something more meaningful. 

For example, to add a new data source named `CUSTOMERS` using `G2ConfigTool.py`:

```console
./G2ConfigTool.py

Welcome to the Senzing configuration tool! Type help or ? to list commands

(g2cfg) addDataSource CUSTOMERS

Data source successfully added!

(g2cfg) save

Are you certain you wish to proceed and save changes? (y/n) y

Configuration changes saved!
```