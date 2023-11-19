from string import Template


shift_template_text = Template("""
Dear $squad,
                          
This is a reminder that your squad is scheduled to be in service and or assume the role of Tango over the next few days.  Please see the schedule below for details.  
If you have any questions or concerns, please notify The Collaborative in the group chat as soon as possible!.

Upcoming Shifts:
$shifts
                               
Upcoming Tango Assignments:
$tangos

The link to the calendar is: https://docs.google.com/spreadsheets/d/1bhmLdyBU9-rYmzBj-C6GwMXZCe9fvdb_hKd62S19Pvs/edit#gid=503761836


Thank you,
Central Somerset County EMS Collaborative
""")

shift_template_html = Template("""
<html>                                
  <head></head>
  <body>
    <p>Hi $squad,<br><br>
       This is a reminder that your squad is scheduled to be in service and or assume the role of Tango over the next few days.  
                               <br><br>
        Please see the schedule below for details.  
If you have any questions or concerns, please notify The Collaborative in the group chat as soon as possible!.<br>
                               
         $shifts<br>
                               <br>

        $tangos<br>
                                 <br>
The link to the calendar is: <a href="https://docs.google.com/spreadsheets/d/1bhmLdyBU9-rYmzBj-C6GwMXZCe9fvdb_hKd62S19Pvs/edit#gid=503761836">Station 95 Calendar</a><br>
                               <br>

Thank you,<br><br>
Central Somerset County EMS Collaborative

    </p>
  </body>
</html>
""")

