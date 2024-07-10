######################
#
# NB MUST Copy this into the course directory and run from there
# Code to ingest downloaded student submissions of Jupyter notebooks nbgrader python ipynb homeworks
# and put these in the correct form for nbgrader to process
#
######################

import os
import re
import nbgrader, csv, codecs, sys, os, shutil
from nbgrader.apps import NbGraderAPI
import zipfile
import shutil
verbose = False

def moodle_gradesheet(notebook_name, assign_name, csv_file, zip_file):        

    api = NbGraderAPI()
    gradebook = api.gradebook

    archive = zipfile.ZipFile(zip_file)

    # IGNORE .csv files
    ignored_ext = ['csv']

    fnames = {}
    # read all the filenames, and get the submission
    # creates a dictionary of submissions for each student
    # keys are the moodle participent number ("Identifier")
    # values are a sequence of files matching this
    for f in archive.filelist:
        fname = f.filename
        
        # There should be a better way to code this
        if True in [ fname.endswith('.'+ext) for ext in ignored_ext ]:
            continue
        
        match = re.match("[\*\w\-\'\s\.]+_([0-9]+)_.*", fname)
        if match:
            if match.groups()[0] in fnames.keys():
                fnames[match.groups()[0]].append(fname)
            else:
                fnames[match.groups()[0]] = [fname]
        else:
            print("Did not match ", fname)

    with open(csv_file, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f) 
        assign_matric = {} 
        n_rows = 0
        successful_files = 0
        missing_files = 0
        problem_files = 0
            
        for line in reader:        
            
            ident, fullname, email, status, grade, max_grade = (line['Identifier'], line['Full name'], line["Email address"], 
                                                                line['Status'], line['Grade'], line['Maximum Grade'])

            should_be_submission =  "Submitted" in status

            # make sure we have this student in our records
            unique_id = email[0:email.index('@')]
            try:
                result = gradebook.find_student(unique_id)
            except nbgrader.api.MissingEntry:
                print("Creating gradebook entry for ", unique_id)
                gradebook.update_or_create_student(unique_id, first_name=fullname, last_name="", email=email)

                
            # map assignment numbers to matric numbers
            matric = email[0:email.index('@')]
            match = re.match('Participant ([0-9]+)', ident)
            if not match:
                print(f"Could not find identity for participant {ident}")
                continue
            
            ident = match.groups()[0]
            assign_matric[ident] = matric
            
            n_rows += 1
            if ident in fnames:                
                # extract each file to the submission directory
                submission_path = os.path.join("submitted", matric, assign_name)
                try:
                    os.makedirs(submission_path)
                except:
                    pass
                
                for fname in fnames[ident]:
                    # if the file ends with ipynb, then rename, otherwise don't
                    if fname.endswith('.ipynb'):
                        notebook_file = notebook_name + ".ipynb"
                    else:
                        notebook_file = fname
                    if verbose:
                        print("Extracting {notebook} to {path}".format(notebook=notebook_file, path=submission_path))

                    source = archive.open(fname)
                    target = open(os.path.join(submission_path, notebook_file), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
                    
                    successful_files += 1
            else:
                # submission was in the CSV file, but we don't have a zip file
                if should_be_submission:
                    print("*** WARNING! No submission for", fullname, matric, "but submission status was", status, "***")
                    problem_files += 1
                else:
                    # submission was not listed in the CSV file as being submitted
                    if verbose:
                        print("No submission for ", fullname, matric, status, "as expected")
                    missing_files +=1

        # print out a summary of what was processed
        print("""{n_files:d} succesfully extracted of {total_zip:d} non-ignored files in the ZIP archive.
{missing:d} files were not submitted, as expected.
{problem:d} files were missing, but showed as submitted on Moodle.
{total:d} records were processed, for {total_csv} rows in the CSV.
""".format(n_files=successful_files, missing=missing_files, problem=problem_files,
total=successful_files+missing_files+problem_files,
total_zip = sum([ len(v) for v in fnames.values()]), total_csv=n_rows))
            

    
import sys

if len(sys.argv)!=3:
    print("""
        Usage:
        
        collect_files.py <assignment_id> <notebook_name>
        
        # must have exactly two files in imports/ being

            <assignment>.csv <assignment>.zip

        The results will be copied into submitted/<matric_id>/<assignment_id>/
        
        NB You MUST run this script from the course directory
           The assignment_id must be the same as the folder in nbgrader eg coursework_1.
           The notebook name must be the same as the ipynb filename in the release/<assignment_id> folder in nbgrader
           The ipynb submission will be renamed <notebook_name>.ipynb; all other files will not.

    """)
    sys.exit()

assign_id, notebook_name = sys.argv[1], sys.argv[2]

import_dir = "imports"

if len(os.listdir(import_dir)) != 2:
    print("There are more than two files in the import directory.  Please only have the submission zip and grading worksheet csv file here.")
    sys.exit()

zip_file = [s for s in os.listdir(import_dir) if s.endswith('.zip')]
csv_file = [s for s in os.listdir(import_dir) if s.endswith('.csv')]
if len(zip_file) != 1:
    print("Can't find the submission zip in", import_dir)
    sys.exit()

if len(csv_file) != 1:
    print("Can't find the grading worksheet csv file in", import_dir)
    sys.exit()

zip_file = os.path.join(import_dir, zip_file[0])
csv_file = os.path.join(import_dir, csv_file[0])

moodle_gradesheet(notebook_name, assign_id, csv_file, zip_file)
