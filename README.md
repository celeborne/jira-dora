# sa-eis-dora
Script written by Luke Thompson
Licensed under the GNU General Public License version 3

This script calculates the average lead and cycle times for a given period in the desired Jira project.

The CLI interface provides quite a bit of flexibilty but is not 100% foolproof.

The user can select from the following options:
1. an ad-hoc report that outputs issues resolved in the last 30, 90, or 180 days and calculates the average lead time and cycle time for the selected time period.
2. a report that does the same for issues from the preceding month
3. a report where the user can select the suspense period they want a report for, ie 11 months prior to last month (a 10 month span)
4. no report, just calculate and display lead time and cycle time for last month

Cycle Time is defined as the average of cycles, where a cycle is:
- The delta of the timestamp of the most recent transition to "Done" for a given issue and the timestamp of the oldest transition to "In Progress" for a given issue = cycle time

Lead Time is the average of leads, where a lead is:
- The delta of the timestamp of the most recent transition to "Done" for a given issue and the timestamp of the issue creation = lead time

In order to use this script, one must do the following:
1. Pull down this script to your local development environment
2. Add your credentials to the script (lines 39-41)
3. Add the project you'd like to query to the script (lines 136, 139, 142, replace FOO)
4. Install any dependencies you might be missing (run the script and address any complaints your python env might have)

If you choose an option that provides reports for your queries, the report will be generated as a .csv in the directory where the script lives as 'lead_cycle_time_report.csv'