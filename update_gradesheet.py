import nbgrader, csv, codecs, sys, os, shutil
from nbgrader.apps import NbGraderAPI
import zipfile
verbose = False

def zip(out, root):
    shutil.make_archive(out, 'zip', root)

import_dir = "imports"
export_dir = "exports"

def moodle_gradesheet(assignment, outputname, with_feedback=True):    
    
    api = NbGraderAPI()
    gradebook = api.gradebook
    
    if len(os.listdir(import_dir)) != 2:
        print("There are more than two files in the import directory.  Please only have the submission zip and grading worksheet csv file here.")
        sys.exit()
    
    csv_file = [s for s in os.listdir(import_dir) if s.endswith('.csv')]
    if len(csv_file) != 1:
        print("Can't find the grading worksheet csv file in", import_dir)
        sys.exit()
    
    csv_file = csv_file[0]
    
    with open(os.path.join(import_dir, csv_file), newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
    
        fname =  os.path.join(export_dir, csv_file)
        
        if with_feedback:
            zip_file = os.path.join(export_dir, outputname+"_feedback.zip")

            archive = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
        
        with open(fname, 'w', encoding='utf-8', newline='') as out:
            writer = csv.DictWriter(out, reader.fieldnames)
            writer.writeheader()
            for line in reader:        
                email, ident, fullname, status, grade, max_grade = line["Email address"], line['Identifier'], line['Full name'], line['Status'], line['Grade'], line['Maximum Grade']                        
                unique_id = email[0:email.index('@')]
                try:
                    submission = gradebook.find_submission(assignment, unique_id)
                except:
                    if "Submitted" in status:
                        print("WARNING: No submission for {id} in assignment {assign}".format(id=unique_id ,assign=assignment))
                    else:
                        if verbose:
                            print("\tNo submission for {id} in assignment {assign}, as expected".format(id=unique_id, assign=assignment))
                else:
                    if verbose:
                        print("\tProcessing submission for {id} in assignment {assign}".format(id=unique_id, assign=assignment))

                    fbk_path = os.path.join("feedback", unique_id, assignment)

                    try:                    
                        
                        files = [os.path.join(fbk_path, f) for f in os.listdir(fbk_path) if f.endswith('.html')]
                        
                        assign_id = ident[12:]
                        # For Chester this is "Participant xxxxx"
                        
                        # create the path to the feedback file
                        fbk_full_path = "{fullname}_{assign_id}_assignsubmission_file_".format(fullname=fullname, 
                            assign_id=assign_id)
                        if with_feedback:
                            for f in files:
                                archive.write(f, arcname=os.path.join(fbk_full_path, os.path.basename(f)))
                        
                    except FileNotFoundError:
                        print("HTML feedback file for {fullname} {id} {assign} is missing".format(id=unique_id,
                        fullname=fullname, assign=assignment))
                        # no feedback to generate
                
                    line['Grade'] = submission.score

                    # warn about dubious scores
                    if line['Grade']<=0 or line['Grade']>submission.max_score:
                        print("Warning: {matric} {name} has a score of {grade}".format(matric=unique_id,
                        name=fullname, grade=line['Grade']))

                    # correct the maximum grade
                    line['Maximum Grade'] = submission.max_score
                    writer.writerow(line)
                
            print("Wrote to {0}".format(fname))

            # tidy up the feedback file
            if with_feedback:
                archive.close()
                    
            
if __name__=="__main__":
    if len(sys.argv)!=3:
            print("""
            Usage:
            
                update_gradesheet.py <assign> <outputname>
                
            Updates a CSV file gradesheet (which must have be downloaded from
            Moodle with "offline gradesheets" enabled in the assignment settings) with
            the results from grading the assignment <assign>.
            
            The input will be the only csv file in imports/
            The output will be put in exports/
            
            Feedback will be zipped up into exports/<outputname>.zip and this
            can be uploaded to Moodle if "Feedback files" is enabled. This uploads all student
            feedback in one go.
            
            """)
            exit(-1)
    
    assignment, outputname = sys.argv[1], sys.argv[2]
    print("Updating gradesheet for {0}...".format(assignment))
    moodle_gradesheet(assignment, outputname)
    
