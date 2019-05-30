#wgs report
__author__ = 'Thomas Antonacci'


#TODO   checks for metrics
#       write report
#       write Ssheet


import csv
import os
import sys
import glob
import datetime
import argparse
import subprocess
from string import Template


parser = argparse.ArgumentParser()
parser.add_argument('-nod', help='Turn off directory creation', action='store_true')
args = parser.parse_args()

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def data_dir_check(dir_list, woid, date):
    """Create and return transfer directory if 'model' found in dir path."""

    # return NA if no transfer dir found
    transfer_dir = 'NA'

    # iterate over data dirs
    for directory in dir_list:
        # if model found, create transfer dir and return path
        if os.path.isdir(directory) and 'model' in directory:

            dir_path_items = directory.split('/')

            for no, d in enumerate(dir_path_items):

                if 'model' in d:

                    model_directory = '/'.join(dir_path_items[:no + 1]) + '/'
                    transfer_dir = os.path.join(model_directory, 'data_transfer/{}_{}/'.format(woid, date))

                    if os.path.isdir(transfer_dir):
                        print('Transfer Directory already exists: {}'.format(transfer_dir))
                        return 'NA'

                    if os.path.isdir(model_directory) and not os.path.isdir(transfer_dir):
                        try:
                            os.mkdir(transfer_dir)
                        except OSError:
                            # raise OSError("Can't create destination directory {}!".format(transfer_dir))
                            return 'NA'
                        print('Data transfer directory created:\n{}'.format(transfer_dir))
                        return transfer_dir

    return transfer_dir

mm_dd_yy = datetime.datetime.now().strftime("%m%d%y")

#Check for metrics file;
if not glob.glob('*.cwl.metrics.*.tsv'):
    sys.exit('cwl.metrics file not found')
else:
    metrics_files = glob.glob('*.cwl.metrics.*.tsv'.format(mm_dd_yy))

#Check, open, and create template file using Template;
if not os.path.isfile('/gscmnt/gc2783/qc/GMSworkorders/reports/wgs_results_template_file.txt'):
    sys.exit('Template file not found.')

with open('/gscmnt/gc2783/qc/GMSworkorders/reports/wgs_results_template_file.txt', 'r', encoding='utf-8') as fh:
    template = fh.read()
    template_file = Template(template)


metrics_tracked = ['HAPLOID COVERAGE', 'discordant_rate', 'inter-chromosomal_Pairing rate',
                    'FREEMIX', 'FOP: PF_MISMATCH_RATE', 'SOP: PF_MISMATCH_RATE']

totals_list = ['HAPLOID COVERAGE', 'discordant_rate', 'inter-chromosomal_Pairing rate', 'FREEMIX',
                'FOP: PF_MISMATCH_RATE','SOP: PF_MISMATCH_RATE', 'MEAN_INSERT_SIZE', 'STANDARD_DEVIATION',
                'PCT_ADAPTER', 'PCT_20X','PCT_30X','PF_ALIGNED_BASES', 'PERCENT_DUPLICATION']

