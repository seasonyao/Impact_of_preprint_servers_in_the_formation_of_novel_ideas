import os
import pandas as pd
import time
from collections import defaultdict

input_file = "Path/to/input/pickle"
phrases_df = pd.read_pickle(input_file)
phrases = phrases_df.tolist()

#The input pickle is generated using the key phrase extraction method described earlier. An alternate input could be a custom list of phrases like below rather than the input pickle file.

# phrases = ["10X_Genomics", "Chromosome_conformation", "CRISPR", "CyTOF", "electrospray_ionization",
#                 "ELISA", "Enzyme_linked_immunosorbent_assay", "Exome", "FACS", "Fluorescence_Activated_Cell_Sorting",
#                 "gene_editing", "Laser_capture_microdissection", "LINNAEUS", "MALDI", "Mass_cytometry",
#                 "Mass_Spectroscopy", "Matrix-assisted_laser_desorption_ionization", "Microfluidics",
#                 "Proximity_Extension_Assay", "scATAC-seq", "Translating_Ribosome_Affinity_Purification",
#                 "Whole_Genome_Amplification"]


pmc_dir = "Path/to/raw/PMC/data"
pmc_csv = "Path/to/PMC/csv"
out_txt = "Path/to/output/txtFile"
out_json_file = "Path/to/output/jsonFile"



# set start and end indexs for the top phrases in the input pickle generated by textRank
start = 0
end = 10000

time1 = time.time()
for i, phrase in enumerate(phrases):
    phrase = phrase.replace('_', ' ')
    if i>=start and i<end:
        print("Running for phrase: " + phrase)
        phrase_quoted ='\'' +  phrase.lower() + '\''
        cmd = "bash Path/to/find_pmc_phrase.sh -p " + phrase_quoted + " -o " + out_txt + phrase.replace(" ", "_") + ".txt -c 24 -d " + pmc_dir
        os.system(cmd)
print("time = " + str(time.time() - time1))



df = pd.read_csv(pmc_csv, header=0, index_col=0, delimiter=r",", usecols = ['pmid', 'pmc', 'publication_date'])
# here, we calculate phrases' raw frequency, normlized frequency, gradient of frequency, and normlized gradient, and then we save them as a .json file.
def cal_curves_y(phrase_name, all_doc_in_year):
    f = open("Path/to/txtFile/" + phrase_name + ".txt")
    pmc_search_result = f.readlines()

    phrase_year_month_freq = defaultdict(int) 
    for pmc in pmc_search_result:
        try:
            year = df[df['pmc']==int(pmc.strip('PMC\n'))].iloc[0]['year']
            month = df[df['pmc']==int(pmc.strip('PMC\n'))].iloc[0]['month']
            phrase_year_month_freq[year + 0.01*month] += 1
        except:
            pass

    #raw_freq
    y_raw_freq = []
    for year in range(1978, 2020):
        for month in range(1, 13):
            try:
                y_raw_freq.append(phrase_year_month_freq[year + 0.01*month])
            except:
                y_raw_freq.append(0)
    
    #norm_freq
    y_norm_freq = []
    for year in range(1978, 2020):
        for month in range(1, 13):
            try:
                y_norm_freq.append(phrase_year_month_freq[year + 0.01*month]/all_doc_in_year[year])
            except:
                y_norm_freq.append(0)
                 
    #cal gradient of freq
    y_gradient = []
    for year in range(1978, 2020):   
        for month in range(1, 13):
            if year == 1978 and month == 1:
                continue
            if month == 1:
                y_gradient.append((phrase_year_month_freq[year + 0.01*month]-phrase_year_month_freq[(year-1)+0.01*12]))
            else:
                y_gradient.append((phrase_year_month_freq[year + 0.01*month]-phrase_year_month_freq[year+0.01*(month-1)]))
        
    #cal norm_slop of freq
    y_norm_slop = []
    for year in range(1978, 2020): 
        for month in range(1, 13):
            if year == 1978 and month == 1:
                continue
                
            if month == 1:
                if phrase_year_month_freq[(year-1)+0.01*12]==0:
                    y_norm_slop.append(0)
                else:
                    y_norm_slop.append((phrase_year_month_freq[year+0.01*month]-phrase_year_month_freq[(year-1)+0.01*12])/phrase_year_month_freq[(year-1)+0.01*12])

            else:
                if phrase_year_month_freq[year+0.01*(month-1)]==0:
                    y_norm_slop.append(0)
                else:
                    y_norm_slop.append((phrase_year_month_freq[year+0.01*month]-phrase_year_month_freq[year+0.01*(month-1)])/phrase_year_month_freq[year+0.01*(month-1)])

                    
            
    return [y_raw_freq, y_norm_freq, y_gradient, y_norm_slop]


phrases_dict = {}

for phrase_name in phrases:
    phrases_dict[phrase_name] = cal_curves_y(phrase_name, df['year'].value_counts())
    
with open(out_json_file, 'w') as fp:
    json.dump(phrases_dict, fp)