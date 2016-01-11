import urllib, urllib2
import xmltodict
from operator import itemgetter

class PDBinfoGetter:
    def __init__(self, query):
        self.query = query

    def get_pdb_query(self):
        queryText = """
<?xml version="1.0" encoding="UTF-8"?>
<orgPdbQuery>
<version>B0907</version>
<queryType>org.pdb.query.simple.MoleculeNameQuery</queryType>
<macromoleculeName>
    """
        queryText += self.query
        queryText += """
</macromoleculeName>
</orgPdbQuery>
        """
        return queryText

    def get_pdb_ids(self):
        url = 'http://www.rcsb.org/pdb/rest/search'
        queryText = self.get_pdb_query()
        req = urllib2.Request(url, data=queryText)
        f = urllib2.urlopen(req)
        result = f.readlines()
        return result

    def clean_pdb_list(self, result):
        clean_result = []
        for entry in result:
            pdb_id = entry.strip().split(':')[0]
            clean_result.append(pdb_id)
        return clean_result

    def get_multiple_pdb_entry_input(self, clean_result):
        result = ""
        for pdb_code in clean_result[:-1]:
            result += pdb_code
            result += ","
        result += clean_result[-1]
        return result

    def url_for_mol_data_from_pdb(self, pdb_code):
        url = 'http://www.rcsb.org/pdb/rest/describeMol?structureId=' + pdb_code
        return url

    def url_for_pdb_data_from_pdb(self, pdb_code):
        url = 'http://www.rcsb.org/pdb/rest/getEntityInfo?structureId=' + pdb_code
        return url

    def get_data_from_pdb(self, pdb_code, pdb_data=False, mol_data=False):
        # Step 1: ask the pdb for the organism, chain, macromolecule_name, uniprot id
        if pdb_data == True:
            url = self.url_for_pdb_data_from_pdb(pdb_code)
        elif mol_data == True:
            url = self.url_for_mol_data_from_pdb(pdb_code)
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        the_page = response.read()
        data = xmltodict.parse(the_page)
        return data

    def get_res_from_pdb_xml(self, data):
        # Return resolution if available
        try:
            resolution = data['@resolution']
        except KeyError:
            resolution = None
        return resolution

    def get_method_from_pdb_xml(self, data):
        # Return experiment if available 
        try:
            if isinstance(data['Method'], dict):
                method = data['Method']['@name']
            elif isinstance(data['Method'], list):
                methods = []
                for i in range(len(data['Method'])):
                    methods.append(data['Method'][i]['@name'])
                method = tuple(methods)
        except KeyError:
            method = None
        return method

    def get_info_from_pdb_xml(self, data):
        resolution = self.get_res_from_pdb_xml(data)
        method = self.get_method_from_pdb_xml(data)
        return method, resolution

    def rank_by_resolution(self, res_map):
        ranked_map = []
        for pdb_code in res_map:
            if res_map[pdb_code]['resolution']:
                ranked_map.append((pdb_code, float(res_map[pdb_code]['resolution'])))
        sorted_ranked_map = sorted(ranked_map, key=itemgetter(1))
        return sorted_ranked_map

    def assign_ranking(self, ranked_map):
        structure_resolution = set([])
        for item in ranked_map:
            structure_resolution.add(item[1])
        sorted_structure_resolution = sorted(list(structure_resolution))
        ranks = {}
        for struct in ranked_map:
            data = list(struct)
            for j in range(len(sorted_structure_resolution)):
                if data[1] == sorted_structure_resolution[j]:
                    ranks[data[0]] = j + 1
        return ranks

    def assign_variables(self, polymer):
        chains = polymer['chain']
        if isinstance(chains, list):
            for j in range(len(chains)): 
                chain = chains[j]['@id']
        elif isinstance(chains, dict):
            chain = chains['@id']
        try:
            organism = polymer['Taxonomy']['@name']
            macromolecule_name = polymer['macroMolecule']['@name']
            uniprot_id = polymer['macroMolecule']['accession']['@id']
            #get_data_from_uniprot(uniprot_id)
        except KeyError:
            organism = None
            macromolecule_name = None
            uniprot_id = None
        return str(organism), str(chain), str(macromolecule_name), str(uniprot_id)


    def parse_mol_xml(self, data):
        polymers = data['polymer']
        if isinstance(polymers, list):
            for polymer in polymers:
                organism, chain, macromolecule_name, uniprot_id = self.assign_variables(polymer)   
        elif isinstance(polymers, dict):
            polymer = polymers
            organism, chain, macromolecule_name, uniprot_id = self.assign_variables(polymer)
        return organism, chain, macromolecule_name, uniprot_id

    def get_data_from_uniprot(self, uniprot_id):
        url = 'http://www.uniprot.org/mapping/'
        params = {
            'from' : 'GENENAME',
            'to' : 'P_REFSEQ_AC', # 'to' : 'ID'
            'format' : 'tab',
            'query' : uniprot_id
        }
        data = urllib.urlencode(params)
        request = urllib2.Request(url, data)
        contact = "andrea.edwards@colorado.edu"
        request.add_header('User-Agent', 'Python %s' % contact)
        response = urllib2.urlopen(request)
        page = response.readlines()
        uniprot_map = {}
        for line in page[1:]:
            tokens = line.strip('\n').split('\t')
            uniprot_map[tokens[0]] = tokens[1]
        return uniprot_map[uniprot_id]
        
    def main(self):
        result = self.get_pdb_ids()
        print "number of PDBs returned:", len(result)
        clean_result = self.clean_pdb_list(result)
        result = self.get_multiple_pdb_entry_input(clean_result)
        pdb_map = {}
        pdb_data = self.get_data_from_pdb(result, pdb_data=True)
        mol_data = self.get_data_from_pdb(result, mol_data=True)
        for pdb_code in pdb_data['entityInfo']['PDB']:
            method, resolution = self.get_info_from_pdb_xml(pdb_code)
            pdb_map[pdb_code['@structureId']] = {
            'resolution' : resolution,
            'method' : method
            }
        data_list = mol_data['molDescription']['structureId']
        for i in range(len(data_list)):
            organism, chain, macromolecule_name, uniprot_id = self.parse_mol_xml(data_list[i])
            #gene_name = get_data_from_uniprot(uniprot_id)
            pdb_map[data_list[i]['@id']]['organism'] = organism
            pdb_map[data_list[i]['@id']]['chain'] = chain
            pdb_map[data_list[i]['@id']]['macromolecule_name'] = macromolecule_name
            pdb_map[data_list[i]['@id']]['uniprot_id'] = uniprot_id
        resolution_map = self.rank_by_resolution(pdb_map)
        rank_map = self.assign_ranking(resolution_map)
        for pdb_code in rank_map:
            pdb_map[pdb_code]['rank'] = rank_map[pdb_code]        
        return pdb_map





