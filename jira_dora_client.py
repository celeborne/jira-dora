# written by Luke Thompson
# Licensed under the GNU General Public License version 3

# TODO You must provide your Jira credentials on lines 39-41

# This script calculates the average lead and cycle times for a given period. 
# The CLI interface provides quite a bit of flexibilty but is not 100% foolproof.

# The average of cycles, where a cycle is:
#   The timestamp of the most recent transition to "Done" for a given issue
#   - The timestamp of the oldest transition to "In Progress" for a given issue
#   = cycle time
# The average of leads, where a lead is:
#   The timestamp of the most recent transition to "Done" for a given issue
#   - The timestamp of the issue creation
#   = lead time

# TODO depending on your environment, you may need to install some dependencies
# 'pip install atlassian-python-api, pandas'

from atlassian import Jira
from dateutil import parser
import datetime
import pytz
import date_handler 
import csv_handler

# localization for timestamps in Jira issues
timezone = pytz.timezone("America/New_York")

# Instance of date handler to handle time ops
dh = date_handler.Date_Handler()

# Instance of csv handler to handle read/write ops
csvh = csv_handler.CSV_Handler()

# credentials for Jira
JIRA_INSTANCE = Jira(
        url = "add-your-team-or-company-managed-jira-project-url", # TODO add the url for your company or team managed project here
        username = "your-jira-username", # TODO your Jira access credentials are required here
        password = "your-password-or-api-key", # TODO your Jira access credentials are required here
        cloud = True
    )


# fields needed for this report - these are embedded in the json returned from Jira
# there are many, but these are the ones we're concerned with
FIELDS = ["key", "summary", "resolution", "issuetype", "created", "resolutiondate", "status", "changelog"]

# these are the headers the csv writer uses to organize the output file
FIELDS_OF_INTEREST = ["key", "fields.summary", "fields.issuetype.name", 
                        "fields.created", "fields.resolutiondate", 
                        "fields.status.statusCategory.name"]


def get_lookback():
    # get input from user to determine lookback for report and type of report
    # this determines the type of query generated and sent to Jira
    report_type = ""
    day_or_month_report = input(
        """\n\n Which type of report do you want to generate?
        1. ad-hoc -> lead time for number of days preceding today (30, 90, 180)
        2. monthly -> lead time for last month
        3. suspense -> specify a range of time you"d like to generate a report on
        4. just calculate lead and cycle time for last month, no report necessary
        > """)
    if day_or_month_report == "1":
        report_type = "adhoc"
        csvh.set_generate_report(True)

        lookback = input("""
        Select suspense for report: 1. 30 day, 2. 90 day, 3. 180 day report:
        > """)
    
        if lookback.strip() == "1":
            dh.set_suspense_period_start(30)

        elif lookback.strip() == "2":
            dh.set_suspense_period_start(90)

        elif lookback.strip() == "3":
            dh.set_suspense_period_start(180)

        else:
            print("Please select one of the viable options.\n\n")
            get_lookback()

    elif day_or_month_report.strip() == "2":
        report_type = "monthly"
        csvh.set_generate_report(True)
    
    elif day_or_month_report.strip() == "3":
        report_type = "suspense"
        csvh.set_generate_report(True)

        print("""
        Specify the number of whole months you'd like the report to start (up to 12) and end, ie start 
        11 months ago and end last month (the delta between current month and the month you'd 
        like the report to start), ie 11 start (11 months ago), 1 end (1 month ago)
        """)

        month_start = int(input("""
        How many months prior would like the report to start?
        > """))
        dh.set_suspense_period_start(month_start)

        month_end = int(input("""
        How many months prior would like the report to end?
        > """))
        dh.set_suspense_period_end(month_end)

        if month_start > 12 or month_end < 0 or month_start < month_end:
            print("Please provide viable numbers at this prompt...")
            get_lookback()

    elif day_or_month_report.strip() == "4":
        report_type = "monthly"
        return report_type

    else:
        print("Please select one of the viable options.")
        get_lookback()

    return report_type

    
# JQL query to get issues with statuses marked "DONE" or "READY TO RELEASE"
# query can change depending on user needs
def set_query(type_of_report: str):
    # define the Jira query
    # param "type_of_report" is generated from user input
    # "dh" or date_handler provides suspense periods and is generated in get_lookback() fn
    # TODO For each of these queries, change FOO to the desired project you want to query
    if type_of_report == "adhoc":
        jql_request = f"project = FOO AND resolved >= startOfDay(-{dh.get_suspense_period_start()}) AND resolved <= endOfDay() AND status in (Done, \"Ready To Release\") AND issuetype in (Story, Bug) ORDER BY status ASC, issuetype ASC"
    
    elif type_of_report == "monthly":
        jql_request = f"project = FOO AND resolved >= startOfMonth(-1) AND resolved <= endOfMonth(-1) AND status in (Done, \"Ready To Release\") AND issuetype in (Story, Bug) ORDER BY status ASC, issuetype ASC"
    
    elif type_of_report == "suspense":
        jql_request = f"project = FOO AND resolved >= startOfMonth(-{dh.get_suspense_period_start()}) AND resolved <= endOfMonth(-{dh.get_suspense_period_end()}) AND status in (Done, \"Ready To Release\") AND issuetype in (Story, Bug) ORDER BY status ASC, issuetype ASC"

    return jql_request