for file in metrics_files:


    file_name = file.split('.')[0]
    file_date = file.split('.')[-2]
    SSheet_outfile = '{}.cwl.results.{}.tsv'.format(file_name, file_date)
    report_outfile = '{}.cwl.report.{}.txt'.format(file_name, file_date)

    # Ini. dicts
    prnt_report = False
    template_file_dict = {}
    totals_dict = {}
    tot_cnt_dict = {}
    data_directories = []


    print('Confluence link: \nhttps://confluence.ris.wustl.edu/pages/viewpage.action?spaceKey=AD&title=WorkOrder+{}'.format(file_name))
    while True:

        hap_in = input('Please enter Haploid Coverage value for {}: '.format(file_name))
        if is_number(hap_in) and float(hap_in) > 0:
            hap_value = float(hap_in)
            break
        else:
            print('Please enter a positive number for Haploid Coverage. ')

    while True:
        seq_in = input('\nWould you like to add a SEQUENCING_NOTE? y/n: ')

        if seq_in is 'y':
            seq_notes = []
            while True:
                note_line = input()
                if note_line != 'q':
                    seq_notes.append(note_line)
                else:
                    break
            break

        elif seq_in is 'n':
            seq_notes = ['']
            print('Skipping SEQUENCING_NOTE')
            break
        else:
            print('Please enter y or n')

    for total in totals_list:
        totals_dict[total] = 0

    for metric in metrics_tracked:
        template_file_dict[metric] = 0

    for total in totals_list:
        tot_cnt_dict[total] = 0

    # Metrics File Open, Check Metrics, Generate 'results', Get Totals;
    with open(file, 'r') as fh, open(SSheet_outfile, 'w') as of:
        metrics_dict = csv.DictReader(fh, delimiter='\t')
        header = metrics_dict.fieldnames

        ofd = csv.DictWriter(of, fieldnames=header, delimiter='\t')
        header.extend(['QC_Status','QC_failed_metrics'])
        ofd.writeheader()

        last_succeeded_build_id = []
        #ini totals variables

        count = 0
        pass_count = 0
        fail_count = 0


        for line in metrics_dict:

            line['QC_failed_metrics'] = ''
            failed_metrics = []
            template_file_dict['WOID'] = line['WorkOrder']
            data_directories.append(line['data_directory'])

            #Check metrics...
            met_to_check = []
            met_not_check = []
            for met in metrics_tracked:
                if met in line and is_number(line[met]):
                    met_to_check.append(met)
                    prnt_report = True
                else:
                    met_not_check.append(met)

            if 'HAPLOID COVERAGE' in met_to_check and float(line['HAPLOID COVERAGE']) < float(hap_value):
                failed_metrics.append('HAPLOID COVERAGE')
                template_file_dict['HAPLOID COVERAGE'] += 1

            if 'discordant_rate' in met_to_check and float(line['discordant_rate']) > 5:
                failed_metrics.append('discordant_rate')
                template_file_dict['discordant_rate'] += 1

            if 'inter-chromosomal_Pairing rate' in met_to_check and float(line['inter-chromosomal_Pairing rate']) > 0.05:
                failed_metrics.append('inter-chromosomal_Pairing rate')
                template_file_dict['inter-chromosomal_Pairing rate'] += 1

            if 'FREEMIX' in met_to_check and float(line['FREEMIX']) > 0.05:
                failed_metrics.append('FREEMIX')
                template_file_dict['FREEMIX'] += 1

            if 'FOP: PF_MISMATCH_RATE' in met_to_check and float(line['FOP: PF_MISMATCH_RATE']) > 0.05:
                failed_metrics.append('FOP: PF_MISMATCH_RATE')
                template_file_dict['FOP: PF_MISMATCH_RATE'] += 1

            if 'SOP: PF_MISMATCH_RATE' in met_to_check and float(line['SOP: PF_MISMATCH_RATE']) > 0.05:
                failed_metrics.append('SOP: PF_MISMATCH_RATE')
                template_file_dict['SOP: PF_MISMATCH_RATE'] += 1

            count += 1

            if len(met_to_check) != len(metrics_tracked):
                line['QC_Status'] = 'NA'
                line['QC_failed_metrics'] = ','.join(failed_metrics)

            elif len(failed_metrics) > 0:
                line['QC_Status'] = 'FAIL'
                line['QC_failed_metrics'] = ','.join(failed_metrics)
                fail_count += 1

            else:
                line['QC_Status'] = 'PASS'
                line['QC_failed_metrics'] = 'NA'
                pass_count += 1

            for total in totals_list:
                if total in line and is_number(line[total]):
                    totals_dict[total] += float(line[total])
                    tot_cnt_dict[total] += 1

            last_succeeded_build_id.append(line['last_succeeded_build'])
            ofd.writerow(line)

        avg_dict = {}
        print('{} not found for {}'.format(', '.join(met_not_check), file_name))

        for total in totals_list:
            if totals_dict[total] != 0:
                avg_dict[total] = totals_dict[total] / tot_cnt_dict[total]
            else:
                avg_dict[total] = 'NA'

        if prnt_report:

            for metric in metrics_tracked:
                if template_file_dict[metric] is 0 and pass_count + fail_count != count:
                    template_file_dict[metric] = 'NA'

            #set unchecked metrics to NA
            #print missing metric
            ##print report

            transfer_data_directory = 'NA'
            if not args.nod:
                transfer_data_directory = data_dir_check(data_directories, template_file_dict['WOID'], mm_dd_yy)

            with open(report_outfile, 'w', encoding='utf-8') as fhr:
                fhr.write(template_file.substitute(WOID = template_file_dict['WOID'],
                                                   HAP_IN = hap_in,
                                                   SEQUENCING_NOTE = '\n'.join(seq_notes),
                                                   SAMPLE_NUMBER = count,
                                                   PASS_SAMPLES = pass_count,
                                                   FAIL = fail_count,
                                                   HAP_FAIL_COUNT = template_file_dict['HAPLOID COVERAGE'],
                                                   DIS_RT_FAIL_COUNT = template_file_dict['discordant_rate'],
                                                   INTER_CHR_FAIL_COUNT = template_file_dict['inter-chromosomal_Pairing rate'],
                                                   FREE_FAIL_COUNT = template_file_dict['FREEMIX'],
                                                   FOP_FAIL_COUNT = template_file_dict['FOP: PF_MISMATCH_RATE'],
                                                   SOP_FAIL_COUNT = template_file_dict['SOP: PF_MISMATCH_RATE'],
                                                   HAPLOID_COVERAGE = avg_dict['HAPLOID COVERAGE'],
                                                   discordant_rate = avg_dict['discordant_rate'],
                                                   inter_chromosomal_Pairing_rate = avg_dict['inter-chromosomal_Pairing rate'],
                                                   FREEMIX = avg_dict['FREEMIX'],
                                                   FOP_PF_MISMATCH_RATE = avg_dict['FOP: PF_MISMATCH_RATE'],
                                                   SOP_PF_MISMATCH_RATE= avg_dict['SOP: PF_MISMATCH_RATE'],
                                                   MEAN_INSERT_SIZE = avg_dict['MEAN_INSERT_SIZE'],
                                                   STANDARD_DEVIATION = avg_dict['STANDARD_DEVIATION'],
                                                   PCT_ADAPTER = avg_dict['PCT_ADAPTER'],
                                                   PCT_20X = avg_dict['PCT_20X'],
                                                   PCT_30X = avg_dict['PCT_30X'],
                                                   PF_ALIGNED_BASES = avg_dict['PF_ALIGNED_BASES'],
                                                   PERCENT_DUPLICATION = avg_dict['PERCENT_DUPLICATION'],
                                                   TRANSFER_DIR=transfer_data_directory,
                                                   RESULTS_SPREADSHEET = SSheet_outfile))
            print('Report generated for {}'.format(file_name))
            print('-----------------------')

            builds = ','.join(last_succeeded_build_id)

            with open('{}.Data_transfer_help.{}.txt'.format(template_file_dict['WOID'], file_date), 'w') as df:
                df.write('Data Transfer Directory ={td}\ncd to parent data dir\ncd to model_data'
                      '\nmkdir data_transfer/{w}\nTransfer Commands:\n\ngenome model cwl-pipeline prep-for-transfer --md5sum'
                      ' --directory={td}  --builds {b}\n\n'
                      'genome model cwl-pipeline prep-for-transfer --md5sum'
                      ' --directory={td} model_groups.project.id={w}\n'.format(td=transfer_data_directory, w=template_file_dict['WOID'], b=builds,))

        else:
            print('No report generated for {}; No required metrics found.'.format(file_name))
            print('-----------------------------------------------------')
