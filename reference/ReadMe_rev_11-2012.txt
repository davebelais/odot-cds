CRASH DATA SYSTEM 
Extract and Decode Database documentation, 10/21/2004.  	     [Revised 11/26/2012]


This ReadMe.txt file describes the items delivered with the CDS Raw Data Extracts and/or CDS Decode Database, as follows:

I.	Modified and New Data Elements - "Old-New Field Xref.doc" File
II. 	Explanation of System-generated and Summary Fields
III.	Data Extract Code Descriptions (CDS_Data_Extract_Code_Desc.pdf) File
IV.	Raw Data Extract Files and Column Headers
V.	Decode Database
VI.	CAR Unit Contacts
VII.	Disclaimer


-----------------------------------------------------------------------------------------
I.  Modified and New Data Elements - "Old-New Field Xref.doc" File
-----------------------------------------------------------------------------------------

Beginning in 2002, the Statewide Crash Data file underwent conversion from a flat-file to a relational database. As part of the conversion, data elements used for multiple purposes were broken up into smaller components, and new data elements were created. If you are accustomed to the pre-2002 flat-file format, a document titled "Old-New Field Xref.doc" is available as an aid in identifying the original elements and their counterparts in the new system.  Please contact Theresa Heyn, Crash Data Analyst, at 503-986-4233 or Theresa.A.Heyn@odot.state.or.us, to obtain a copy. 

------------------------------------------------------------------------------------------
II.  Explanation of System-generated and Summary Fields
------------------------------------------------------------------------------------------
A.	Description of system-generated fields available in Raw Data Extracts and Decode Database

	The Raw Data Extract (CDS501) and Decode Database (CDS510) contain fields which were developed for the purpose of simplifying querying. Depending on the user's search criteria, use of these fields can eliminate the need for writing complex queries and linking tables. The “Data Extract Code Descriptions” manual, available on the Crash Analysis & Reporting Unit’s web page, provides information specific to each system-generated field.  Please visit this link: http://www.oregon.gov/ODOT/TD/TDATA/pages/car/car_publications.aspx

     1.  Crash Level
	-  Alcohol-Involved: Crashes where an active participant had been drinking. 
	-  Drug-Involved:    Crashes where an active participant had been using drugs. 
	 -  Speed-Involved:   Crashes where a driver was driving too fast for conditions or exceeding 
    the posted speed.  (Definition revised for Release 4, effective July 2008) 
	 -  Hit and Run
	 -  Population Range
	 -  Road Control  
	 -  Route Type/Route Number

     2.  Vehicle Level
	 - Vehicle Occupant Count

------------------------------------------------------------------------------------------ 
B. 	Description of Summary Fields available in Raw Data Extract (CDS501) and Decode Database (CDS510)
 	The following summary fields are available on the CRASH table. 

    TOT_VHCL_CNT:	total vehicles involved in this crash
    TOT_FATAL_CNT:	total fatalities that occurred in this crash
    TOT_INJ_LVL_A_CNT:	total major (severe, "incapacitating") injuries that occurred in this crash
    TOT_INJ_LVL_B_CNT: 	total moderate or "non-incapacitating" injuries that occurred in this crash
    TOT_INJ_LVL_C_CNT: 	total minor or "possible" injuries that occurred in this crash	
    TOT_INJ_CNT: 		total injuries that occurred in this crash

    TOT_UNINJD_AGE00_04_CNT: 	total participants in this crash age 4 and under, based on a participant's coded age value 01 to 04
    TOT_UNINJD_PER_CNT:		total participants (occupants and non-motorists) in this crash for whom no injury was reported
    TOT_PED_CNT: 		total participants in a crash who were pedestrians
    TOT_PED_FATAL_CNT: 		total pedestrian fatalities that occurred in this crash
    TOT_PED_INJ_CNT: 		total pedestrians injured in this crash
    TOT_PEDCYCL_CNT: 		total participants in a crash who were pedalcyclists
    TOT_PEDCYCL_FATAL_CNT: 	total pedalcyclist fatalities that occurred in this crash
    TOT_PEDCYCL_INJ_CNT:	total pedalcyclist injuries that occurred in this crash
    TOT_UNKNWN_CNT: 		total participants in a crash that were an unknown type of non-motorist
    TOT_UNKNWN_FATAL_CNT: 	total "unknown type" non-motorist fatalities that occurred in this crash
    TOT_UNKNWN_INJ_CNT: 	total "unknown type" non-motorist injuries that occurred in this crash
    TOT_OCC_CNT: 		total vehicle occupants involved in this crash 
    TOT_PER_INVLV_CNT:		total persons involved in this crash (sum of vehicle occupants and non-motorists)
    TOT_SFTY_EQUIP_USED_QTY: 	total participants (occupants and non-motorists) in this crash who were using safety equipment 
    TOT_SFTY_EQUIP_UNUSED_QTY:  total participants (occupants and non-motorists) in this crash with no or improper use of safety 				 		  equipment
    TOT_SFTY_EQUIP_UNKNWN_QTY: total participants (occupants and non-motorists) in this crash for whom safety equipment use is 				  unknown

