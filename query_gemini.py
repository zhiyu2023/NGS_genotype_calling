#!/usr/local/Anaconda/envs/py3.5/bin/python


import argparse
from argparse import RawTextHelpFormatter
import subprocess
import xlsxwriter
from collections import Counter
import datetime
import sys
from textwrap import dedent
import re
import pandas as pd

#########PARSER##############
parser = argparse.ArgumentParser(description=\
    """
	Queries gemini (v0.18) database to identify variants matching 
	models of automosomal recessive, de novo, mendelian error, 
	compound hets and autosomal dominant. 
	
	Returns an xlsx file of the results.
	
	Input: 
		database to query 
		family to analyze (optional) 
		name for output xlsx file.
	
	Examples (no need for sbatch): 
		query_gemini.py --database CCG0.gemini.db --family CCG0_800042 CCGO_800042.variants.xlsx 
		query_gemini.py --database CCGO.gemini.db --family all.variants.xlsx""", 

	formatter_class=RawTextHelpFormatter)

parser.add_argument('-d','--database',required=True)
parser.add_argument('-f','--family')
parser.add_argument('-o','--output_name', required=True)
parser.add_argument('-l','--lenient', default='No', help="Use '-l Yes' to  to use lenient settings on Autosome Dominant. Useful \
					for situations where phenotype of parents uncertain or unknown")
#########CODE#############
def autosomal_recessive(db, family):
	filter = " --filter \"aaf_esp_all < 0.01 AND aaf_1kg_all < 0.01 AND aaf_exac_all < 0.01 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL\" --min-gq 20 "
	if family=='-':
		ar_query = "gemini autosomal_recessive" + columns + db + " " + filter
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		ar_query = "gemini autosomal_recessive" + new_columns + \
					"--families " + family + " " + db + " " + filter
	ar = subprocess.check_output(ar_query,shell=True).decode('utf-8')
	ar = ar.split('\n')
	ar = reorder(ar)
	return(ar,ar_query)

def de_novo(db, family):
	filter = " --filter \"aaf_esp_all < 0.005 AND aaf_1kg_all < 0.005 AND aaf_exac_all < 0.005 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL\" --min-gq 20 "
	if family=="-":
		dn_query = "gemini de_novo" + columns + db + " " + filter
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		dn_query = "gemini de_novo" + new_columns + \
					"--families " + family + " " + db + " " + filter
	dn = subprocess.check_output(dn_query,shell=True).decode('utf-8')	
	dn = dn.split('\n')
	return(dn, dn_query)

def autosomal_dominant(db, family, lenient):
	filter = " --filter \"aaf_esp_all < 0.0001 AND aaf_1kg_all < 0.0001 AND aaf_exac_all < 0.0001 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL\" --min-gq 20 "
	if family == "-":
		ad_query = "gemini autosomal_dominant" + columns + db + " " + filter
	if lenient == 'yes':
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		ad_query = "gemini autosomal_dominant --lenient" + new_columns + \
					"--families " + family + " " + db + " " + filter
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		ad_query = "gemini autosomal_dominant" + new_columns + \
					"--families " + family + " " + db + " " + filter
	ad = subprocess.check_output(ad_query,shell=True).decode('utf-8')
	ad = ad.split('\n')
	return(ad, ad_query)

def x_linked_recessive(db, family):
	filter = " --filter \"aaf_esp_all < 0.005 AND aaf_1kg_all < 0.005 AND aaf_exac_all < 0.005 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL\" --min-gq 20 "
	if family == "-":
		xlr_query = "gemini x_linked_recessive" + columns + db + " " + filter
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		xlr_query = "gemini x_linked_recessive" + new_columns + \
					"--families " + family + " " + db + " " + filter
	xlr = subprocess.check_output(xlr_query,shell=True).decode('utf-8')
	xlr = xlr.split('\n')
	return(xlr, xlr_query)
	
def x_linked_dom(db, family):
	filter = " --filter \"aaf_esp_all < 0.005 AND aaf_1kg_all < 0.005 AND aaf_exac_all < 0.005 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL\" --min-gq 20 "
	if family == "-":
		xld_query = "gemini x_linked_dominant" + columns + db + " " + filter
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		xld_query = "gemini x_linked_dominant" + new_columns + \
					"--families " + family + " " + db + " " + filter
	xld = subprocess.check_output(xld_query,shell=True).decode('utf-8')
	xld = xld.split('\n')
	return(xld, xld_query)