# Jira limits response data to 100 issues, this function provides pagination workaround
def retrieve_all_query_results(Jira: Jira, query_string: str, fields: list) -> list:
    issues_per_query = 100
    list_of_jira_issues = []

    # gets the total number of issues in the results set. 
    num_issues_in_query_result_set = Jira.jql(query_string, limit = 0)["total"]
    print(f"""
    Query `{query_string}` returns {num_issues_in_query_result_set} issues""")
    
    # use floor division + 1 to calculate the number of requests needed to get all issues
    for query_number in range(0, (num_issues_in_query_result_set // issues_per_query) + 1):
        results = Jira.jql(query_string, limit = issues_per_query, 
                           start = query_number * issues_per_query, 
                           fields = fields, expand="changelog")

        # appends each subsequent query to the list, under "issues" key of response object
        list_of_jira_issues.extend(results["issues"])

    return list_of_jira_issues


def get_issue_element(histories: dict, issue_type: str, return_oldest: datetime) -> datetime:
    # this function collects and orders the timestamps when an issue is transitioned 
    # from one state to "Done" state and uses the most recent transition for the calculations
    if return_oldest:
        date_track = datetime.datetime.strptime("2999-12-31", "%Y-%m-%d")
    else:
        date_track = datetime.datetime.strptime("1970-01-01", "%Y-%m-%d")
    date_track = timezone.localize(date_track)

    # timestamps are nested in the JSON structure, here we drill down into their location
    # and check to see whether the status is commensurate with what we're looking for, ie
    # history item set to "In Progress", "Done", or "Ready to Release"
    for history in histories["changelog"]["histories"]:
        for item in history["items"]:
            to_string = item["toString"]
            if to_string == issue_type:
                this_tstamp = parser.parse(history["created"])
                if return_oldest:
                    if this_tstamp < date_track:
                        date_track = this_tstamp
                else:
                    if this_tstamp > date_track:
                        date_track = this_tstamp
    if date_track.year == 2999 or date_track.year == 1970:
        return None
    return date_track


def calculate_lead_cycle_time(jira_issues: list) -> str:
    leadtime_deltas: datetime.timedelta = datetime.timedelta(0)
    cycletime_deltas: datetime.timedelta = datetime.timedelta(0)
    changelog_dict = {}
    skipped: int = 0

    for issue in jira_issues:
        # get and parse the date the issue was created
        creation_date = parser.parse(issue["fields"]["created"])
        # assign these dates to dictionary key, ordering them by timestamps via the
        # get_issue_element fn
        changelog_dict["created"] = creation_date
        changelog_dict["in_progress"] = get_issue_element(issue, "In Progress", True)
        changelog_dict["completed"] = get_issue_element(issue, "Done", False)
        if changelog_dict.get("in_progress") is not None and changelog_dict.get("completed") is not None:
            leadtime_deltas += changelog_dict.get("completed") - changelog_dict.get("created")
            cycletime_deltas += changelog_dict.get("completed") - changelog_dict.get("in_progress")

        else:
            skipped += 1

    calculated_leadtime = round((leadtime_deltas.days / len(jira_issues)), 1)
    calculated_cycletime = round((cycletime_deltas.days / len(jira_issues)), 1)

    print(f"\nAverage lead time in days: {calculated_leadtime}")
    print(f"Average cycle time in days: {calculated_cycletime}")

    if skipped > 0:
        print(f"""
        Skipped issues: {skipped}
        
        Skipped issues are those that went from "Created" or "Backlog" to "Done" 
        without ever being "In Progress". This is an important distinction for 
        calculating Cycle Time properly.\n""")
    
    return [calculated_leadtime, calculated_cycletime]

# WORM (write once read many) variable for long functions and their args
generate_query = set_query(get_lookback())
param_set = retrieve_all_query_results(JIRA_INSTANCE, generate_query, FIELDS)

if csvh.get_generate_report() == True:
    # write report to csv once generated
    csvh.pandas_to_csv(param_set, FIELDS_OF_INTEREST, 
                       calculate_lead_cycle_time(param_set),
                       csvh.get_generate_report())


elif csvh.get_generate_report() == False:
    calculate_lead_cycle_time(param_set)
