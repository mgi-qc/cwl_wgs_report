__author__ = 'Thomas Antonacci'

import csv
import os
import glob
from datetime import datetime
from string import Template
import copy
import argparse


def print_line_to_terminal(n=None):
    i = 0
    if n is None:
        n = 15
    divider = ''
    while i < n:
        divider += '-'
        i += 1
    print(divider)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def metric_pass(metric_name, value, metrics_tracked_dict):

    if metrics_tracked[metric_name]['gl'] == 'l':
        if float(value) < metrics_tracked_dict[metric_name]['value']:
            return True
        else:
            return False
    elif metrics_tracked[metric_name]['gl'] == 'g':

        if float(value) > metrics_tracked_dict[metric_name]['value']:
            return True
        else:
            return False


def compare_dates(date1, date2):
    m1 = date1[0]+date1[1]
    m2 = date2[0]+date2[1]

    d1 = date1[2]+date1[3]
    d2 = date2[2]+date2[3]

    y1 = date1[4]+date1[5]
    y2 = date2[4]+date2[5]

    if int(y1) == int(y2):
        if int(m1) == int(m2):
            if int(d1) > int(d2):
                return True
            else:
                return False
        elif int(m1) > int(m2):
            return True
        else:
            return False
    elif int(y1) > int(y2):
        return True
    else:
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


parser = argparse.ArgumentParser()
parser.add_argument('-nod', help='Turn off directory creation', action='store_true')
parser.add_argument('-f', help='Name of metrics file the report will use', type=str)
args = parser.parse_args()


mm_dd_yy = datetime.now().strftime("%m%d%y")

# get file base on args
if args.f:
    file = args.f
    metrics_files = [file]
else:
    # glob for metrics file
    if not glob.glob('*.cwl.metrics.*.tsv'):
        exit('No metrics file found!')
    else:
        metrics_files = glob.glob('*.cwl.metrics.*.tsv')

# Get template file(specific to pipeline)
# #For use on server
# if not os.path.isfile('/gscmnt/gc2783/qc/GMSworkorders/reports/wgs_results_template_file.txt'):
#     exit('Template file not found!')
#
# with open('/gscmnt/gc2783/qc/GMSworkorders/reports/wgs_results_template_file.txt') as tf:
#     temp_read = tf.read()
#     template = Template(temp_read)

# For LOCAL use:
if not os.path.isfile('wgs_results_template_file.txt'):
    exit('Template file not found!')
with open('wgs_results_template_file.txt') as tf:
    temp_read = tf.read()
    template = Template(temp_read)

# Tracked metrics : passing value : greater/less than
metrics_tracked = {'HAPLOID COVERAGE': {'value': 0, 'gl': 'g'},
                   'discordant_rate': {'value': 5, 'gl': 'l'},
                   'inter-chromosomal_Pairing rate': {'value': 0.05, 'gl': 'l'},
                   'FREEMIX': {'value': 0.05, 'gl': 'l'},
                   'FOP: PF_MISMATCH_RATE': {'value': 0.05, 'gl': 'l'},
                   'SOP: PF_MISMATCH_RATE': {'value': 0.05, 'gl': 'l'}}

# Metrics to get averages for
metric_averages = ['HAPLOID COVERAGE', 'discordant_rate', 'inter-chromosomal_Pairing rate', 'FREEMIX',
                   'FOP: PF_MISMATCH_RATE','SOP: PF_MISMATCH_RATE', 'MEAN_INSERT_SIZE', 'STANDARD_DEVIATION',
                   'PCT_ADAPTER', 'PCT_20X','PCT_30X','PF_ALIGNED_BASES', 'PERCENT_DUPLICATION']

files_not_to_use = []
# get most recent file if more than one per work order
for file1 in metrics_files:
    for file2 in metrics_files:
        if file1.split('.')[0] == file2.split('.')[0]:
            if compare_dates(file1.split('.')[-2],file2.split('.')[-2]):
                if file2 not in files_not_to_use:
                    files_not_to_use.append(file2)
            elif compare_dates(file1.split('.')[-2],file2.split('.')[-2]):
                if file1 not in files_not_to_use:
                    files_not_to_use.append(file1)

for file in files_not_to_use:
    if file in metrics_files:
        metrics_files.remove(file)