-----------------------------------------------------------------------------------------------------
III.  Data Extract Code Descriptions (Data_Extract_Code_Desc.pdf) File
-----------------------------------------------------------------------------------------------------

A "Decode Manual" titled Data Extract Code Descriptions (Data_Extract_Code_Desc.pdf) was created to assist users with data retrieval.  The publication is intended as an aid in interpreting data and discerning important relationships between data fields. It is not an instructional manual. This file, and the full Code Manual are available online at http://www.oregon.gov/ODOT/TD/TDATA/car/CAR_Publications.shtml, under the heading "Crash Analysis and Reporting - Additional Publications".

---------------------------------------------------------------------------------------------------
IV.  Raw Data Extract Files and Column Headers
---------------------------------------------------------------------------------------------------
       A.   Overview of Raw Data Extract file (CDS501.txt)

The Raw Data Extract files contain all available data on the selected crashes. Each crash case contains three different types of records: Crash, Vehicle and Participant.  For each crash case included in the text file: 

     •   One record is written for the crash information.  This record is identified by a “1” in the “Record Type” column.  
     •   One record is written for each vehicle that is involved in the crash. These records are identified by a “2” in the “Record Type” column. 
     •   One record is written for each Participant that is involved in the Crash.  These records are identified by a “3” in the “Record Type” column.   The Vehicle Identifier on the Participant record is used to relate the Vehicle to each Participant who occupied it. 

For each case, the Crash record is followed by the first Vehicle record or Non-Motorist record for that crash.  Vehicle records are followed by all associated Participant records (vehicle occupants). Additional Vehicle records, Participant records, and Non-Motorist records follow, generally in accordance with the crash's sequence of events. 

The “Vehicle Id” value on the Participant records can be used to link each vehicle occupant to its associated vehicle.  Please note that Pedestrians, Pedalcyclists, and Unknown Non-Motorists are no longer tied to a “virtual” vehicle. As a result, the “Vehicle Id” value on those Participant records is blank or zero. 
   
All fields are in text-compatible format.  No fields are “packed” or “over punched”.  All fields include leading zeros when applicable. Numeric fields that can potentially contain a minus sign have either a zero or a minus in the first character. The decimal point character is included in the output field when it is applicable for the given data item. Examples: a milepoint value of 23.45 is shown as “0023.45”. A milepoint value of –46.00 is shown as “-046.00”. 

When a field is null in the master SQL database, it is null (represented only by a comma) in the CDS501 raw data extract. 
   
------------------------------------------------------------------------------------------ 
     B.   Recommendations for importing Raw Data Extract files.

"Comma-Delimited" CDS501.txt
This version of the Raw Data Extract separates data fields by commas.  The delimitation allows import applications to automatically place column breaks as intended by the original program, which results in a quicker and more automatic import process.  Refer to the CDS501_DataExtract_Layout_rev_11-2012.doc for information on the use of each field, and its data format.  

------------------------------------------------------------------------------------------ 
     C.   CDS_DataExtract_ColumnHeaders

No column headers are available in the Raw Data Extract CDS501.  We provide a separate, comma-delimited text or Excel file that contains the headers, which can be imported or pasted into your spreadsheet.  

