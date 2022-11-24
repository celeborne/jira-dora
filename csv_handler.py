import pandas as pd
# disables pandas chained assignment warning
# read "https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy" 
# for more info
pd.options.mode.chained_assignment = None # default='warn'

class CSV_Handler:
    def __init__ (self,
                generate_report = False):
            self.generate_report = generate_report


    def set_generate_report(self, x):
        self.generate_report = x

    def get_generate_report(self):
        return self.generate_report

    def pandas_to_csv(self, jira_issues: list, 
                      fields: list,
                      calculations: list,
                      generate_report: bool):
        if generate_report:
            # load the results into a DataFrame.
            issues = pd.json_normalize(jira_issues)

            # define which fields we're interested in for lead time with fields param
            # which works like a filter. This needs to be defined in the script that uses
            # the function (or it can be defined in this class)
            filtered_issues = issues[fields]

            # append lead time and cycle time calculations to the csv
            filtered_issues["Avg Lead Time"] = pd.Series(calculations[0])
            filtered_issues["Avg Cycle Time"] = pd.Series(calculations[1])
        
            
            filtered_issues.to_csv("lead_cycle_time_report.csv", index=False)