def x_linked_de_novo(db, family):
	filter = " --filter \"aaf_esp_all < 0.005 AND aaf_1kg_all < 0.005 AND aaf_exac_all < 0.005 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL\" --min-gq 20 "
	if family == "-":
		xldn_query = "gemini x_linked_de_novo" + columns + db + " " + filter
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		xldn_query = "gemini x_linked_de_novo" + new_columns + \
					"--families " + family + " " + db + " " + filter
	xldn = subprocess.check_output(xldn_query,shell=True).decode('utf-8')
	xldn = xldn.split('\n')
	return(xldn, xldn_query)

def mendel_errors(db, family):
	filter = " --filter \"aaf_esp_all < 0.005 AND aaf_1kg_all < 0.005 AND aaf_exac_all < 0.005 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL\" --min-gq 20 "
	if family == '-':
		me_query = "gemini mendel_errors" + columns + db + " " + filter
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		me_query = "gemini mendel_errors" + new_columns + \
					"--families " + family + " " + db + " " + filter
	me = subprocess.check_output(me_query,shell=True).decode('utf-8')
	me = me.split('\n')	
	return(me, me_query)

def comp_hets(db, family):
	filter = " --filter \"aaf_esp_all < 0.01 AND aaf_1kg_all < 0.01 AND aaf_exac_all < 0.01 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL\" --min-gq 20 --max-priority 2 "
	if family == "-":
		ch_query = "gemini comp_hets" + columns + db + " " + filter
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		ch_query = "gemini comp_hets" + new_columns + \
					"--families " + family + " " + db + " " + filter
	ch = subprocess.check_output(ch_query,shell=True).decode('utf-8')
	ch = ch.split('\n')
	####
	# reorder to put common comp_het genes (more than 4 variants) at bottom
	####
	# find position of the gene column
	print(ch[0])
	gene_index = ch[0].split('\t').index('gene')
	# get counts for genes (last item in ch is blank)
	gene_counts = Counter([x.split('\t')[gene_index] for x in ch[:-1]])
	# id genes that appear more than 4 times
	common_genes = [x[0] for x in gene_counts.items() if x[1]>4]
	unique_ch = [x for x in ch[:-1] if x.split('\t')[gene_index] not in common_genes]
	common_ch = [x for x in ch[:-1] if x.split('\t')[gene_index] in common_genes]
	new_ch = unique_ch
	new_ch.append('\n')
	new_ch.append('Below are likely false positives (more than four \
				variants in a gene are unlikely to be a deleterious comp het)')
	new_ch.append('\n')
	new_ch.extend(common_ch)
	return(new_ch, ch_query)