------------------------------------------------------------------------------------------
V.  Decode Database
------------------------------------------------------------------------------------------
     A.   Description

The Decode Database is an MS Access database that is loaded with your requested subset of crash data.  There are three (3) master data tables:  CRASH, VHCL and PARTIC.  The remaining tables are look-up tables. The table structure and lookup tables are documented in Section IV of the “Data Extract Code Descriptions” manual on our web page:  http://www.oregon.gov/ODOT/TD/TDATA/pages/car/car_publications.aspx

Use of the CDS Decode Database requires experience working with MS Access or other database applications. 

------------------------------------------------------------------------------------------ 
     B.   Built-in Reports

     The Decode Database contains two types of built-in reports. 
	
     1.  Code Tables provide code descriptions for use in deciphering the codes used in the reports. They are:
	    
	 - ACTN	Action
	 - CAUSE	Cause
	 - ERR	Error (usually made by participant)
	 - EVNT	Event
	 - SFTY_EQUIP_USE	Safety Equipment Use

     2.  Data Reports provide summary total or detail information on the crash data contained in the database.

	 - rptIntersection:	summarizes all crashes by intersection and collision type
	 - rptPRC_Type:	lists crashes singly; displays detailed information on all facets of a given crash
	 - rptPRC_TypeWithCodes:	same as above, except provides interpretation tables for coded data
	 - rptSpecificIntersection:	same as (a) above, except user specifies the desired intersection by entering the first and second street numbers (codes)
	 - rptSummary:	summarizes all crashes by year and collision type, with totals by crash severity, injury, and other factors
	 - rptSum_w/totals:	same as above, except does not provide a break on crash year


------------------------------------------------------------------------------------------
VI.  Contacts
------------------------------------------------------------------------------------------

For additional information or assistance, please contact one of the following ODOT Crash 
Analysis and Reporting Unit staff members.

For assistance with understanding CDS coding protocols, please contact:
   Sylvia Vogel, Crash Data Team Leader, 503-986-4240, Sylvia.M.Vogel@odot.state.or.us

For assistance with the Raw Data Extract files or Decode Database, please contact either:
   Theresa Heyn, Crash Data Analyst, 503-986-4233, Theresa.A.Heyn@odot.state.or.us or
   Kelly Hawley, Crash Data Analyst, 503-986-4235, Kelly.R.Hawley@odot.state.or.us
   

------------------------------------------------------------------------------------------
VII.  Disclaimer
------------------------------------------------------------------------------------------

The Crash Analysis and Reporting Unit compiles data for reported motor vehicle traffic crashes occurring on city streets, county roads and state highways. The data supports various local, county and state traffic safety programs, engineering and planning projects, legislative concepts, and law enforcement services.

A higher number of crashes are reported for the 2011 data file compared to previous years.  This does not reflect an increase in annual crashes. The higher numbers result from a change to an internal departmental process that allows the Crash Analysis and Reporting Unit to add previously unavailable, non-fatal crash reports to the annual data file.  Please be aware of this change when comparing pre-2011 crash statistics.

Legally reportable motor vehicle traffic crashes are those involving death, bodily injury, or damage to personal property in excess of $500 (for crashes that occurred prior to 09/01/1997) or $1000 (for crashes that occurred between 09/01/1997 and 12/31/2003).  As of 01/01/2004, drivers are required to file an Accident and Insurance Report Form with DMV within 72 hours when damage to the driver's vehicle is over $1,500; damage to any vehicle is over $1,500 and any vehicle is towed from the scene as a result of damage from the accident; if injury or death resulted from the accident; or if damage to any one person’s property other than a vehicle involved in the accident is over $1,500.  For more information on filing requirements, please contact DMV. 

The Crash Analysis and Reporting Unit is committed to providing the highest quality crash data to customers.  However, because submittal of crash report forms is the responsibility of the individual driver, the Crash Analysis and Reporting Unit cannot guarantee that all qualifying crashes are represented; nor can assurances be made that all details pertaining to a single crash are accurate.  

Database expansion and refinement implemented in 2002 may result in slight differences between data reported from these extracts and data reported from versions released prior to October 2004.