for file in metrics_files:

    # get wo and date
    wo = file.split('.')[0]
    file_date = mm_dd_yy
    data_directories = []

    # outfile names
    results_out = '{}.cwl.results.{}.tsv'.format(wo, file_date)
    report_out = '{}.cwl.report.{}.txt'.format(wo,file_date)

    # Tracks totals, counts, and averages for metrics that need averages
    totals = {'count': {},
              'amount': {},
              'average': {}}

    # Temp file values that aren't averages or don't have own variable
    print_line_to_terminal(25)
    print('Report for {}:'.format(file))
    print('Confluence link: \nhttps://confluence.ris.wustl.edu/pages/viewpage.action?spaceKey=AD&title=WorkOrder+{}'.format(wo))

    """
    Option to QC based on total base pairs ipo coverage (both?)
    """
    print_line_to_terminal()
    print('QC based on:\n'
          '1. Haploid Coverage\n'
          '2. Haploid Coverage and Total Base Pairs(WIP)\n'
          '3. Total Base Pairs in place of Haploid Coverage(WIP)')

    use_hap = True
    while True:

        use_base = input()
        # redirect 2/3 to 1 until feature finished in metrics:
        use_base = 1

        if use_base == 1 or use_base == 2:

            print_line_to_terminal()

            while True and use_hap:
                hap_in = input('Enter Haploid Coverage value: ')

                if is_number(hap_in) and float(hap_in) > 0:
                    metrics_tracked['HAPLOID COVERAGE']['value'] = float(hap_in)
                    break
                else:
                    print('Please enter a positive number.')

        if use_base == 2 or use_base == 3:

            print_line_to_terminal()
            # reset metrics tracked
            base_chck = True
            while True:
                base_in = input('Please enter the required Total Base Pairs (in Gb): ')

                if is_number(base_in) and float(base_in) > 0:
                    base_in = float(base_in)
                    break
                else:
                    print('Please enter a positive number.')

            metrics_tracked['total_base_pairs'] = {'value': base_in, 'gl': 'g'}
            metric_averages.append('total_base_pairs')

        if use_base == 3:
            use_hap = False

            metrics_tracked.pop('HAPLOID COVERAGE')
            metric_averages.remove('HAPLOID COVERAGE')

        if use_base == 1 or use_base == 2 or use_base == 3:
            break
        else:
            print('Please enter 1,2, or 3.')

    print_line_to_terminal(25)

    """
    ========================================================================
    """

    # Get sequencing note
    while True:
        seq_in = input('Would you like to add a SEQUENCING_NOTE? y/n: ')

        if seq_in is 'y':
            print('Paste/Type SEQUENCING_NOTE below. \nEnter "return q return when finished": ')
            seq_notes = []
            while True:
                note_line = input()
                if note_line != 'q':
                    seq_notes.append(note_line)
                else:
                    break

            seq_notes = '\n'.join(seq_notes)
            break

        elif seq_in is 'n':
            seq_notes = ''
            print('Skipping SEQUENCING_NOTE')
            break
        else:
            print('Please enter y or n')

    print_line_to_terminal(25)

    # ini count and amount in totals dict
    for head in metric_averages:
        totals['count'][head] = 0
        totals['amount'][head] = 0

    # open files, read-in, and write to files
    with open(file, 'r') as results_in_file, open(results_out, 'w') as results_out_file:

        # set reader and get header from fieldnames
        results_dict_in = csv.DictReader(results_in_file, delimiter='\t')
        header = copy.deepcopy(results_dict_in.fieldnames)
        header.extend(['QC_Status', 'QC_failed_metrics', 'QC_metrics_not_found'])

        results_dict_out = csv.DictWriter(results_out_file, fieldnames=header, delimiter='\t')
        results_dict_out.writeheader()
        last_succeeded_build_id = []

        """1st Pass marking missing metrics"""
        missing_dict = {}
        missing_list = []
        skipped_list = []
        num_samples = 0

        for met in metrics_tracked:
            missing_dict[met] = 0

        for line in results_dict_in:
            num_samples += 1
            for met in metrics_tracked:
                try:
                    if line[met] is None or line[met] == '':
                        missing_dict[met] += 1
                        if met not in missing_list:
                            missing_list.append(met)
                except KeyError:
                    missing_dict[met] += 1
                    if met not in missing_list:
                        missing_list.append(met)

        if len(missing_list) >= 1:
            print('Missing metric values:')
            print('{0:<4}{1:<25}{2:<20}'.format('No.','Metrics', 'Missing/Total'))

            for met in missing_list:
                print('{0:<4}{1:<25}{2:<20}'.format(missing_list.index(met)+1,met,str(missing_dict[met]) + '/' + str(num_samples)))

            while len(skipped_list) < len(missing_list):
                miss_in = input('Enter the index of metric you wish to skip.\n(Enter 0 to exit): ')
                if is_int(miss_in):
                    miss_in = int(miss_in)
                    if 0 <= miss_in <= len(missing_list):
                        if miss_in == 0:

                            break
                        elif miss_in > 0:
                            skipped_list.append(missing_list[miss_in-1])
                            metrics_tracked.pop(missing_list[miss_in-1])
                            metric_averages.remove(missing_list[miss_in-1])
                else:
                    print('Enter an integer between 0 and {}.'.format(len(missing_list)))

        if len(skipped_list) == 0:
            print('No missing metircs')
        if len(metrics_tracked) == 0:
            exit('No report generated, all metrics skipped.')

        results_in_file.seek(0)
        next(results_in_file)

        failed_mets_count = {}
        for metric in metrics_tracked:
            failed_mets_count[metric] = 0

        pass_count = 0
        fail_count = 0
        na_count = 0

        for line in results_dict_in:
            data_directories.append(line['data_directory'])
            line_pass = True
            failed_mets = []
            missing_mets = []

            # Strip % from numbers
            for item in line:
                if '%' in line[item]:
                    line[item] = line[item].strip('%')

            for metric in metrics_tracked:
                if metric in line and line[metric] is None:
                    exit('{} not found in metrics files!')

                elif metric in line and is_number(line[metric]):
                    if not metric_pass(metric,line[metric], metrics_tracked):
                        failed_mets_count[metric] += 1
                        failed_mets.append(metric)
                        line_pass = False
                else:
                    missing_mets.append(metric)
                    line_pass = False

            if len(missing_mets) >= 1:
                print(','.join(missing_mets) + ' missing for {}'.format(line['sample_name']))
                line['QC_Status'] = 'NA'
                line['QC_metrics_not_found'] = ','.join(missing_mets)
            else:
                line['QC_metrics_not_found'] = 'NA'

            if len(failed_mets) >= 1:
                line['QC_failed_metrics'] = ','.join(failed_mets)
                if len(missing_mets) == 0:
                    fail_count += 1
                    line['QC_Status'] = 'Fail'
            else:
                line['QC_failed_metrics'] = 'NA'

            if line_pass:
                pass_count += 1
                line['QC_Status'] = 'Pass'

            last_succeeded_build_id.append(line['last_succeeded_build'])
            results_dict_out.writerow(line)

            for metric in metric_averages:
                if line[metric] and is_number(line[metric]):
                    totals['amount'][metric] += float(line[metric])
                    totals['count'][metric] += 1

        if pass_count == 0 and fail_count == 0:
            print("No report generated as no samples were QC'd")
            print_line_to_terminal(25)
        else:

            for metric in metric_averages:
                if totals['count'][metric] == 0:
                    totals['average'][metric] = 0
                else:
                    totals['average'][metric] = totals['amount'][metric]/totals['count'][metric]
            """
            Format special metrics and output values
            """

            for met in skipped_list:
                failed_mets_count[met] = 'Skipped'
                totals['average'][met] = 'Skipped'

            transfer_data_directory = 'NA'
            if not args.nod:
                transfer_data_directory = data_dir_check(data_directories, wo, mm_dd_yy)

            with open(report_out, 'w', encoding='utf-8') as fhr:
                fhr.write(template.substitute(WOID=wo,
                                              HAP_IN=hap_in,
                                              SEQUENCING_NOTE=seq_notes,
                                              SAMPLE_NUMBER=pass_count + fail_count,
                                              PASS_SAMPLES=pass_count,
                                              FAIL=fail_count,
                                              HAP_FAIL_COUNT=failed_mets_count['HAPLOID COVERAGE'],
                                              DIS_RT_FAIL_COUNT=failed_mets_count['discordant_rate'],
                                              INTER_CHR_FAIL_COUNT=failed_mets_count['inter-chromosomal_Pairing rate'],
                                              FREE_FAIL_COUNT=failed_mets_count['FREEMIX'],
                                              FOP_FAIL_COUNT=failed_mets_count['FOP: PF_MISMATCH_RATE'],
                                              SOP_FAIL_COUNT=failed_mets_count['SOP: PF_MISMATCH_RATE'],
                                              HAPLOID_COVERAGE=totals['average']['HAPLOID COVERAGE'],
                                              discordant_rate=totals['average']['discordant_rate'],
                                              inter_chromosomal_Pairing_rate = totals['average']['inter-chromosomal_Pairing rate'],
                                              FREEMIX=totals['average']['FREEMIX'],
                                              FOP_PF_MISMATCH_RATE=totals['average']['FOP: PF_MISMATCH_RATE'],
                                              SOP_PF_MISMATCH_RATE=totals['average']['SOP: PF_MISMATCH_RATE'],
                                              MEAN_INSERT_SIZE=totals['average']['MEAN_INSERT_SIZE'],
                                              STANDARD_DEVIATION=totals['average']['STANDARD_DEVIATION'],
                                              PCT_ADAPTER=totals['average']['PCT_ADAPTER'],
                                              PCT_20X=totals['average']['PCT_20X'],
                                              PCT_30X=totals['average']['PCT_30X'],
                                              PF_ALIGNED_BASES=totals['average']['PF_ALIGNED_BASES'],
                                              PERCENT_DUPLICATION=totals['average']['PERCENT_DUPLICATION'],
                                              TRANSFER_DIR=transfer_data_directory,
                                              RESULTS_SPREADSHEET=results_out,
                                              REPORT_FILE=report_out))

            print('Report generated for {}'.format(file))

            builds = ','.join(last_succeeded_build_id)

            with open('{}.Data_transfer_help.2.{}.txt'.format(wo, file_date), 'w') as df:
                df.write('Data Transfer Directory ={td}\ncd to parent data dir\ncd to model_data'
                         '\nmkdir data_transfer/{w}\nTransfer Commands:\n\ngenome model cwl-pipeline prep-for-transfer --md5sum'
                         ' --directory={td}  --builds {b}\n\n'
                         'genome model cwl-pipeline prep-for-transfer --md5sum'
                         ' --directory={td} model_groups.project.id={w}\n'.format(td=transfer_data_directory, w= wo, b=builds,))

            if na_count != 0:
                print('{} SAMPLES MISSING METRICS!'.format(na_count))
            print_line_to_terminal(25)