def acmg_incidentals(db, family):
	#ACMG http://www.ncbi.nlm.nih.gov/clinvar/docs/acmg/ (list pulled 2016-07-11) incidental gene list
	filter = "aaf_esp_all < 0.01 AND aaf_1kg_all < 0.01 AND aaf_exac_all < 0.01 AND (is_coding=1 OR is_splicing=1 OR impact_severity='HIGH') \
				AND filter IS NULL"
	acmg_genes = 'ACTA2','ACTC1','APC','APOB','BRCA1','BRCA2','CACNA1S','COL3A1','DSC2','DSG2','DSP','FBN1','GLA','KCNH2','KCNQ1',\
				 'LDLR','LMNA','MEN1','MLH1','MSH2','MSH6','MUTYH','MYBPC3','MYH11','MYH7','MYL2','MYL3','MYLK','NF2','PCSK9','PKP2',\
				 'PMS2','PRKAG2','PTEN','RB1','RET','RYR1','RYR2','SCN5A','SDHAF2','SDHB','SDHC','SDHD','SMAD3','STK11','TGFBR1',\
				 'TGFBR2','TMEM43','TNNI3','TNNT2','TP53','TPM1','TSC1','TSC2','VHL','WT1'
	columns = "chrom, start, end, codon_change, aa_change, type, impact, \
           	   impact_severity, gene, clinvar_gene_phenotype, clinvar_sig, pfam_domain, vep_hgvsp, \
         	   max_aaf_all, aaf_1kg_all, aaf_exac_all, exac_num_hom_alt, exac_num_het, \
           	   geno2mp_hpo_ct, gerp_bp_score, polyphen_score, cadd_scaled, sift_pred, \
           	   sift_score, vep_maxEntScan, vep_grantham, (gts).(*), (gt_ref_depths).(*), (gt_alt_depths).(*)"

	if family == "-":
		acmg_query = "gemini query --header -q \"SELECT " + columns + "FROM variants WHERE \
					  (gene IN (" + ",".join("'%s'" % g for g in acmg_genes) + ")) AND \
					  (clinvar_sig LIKE '%pathogenic%' OR impact_severity='HIGH') AND (" + filter + ")\"" + \
				 	  "--gt-filter \"(gt_types).(*).(!=HOM_REF).(count>=1)\" " + db
	else:
		new_columns = columns.replace('*','family_id=' + '\'' + family +'\'')
		acmg_query = "gemini query --header -q \"SELECT " + new_columns + "FROM variants WHERE \
					  (gene IN (" + ",".join("'%s'" % g for g in acmg_genes) + ")) AND \
					  (clinvar_sig LIKE '%pathogenic%' OR impact_severity='HIGH') AND (" + filter + ")\"" + \
					  " --gt-filter \"(gt_types).(family_id==" + "\'" + family + "\').(!=HOM_REF).(count>=1)\" " + db
	acmg = subprocess.check_output(acmg_query,shell=True).decode('utf-8')
	acmg = acmg.split('\n')
	if acmg[1] == '': 
		# most likely to be empty
		acmg = list('')
		acmg.append(dedent("""\
				No ACMG incidental findings to return. This does NOT mean there are no mutations in the ACMG 56 list, as sequencing
				technology does not fully cover every single relevant nucleotide."""))
	else:
		acmg.insert(0, dedent("""\
					POTENTIAL ACMG incidental findings found. This does NOT mean that the subject has damaging and actionable mutations. 
					This list of variants should be reviewed by a genetic counselor""")) 
	return(acmg, acmg_query)

def overview(db, queries):
	# pull useful info and  parameters from vcf header
	vcf_header_query = "gemini query --header -q \"SELECT * FROM vcf_header\" " + db
	vcf_header = subprocess.check_output(vcf_header_query,shell=True).decode('utf-8')
	vcf_header = vcf_header.split('\n')
	vcf_header_bits = []
	vcf_header_bits.extend([x for x in vcf_header if x.startswith("##FILTER")])
	vcf_header_bits.extend([x for x in vcf_header if x.startswith("##GATKCommandLine")])
	vcf_header_bits.extend([x for x in vcf_header if x.startswith("##reference")])
	vcf_header_bits.extend([x for x in vcf_header if x.startswith("##VEP")])
	vcf_header_bits.extend([x for x in vcf_header if x.startswith("#CHROM")])
	# summary stats, queries used, ped file
	stats_query = "gemini stats --gts-by-sample " + db
	stats = subprocess.check_output(stats_query,shell=True).decode('utf-8')
	stats = stats.split('\n')
	ped_query = "gemini query --header -q \"SELECT * FROM samples\" " + db
	ped = subprocess.check_output(ped_query,shell=True).decode('utf-8')
	ped = ped.split('\n')
	output = []
	output.append("Date and Time this file was generated")
	output.append(str(datetime.datetime.now().date()) + '\t' + str(datetime.datetime.now().time()))
	output.append('Overall genotypes by sample')
	output.extend(stats)
	output.append('PED information used for calls')
	output.append('Gender: 1=male, 2=female, 0=unknown')
	output.append('Phenotype: 1=unaffected, 2=affected, 0=unknown')
	output.append("Any column after 'phenotype' is not used in these queries")
	output.extend(ped)
	output.append('Gemini Queries')
	output.extend(queries)
	output.append('')
	output.append("Info on GATK commands and filtering, reference used, VEP version, samples in VCF")
	output.extend(vcf_header_bits)
	return(output)

def output_to_xlsx(data,sheet_name):
	worksheet = workbook.add_worksheet(sheet_name)
	row = 0
	col = 0
	# Handling for nothing found. Don't want anyone thinking a messup happened
	# Will print first bit of info if this logic screws up
	if len(data) < 2:
		worksheet.write(0,0, "No variants found")	
		worksheet.write(1,0, data[0])
	else:		
		for line in data:
			line = line.split('\t')
			for unit in line: 
				worksheet.write(row, col, unit)
				col += 1
			col = 0
			row += 1

def reorder(data):
	list_of_list = [item.split('\t') for item in data[0]]
	# into pandas data frame
	ar=pd.DataFrame(list_of_list[1:-1],columns=list_of_list[0])
	# custom ordering
	ar['impact_severity'] = pd.Categorical(ar['impact_severity'],['HIGH','MED','LOW'])
	#clinvar_sig_order = list(set(ar['clinvar_sig']))
	ar['max_aaf_all'] = ar['max_aaf_all'].astype(float)
	ar['cadd_scaled'] = ar['cadd_scaled'].replace(to_replace='None')
	ar['cadd_scaled'] = ar['cadd_scaled'].astype(float)
	ar = ar.sort_values(by=['impact_severity', 'impact', 'clinvar_sig', 'pfam_domain','vep_phenotypes','vep_pubmed','max_aaf_all'])	
	out = ar.to_csv(index=False,sep='\t').split('\n')
	return(out)

def main():
	db = args.database
	if args.family:
		family = args.family
	else:
		family = '-'
	lenient = args.lenient
	lenient = lenient.lower()
#	if lenient != 'no' or lenient != 'yes':
#		print("-l --lenient must be 'Yes' or 'No'")
#		sys.exit()
	# output time
	print('Running Autosomal Recessive')
	ar, ar_query = autosomal_recessive(db, family)
	output_to_xlsx(ar, "Autosomal Recessive")	

	print('Running De Novo')
	dn, dn_query = de_novo(db, family)
	output_to_xlsx(dn, "De Novo")	
	
	print('Running Autosomal Dominant')
	ad, ad_query = autosomal_dominant(db, family, lenient)
	output_to_xlsx(ad, "Autosomal Dominant")
	
	print('Running X-Linked Tests')
	xlr, xlr_query = x_linked_recessive(db, family)
	output_to_xlsx(xlr, "XLR")
	xld, xld_query = x_linked_dom(db, family)
	output_to_xlsx(xld, "XLD")
	xldn, xldn_query = x_linked_de_novo(db, family)
	output_to_xlsx(xldn, "XLDeNovo")
	
	print('Running Mendelian Errors')
	me, me_query = mendel_errors(db, family)
	output_to_xlsx(me, "Mendelian Errors")

	print('Running Compound Hets')
	ch, ch_query = comp_hets(db, family)
	output_to_xlsx(ch, "Compound Hets")

	print('Running ACMG incidental findings')
	acmg, acmg_query = acmg_incidentals(db, family)
	output_to_xlsx(acmg, "ACMG Incidental Findings")


	# get all queries in one list
	queries = []
	queries.append(re.sub(r'\s+',' ',ar_query)), queries.append(re.sub(r'\s+',' ',dn_query))
	queries.append(re.sub(r'\s+',' ',me_query)), queries.append(re.sub(r'\s+',' ',ch_query))
	queries.append(re.sub(r'\s+',' ',ad_query)), queries.append(re.sub(r'\s+',' ',acmg_query))
	queries.append(re.sub(r'\s+',' ',xlr_query)), queries.append(re.sub(r'\s+',' ',xld_query))
	queries.append(re.sub(r'\s+',' ',xldn_query))
	# Create the info worksheet
	overview_info = overview(db, queries)
	output_to_xlsx(overview_info, "Info")
	workbook.close()
	


# global stuff
args = parser.parse_args()
workbook = xlsxwriter.Workbook(args.output_name)
columns = 	" --columns \"chrom, start, end, codon_change, aa_change, type, vep_hgvsc, vep_hgvsp, gene, \
			clinvar_gene_phenotype, impact, clinvar_sig, impact_severity, vep_pubmed, vep_phenotypes, \
			pfam_domain, max_aaf_all, gerp_bp_score, cadd_scaled, aaf_1kg_all, aaf_exac_all, \
			exac_num_hom_alt, exac_num_het, geno2mp_hpo_ct, polyphen_score, sift_pred, sift_score, \
			vep_maxEntScan, vep_grantham, variant_id, (gts).(*), (gt_ref_depths).(*), (gt_alt_depths).(*) \" "

# run it!
main()
