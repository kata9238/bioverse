import os
import urllib2
import subprocess
from Bio import SeqIO
from Bio.PDB import PDBParser, MMCIFParser
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from util import FileHandlers
from prody import fetchPDBviaFTP, parsePDB, writePDB
import numpy
from operator import itemgetter
import matplotlib.pyplot as plt
import itertools
import amino_acids
import settings

# Constants
ORG_SCI_NAME = '_entity_src_gen.pdbx_host_org_scientific_name'
GENE_SCI_NAME = '_entity_src_gen.pdbx_gene_src_scientific_name'
NAT_ORG_SCI_NAME = '_entity_src_nat.pdbx_organism_scientific'
STRAND_ID = '_struct_ref_seq.pdbx_strand_id'


class PDBFromUniprot:
    def __init__(self):
        self.pdb_dir = os.getcwd() + '/bioverse/static/results/'

    def fetch_pdb(self, pdb_code):
        if self._isempty_pdb(pdb_code):
            fetchPDBviaFTP(pdb_code, format='pdb', folder=self.pdb_dir)
            self._rename_pdb_file(pdb_code)

    def _isempty_pdb(self, pdb_code):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        pdb_files = file_handlers.find_files(file_paths, 'pdb')
        file_names = []
        for pdb_file in pdb_files:
            file_names.append(
                file_handlers.get_file_name(pdb_file).split('.')[0])
        return pdb_code.upper() not in file_names

    def get_pdb_id(self, queryText):
        url = 'http://www.rcsb.org/pdb/rest/search'
        print "querying PDB..."
        req = urllib2.Request(url, data=queryText)
        f = urllib2.urlopen(req)
        result = f.readlines()
        if result:
            PDB_codes = []
            print "Found number of PDB entries: %d" % len(result)
            for pdb_code in result:
                PDB_codes.append(pdb_code.strip())
            return PDB_codes
        else:
            print "Failed to retrieve results"
            PDB_codes = []
            return PDB_codes

    def _get_downloaded_file_path(self, pdb_code, prody=False):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        if not prody:
            ent_files = file_handlers.find_files(file_paths, 'ent')
            for ent_file in ent_files:
                name = file_handlers.get_file_name(ent_file)
                name = name.split('.')[0].lstrip('pdb').upper()
                if pdb_code == name:
                    return ent_file
        else:
            pdb_files = file_handlers.find_files(file_paths, 'pdb')
            for pdb_file in pdb_files:
                if pdb_code.lower() == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    return pdb_file

    def _unzip_file(self, pdb_code):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        zip_files = file_handlers.find_files(file_paths, 'gz')
        for zip_file in zip_files:
            z = file_handlers.get_file_name(zip_file).split('.')[0].upper()
            if pdb_code == z:
                cmd = ['gunzip -d ' + zip_file]
                subprocess.call(cmd, shell=True)

    def _rename_pdb_file(self, pdb_code):
        self._unzip_file(pdb_code)
        pdb_file = self._get_downloaded_file_path(pdb_code, prody=True)
        split_path = pdb_file.split('/')
        name = split_path[-1].split('.')
        new_name = name[0].lstrip('pdb').upper() + '.pdb'
        split_path[-1] = new_name
        new_path = '/'.join(split_path)
        os.rename(pdb_file, new_path)


class CIFFromUniprot:
    def __init__(self, pdb_code):
        self.pdb_dir = os.getcwd() + '/results/'
        self.filename = pdb_code
        self.zipped_filepath = self.pdb_dir + '/' + pdb_code + '.cif.gz'

    def _isempty_mmCIF(self):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        cif_files = file_handlers.find_files(file_paths, 'cif')
        file_names = []
        for cif_file in cif_files:
            file_names.append(
                file_handlers.get_file_name(cif_file).split('.')[0])
        return True if self.filename not in file_names else False

    def _get_mmCIF(self):
        fetchPDBviaFTP(self.filename, format='cif', folder=self.pdb_dir)

    def _unzip_mmCIF(self):
        cmd = ['gunzip -d ' + self.zipped_filepath]
        subprocess.call(cmd, shell=True)

    def _rename_mmCIF_file(self):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        cif_files = file_handlers.find_files(file_paths, 'cif')
        for cif_file in cif_files:
            f = file_handlers.get_file_name(cif_file).split('.')[0].upper()
            if self.filename == f:
                print "Downloaded cif file for %s" % self.filename

    def fetch_mmCIF(self):
        if self._isempty_mmCIF():
            self._get_mmCIF()
            self._unzip_mmCIF()
            self._rename_mmCIF_file()


class CIFFParser:
    def __init__(self, pdb_code):
        self.filename = pdb_code
        self.filtered_pdb_genes = []
        self.chains = []
        self.genes = []
        self.organisms = []
        self.pdb_sequences = []

    def _write_cif_dict(self, mmcif_dict):
        outfile = os.getcwd() + '/results/' + self.filename + '_mmCIFDict'
        output = open(outfile, 'w')
        for key in mmcif_dict:
            if isinstance(mmcif_dict[key], str):
                output.write('key:\n' + key + '\n' + 'value:\n' +
                             mmcif_dict[key] + '\n')
            elif isinstance(mmcif_dict[key], list):
                output.write('key:\n' + key + '\n' + 'value:\n' +
                             ' '.join(mmcif_dict[key]) + '\n')
        output.close()

    def _is_real_gene(self, genes):
        genome = SeqIO.read('/Users/andrea/repositories/design_pipeline/main/'
                            'database/gb/NC_000913.3.gb', 'genbank')
        gene_list = []
        for feature in genome.features:
            for key, value in feature.qualifiers.iteritems():
                if key == 'gene':
                    gene_list.append(value[0].upper())
        if isinstance(genes, str):
            pdb_genes = []
            if len(genes.split('_')) > 1:
                Genes = genes.split('_')
                for gene in Genes:
                    pdb_genes.append(gene.upper())
            elif len(genes.split(',')) > 1:
                Genes = genes.split(',')
                for gene in Genes:
                    pdb_genes.append(gene.upper().strip())
            elif len(genes.split(' ')) > 1:
                Genes = genes.split(' ')
                for gene in Genes:
                    pdb_genes.append(gene.upper().strip())
            else:
                pdb_genes = [genes.upper()]
        elif isinstance(genes, list):
            pdb_genes = []
            for gene in genes:
                if len(gene.split('_')) > 1:
                    pdb_genes.append(gene.split('_')[0].upper())
                elif len(gene.split(',')) > 1:
                    split_gene = [gene.upper().strip()
                                  for gene in gene.split(',')]
                    for item in split_gene:
                        pdb_genes.append(item)
                else:
                    pdb_genes.append(gene.upper())
        filtered_pdb_genes = []
        for gene in pdb_genes:
            if gene in gene_list:
                filtered_pdb_genes.append(gene)
        if filtered_pdb_genes != []:
            self.filtered_pdb_genes = filtered_pdb_genes
            return set(filtered_pdb_genes).issubset(set(gene_list))
        else:
            return False

    def _get_publication_info(self, mmcif_dict):
        if '_citation.title' in mmcif_dict:
            title = mmcif_dict['_citation.title']
        if '_citation_author.name' in mmcif_dict:
            authors = mmcif_dict['_citation_author.name']
        return title, authors

    def get_gene_info_from_genbank(self):
        gene_info = {}
        genome = SeqIO.read('/Users/andrea/repositories/design_pipeline/main/'
                            'database/gb/NC_000913.3.gb', 'genbank')
        for short_gene_name in self.filtered_pdb_genes:
            for feature in genome.features:
                if feature.type == 'CDS' and short_gene_name in \
                        [gene.upper() for gene in feature.qualifiers['gene']]:
                    gene_info[short_gene_name] = {}
                    try:
                        if 'gene' in feature.qualifiers:
                            gene_info[short_gene_name]['GENE'] = \
                                feature.qualifiers['gene']
                        else:
                            gene_info[short_gene_name]['GENE'] = ''
                    except Exception:
                        pass
                    try:
                        if 'product' in feature.qualifiers:
                            gene_info[short_gene_name]['PRODUCT'] = \
                                feature.qualifiers['product']
                        else:
                            gene_info[short_gene_name]['PRODUCT'] = ''
                    except Exception:
                        pass
                    try:
                        if 'function' in feature.qualifiers:
                            gene_info[short_gene_name]['FUNCTION'] = \
                                feature.qualifiers['function']
                        else:
                            gene_info[short_gene_name]['FUNCTION'] = ''
                    except Exception:
                        pass
                    try:
                        if 'protein_id' in feature.qualifiers:
                            gene_info[short_gene_name]['PROTEIN_ID'] = \
                                feature.qualifiers['protein_id']
                        else:
                            gene_info[short_gene_name]['PROTEIN_ID'] = ''
                    except Exception:
                        pass
        return gene_info

    def _open_file(self, filepath):
        Data = open(filepath, 'r')
        data = Data.readlines()
        Data.close()
        os.remove(filepath)
        return data

    def _get_sequence_from_structure(self, genes, chains):
        sequences = []
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        pdb_files = file_handlers.find_files(file_paths, 'pdb')
        for pdb_file in pdb_files:
            if self.filename == \
                    file_handlers.get_file_name(pdb_file).split('.')[0]:
                for gene, chain in zip(genes, chains):
                    cmd = ['python ~/repositories/bioverse_beta/bioverse/src/'
                           'get_fasta_from_pdb.py ' + pdb_file + ' ' + chain +
                           ' ' + (gene + '_' + self.filename + '_chain-' +
                                  chain + '.fasta')]
                    subprocess.call(cmd, shell=True)
                    filepath = (os.getcwd() + '/' + gene + '_' +
                                self.filename + '_chain-' + chain + '.fasta')
                    data = self._open_file(filepath)
                    sequences.append(data[1].strip())
        return sequences

    def _get_genes(self, mmcif_dict):
        if '_entity_src_gen.pdbx_gene_src_gene' in mmcif_dict and \
                self._is_real_gene(mmcif_dict[
                    '_entity_src_gen.pdbx_gene_src_gene']):
            genes = self.filtered_pdb_genes
        elif '_struct_ref.db_code' in mmcif_dict and \
                self._is_real_gene(mmcif_dict['_struct_ref.db_code']):
            genes = self.filtered_pdb_genes
        elif '_entity_name_com.name' in mmcif_dict and \
                self._is_real_gene(mmcif_dict['_entity_name_com.name']):
            genes = self.filtered_pdb_genes
        elif '_entity.pdbx_description' in mmcif_dict and \
                self._is_real_gene(mmcif_dict['_entity.pdbx_description']):
            genes = self.filtered_pdb_genes
        else:
            print 'cannot determine gene names from cif file'
        return genes

    def _get_organisms(self, mmcif_dict):
        organisms = None
        for i in range(3):
            if i == 0:
                if ORG_SCI_NAME in mmcif_dict:
                    if isinstance(mmcif_dict[ORG_SCI_NAME], str):
                        empty = set(['?'])
                        if not set([mmcif_dict[ORG_SCI_NAME]]).issubset(empty):
                            organisms = [mmcif_dict[ORG_SCI_NAME]]
                        else:
                            organisms = None
                    else:
                        empty = set(['?'])
                        if not set(mmcif_dict[ORG_SCI_NAME]).issubset(empty):
                            organisms = mmcif_dict[ORG_SCI_NAME]
                        else:
                            None
                else:
                    pass
            elif i == 1 and organisms is None:
                if GENE_SCI_NAME in mmcif_dict:
                    if isinstance(mmcif_dict[GENE_SCI_NAME], str):
                        empty = set(['?'])
                        if not set(
                                [mmcif_dict[GENE_SCI_NAME]]).issubset(empty):
                            organisms = [mmcif_dict[GENE_SCI_NAME]]
                        else:
                            organisms = None
                    else:
                        empty = set(['?'])
                        if not set(mmcif_dict[GENE_SCI_NAME]).issubset(empty):
                            organisms = mmcif_dict[GENE_SCI_NAME]
                        else:
                            organisms = None
                else:
                    pass
            elif i == 2 and organisms is None:
                if NAT_ORG_SCI_NAME in mmcif_dict:
                    if isinstance(mmcif_dict[NAT_ORG_SCI_NAME], str):
                        empty = set(['?'])
                        if not set([mmcif_dict[NAT_ORG_SCI_NAME]]).issubset(
                                empty):
                            organisms = [mmcif_dict[NAT_ORG_SCI_NAME]]
                        else:
                            organisms = None
                    else:
                        empty = set(['?'])
                        if not set(mmcif_dict[NAT_ORG_SCI_NAME]).issubset(
                                empty):
                            organisms = mmcif_dict[NAT_ORG_SCI_NAME]
                        else:
                            organisms = None
                else:
                    pass
        return organisms

    def _get_chains(self, mmcif_dict, genes):
        if isinstance(mmcif_dict[STRAND_ID], list):
            chains = mmcif_dict[STRAND_ID][:len(genes)]
        else:
            chains = [mmcif_dict[STRAND_ID]]
        return chains

    def get_gene_annotations(self):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        cif_files = file_handlers.find_files(file_paths, 'cif')
        for cif_file in cif_files:
            if self.filename == \
                    file_handlers.get_file_name(cif_file).split('.')[0]:
                MMCIFParser()
                mmcif_dict = MMCIF2Dict(cif_file)
                self._write_cif_dict(mmcif_dict)  # for debugging
                genes = self._get_genes(mmcif_dict)
                organisms = self._get_organisms(mmcif_dict)
                chains = self._get_chains(mmcif_dict, genes)
                pdb_sequences = self._get_sequence_from_structure(genes,
                                                                  chains)
                title, authors = self._get_publication_info(mmcif_dict)
        self.chains = chains
        self.genes = genes
        self.organisms = organisms
        self.pdb_sequences = pdb_sequences
        return chains, genes, organisms, pdb_sequences, title, authors

    def collate_sequence_annotations(self):
        sequence_annotations = []
        for chain, gene, organism, pdb_sequence in zip(
                self.chains, self.genes, self.organisms, self.pdb_sequences):
            sequence_annotations.append([chain, gene, organism, pdb_sequence])
        return sequence_annotations

    def write_fasta(self, sequence_annotations):
        for i in range(len(sequence_annotations)):
            sequence_id = sequence_annotations[i][1] + '_' + self.filename + \
                          '_chain-' + sequence_annotations[i][0]
            outfile = os.getcwd() + '/' + sequence_id + '.fasta'
            output = open(outfile, 'w')
            output.write('>' + sequence_id + '\n' +
                         sequence_annotations[i][3] + '\n')
            output.close()


class HeaderParser:
    def __init__(self, pdb_code):
        self.filename = pdb_code

    def get_header_dict(self):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        pdb_files = file_handlers.find_files(file_paths, 'pdb')
        for pdb_file in pdb_files:
            if self.filename == \
                    file_handlers.get_file_name(pdb_file).split('.')[0]:
                atoms, header = parsePDB(pdb_file, header=True)
        return header


class PDBPreProcessor:
    # Preprocessor performs several key steps required before picking target
    # mutation sites
    # 1. Parse header using ProDy to find how many molecules are in the
    # asymmetric unit and which chains belong to which component of the
    # asymmetric unit
    # 2. Clean pdb using Rosetta's python script 'clean_pdb.py' as->
    # clean_pdb.py code.pdb AB where 'AB' are the chains discovered in the
    # previous step
    # 3. The previous step also outputs a fasta file for each chain that will
    # be used later in the pipeline for matching sequence changes to the
    # correct residue numbering of the genomic variant
    # 4. Minimizes the cleaned pdb file using the Rosetta Minimizer. The
    # resulting file (appended with '_0001.pdb') will be used for all target
    # picking steps

    # There is a problem here. clean_pdb.py removes hetatms. These hetatms need
    # to remain in place for the LigandBinidngSite to work. Use pdb_renumber.py
    # --preserve input.pdb output.pdb for LigandBindingSite

    def __init__(self, pdb_code):
        self.filename = pdb_code
        self.file_path = ''
        self.chains = ''

    def _get_file_path(self, cleaned=False, minimized=False,
                       test_minimized=False, mmCIF=False):
        self.file_path = ''
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        if mmCIF:
            cif_files = file_handlers.find_files(file_paths, 'cif')
            for cif_file in cif_files:
                if self.filename == \
                        file_handlers.get_file_name(cif_file).split('.')[0]:
                    self.file_path = cif_file
        else:
            pdb_files = file_handlers.find_files(file_paths, 'pdb')
            if cleaned:
                for pdb_file in pdb_files:
                    if (self.filename + '_' + self.chains) == \
                            file_handlers.get_file_name(
                                pdb_file).split('.')[0]:
                        self.file_path = pdb_file
            elif minimized:
                for pdb_file in pdb_files:
                    if (self.filename + '_' + self.chains + '_0001') == \
                            file_handlers.get_file_name(
                                pdb_file).split('.')[0]:
                        self.file_path = pdb_file
            elif test_minimized:
                for pdb_file in pdb_files:
                    if (self.filename + '_0001') == \
                            file_handlers.get_file_name(
                                pdb_file).split('.')[0]:
                        self.file_path = pdb_file
            else:
                for pdb_file in pdb_files:
                    if self.filename == \
                            file_handlers.get_file_name(
                                pdb_file).split('.')[0]:
                        self.file_path = pdb_file

    def count_structures_in_asymmetric_unit(self):
        header_parser = HeaderParser(self.filename)
        header = header_parser.get_header_dict()
        number_of_structures = len(header['biomoltrans'])
        self.chains = ''.join(header['biomoltrans']['1'][0])
        print ("There are %s structures in the asymmetric unit. Chains %s are "
               "suficient to represent the asymmetric unit." %
               (str(number_of_structures), self.chains))
        return number_of_structures, self.chains

    def get_experiment_type(self):
        header_parser = HeaderParser(self.filename)
        header = header_parser.get_header_dict()
        try:
            experiment = header['experiment'] if header['experiment'] \
                else None
        except Exception:
            try:
                experiment = header['EXPERIMENT'] if header['EXPERIMENT'] \
                    else None
            except Exception:
                experiment = 'undetermined'
        print "This model was built using an %s experiment" % experiment
        return experiment

    def get_diffraction_resolution(self):
        header_parser = HeaderParser(self.filename)
        header = header_parser.get_header_dict()
        try:
            resolution = header['resolution'] if header['resolution'] \
                else None
        except Exception:
            try:
                resolution = header['RESOLUTION'] if header['RESOLUTION'] \
                    else None
            except Exception:
                resolution = 'undetermined'
        print ("This model was determined to %s Angstrom "
               "resolution" % resolution)
        return resolution

    def _run_clean_pdb(self):
        self._get_file_path()
        cmd = ['python ~/rosetta/tools/protein_tools/scripts/clean_pdb.py ' +
               self.file_path + ' ' + self.chains]
        subprocess.call(cmd, shell=True)

    def _run_rosetta_minimizer(self):
        self._get_file_path(cleaned=True)
        print self.file_path
        cmd = ['~/rosetta/main/source/bin/minimize.static.macosclangrelease '
               '-jd2 -s ' + self.file_path + ' -ignore_unrecognized_res']
        subprocess.call(cmd, shell=True)

    def _rename_minimized_structure(self):
        self._get_file_path(minimized=True)
        file_handlers = FileHandlers()
        source_filename = file_handlers.get_file_name(
            self.file_path).split('.')[0]
        source_list = source_filename.split('_')
        destination = '_'.join([source_list[0], source_list[2]])
        os.rename(self.file_path, (os.getcwd() + '/' + destination + '.pdb'))

    def _is_clean(self):
        self._get_file_path(cleaned=True)
        if self.file_path == '':
            return False
        else:
            return True

    def _is_minimized(self):
        self._get_file_path(test_minimized=True)
        return self.file_path != ''

    def process(self):
        number_of_structures, self.chains = \
            self.count_structures_in_asymmetric_unit()
        if not self._is_clean():
            self._run_clean_pdb()
        if not self._is_minimized():
            self._run_rosetta_minimizer()
            self._rename_minimized_structure()
        return number_of_structures

    def _is_pdb_downloaded(self):
        self._get_file_path()
        return self.file_path != ''

    def _is_mmcif_downloaded(self):
        self._get_file_path(mmCIF=True)
        return self.file_path != ''

    def preprocess_check(self):
        if not self._is_pdb_downloaded():
            pdb_getter = PDBFromUniprot()
            pdb_getter.fetch_pdb(self.filename)
        if not self._is_mmcif_downloaded():
            cif_getter = CIFFromUniprot(self.filename)
            cif_getter.fetch_mmCIF()


class LigandBindingSite:
    def __init__(self, pdb_code, chains):
        print "\n\n\nSearching for ligand binding sites...."
        self.filename = pdb_code
        self.chains = chains
        self.file_path = ''
        self.out_filename = ''
        self.ligand_centroid = []
        self.ligands = []
        self.ligand_binding_pocket = []
        self.ignore = ['MN ', 'DOD', 'SO4', 'HOH']
        self.ligand_chain = []
        self.all_ligand_atoms = []
        self.pdb_dir = os.getcwd() + '/results/'

    def _get_file_path(self, ligand=False, pdb=False):
        self.file_path = ''
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        pdb_files = file_handlers.find_files(file_paths, 'pdb')
        if ligand:
            for pdb_file in pdb_files:
                if self.filename == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    self.file_path = pdb_file
        elif pdb:
            for pdb_file in pdb_files:
                if (self.filename) == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    self.file_path = pdb_file

    def _find_ligand(self):
        self._get_file_path(ligand=True)
        protein = parsePDB(self.file_path)
        ligand = protein.select('not protein and not water')
        if ligand:
            self.out_filename = self.file_path.split('.')[0] + '_ligand.pdb'
            writePDB(self.out_filename, ligand)

    def _get_ligand_coordinates(self):
        self._find_ligand()
        p = PDBParser(QUIET=True)
        if self.out_filename == '':
            pass
        else:
            structure = p.get_structure('ligand', self.out_filename)
            atom_pos_array = []
            for Chain in structure.get_chains():
                print "Looking for ligands on chain %s" % Chain.id
                try:
                    chain = structure[0][Chain.id]
                    if chain:
                        print "Found ligand on chain %s" % chain.id
                        for residue in chain.get_residues():
                            if residue.resname not in self.ignore:
                                print "Found ligand: %s" % residue.resname
                                for atom in residue:
                                    min_array = [atom.get_coord()[0],
                                                 atom.get_coord()[1],
                                                 atom.get_coord()[2]]
                                    atom_pos_array.append(min_array)
                                self.ligand_centroid.append(
                                    numpy.mean(atom_pos_array, axis=0))
                                self.all_ligand_atoms = atom_pos_array
                except KeyError:
                    pass

    def _get_ligand_name(self):
        p = PDBParser(QUIET=True)
        ligand = p.get_structure('ligand', self.out_filename)
        for chain in ligand.get_chains():
            try:
                chain = ligand[0][chain.id]
                for residue in chain.get_residues():
                    if residue.resname in self.ignore:
                        pass
                    else:
                        self.ligands.append(residue.resname)
                        self.ligand_chain.append(chain.id)
                print "Ligands found: ", self.ligands
                return self.ligands
            except KeyError:
                pass

    def get_residues_within_5A(self, centroid='False'):
        self._get_ligand_coordinates()
        if self.ligand_centroid == []:
            print '\nNo ligand bound to %s' % self.filename
        else:
            self._get_ligand_name()
            self._get_file_path(pdb=True)
            p = PDBParser(QUIET=True)
            structure = p.get_structure('protein', self.file_path)
            ligand_binding_pocket = []
            for chain in structure.get_chains():
                print ("looking for ligand binding pocket on "
                       "chain %s" % chain.id)
                try:
                    chain = structure[0][chain.id]
                    for residue in chain.get_residues():
                        for atom in residue:
                            if residue.resname in self.ligands or \
                                    (' ' + residue.resname.rstrip()) in \
                                    self.ligands or \
                                    (residue.resname.lstrip() + ' ') in \
                                    self.ligands:
                                pass
                            elif residue.resname in self.ignore or \
                                    (' ' + residue.resname.rstrip()) in \
                                    self.ignore or \
                                    (residue.resname.lstrip() + ' ') in \
                                    self.ignore:
                                pass
                            else:
                                if centroid == 'True':
                                    for centroid in self.ligand_centroid:
                                        if abs(float(atom.get_coord()[0]) -
                                               float(centroid[0])) <= 5 and \
                                           abs(float(atom.get_coord()[1]) -
                                               float(centroid[1])) <= 5 and \
                                           abs(float(atom.get_coord()[2]) -
                                               float(centroid[2])) <= 5:
                                            ligand_binding_pocket.append(
                                                str(residue.resname) + '\t' +
                                                chain.id + '\t' +
                                                str(residue.id[1]))

                                else:
                                    for coordinate in self.all_ligand_atoms:
                                        if abs(float(atom.get_coord()[0]) -
                                               float(coordinate[0])) <= 5 and \
                                           abs(float(atom.get_coord()[1]) -
                                               float(coordinate[1])) <= 5 and \
                                           abs(float(atom.get_coord()[2]) -
                                               float(coordinate[2])) <= 5:
                                            ligand_binding_pocket.append(
                                                str(residue.resname) + '\t' +
                                                chain.id + '\t' +
                                                str(residue.id[1]))
                    self.ligand_binding_pocket = set(ligand_binding_pocket)
                    print ("Residues in ligand binding pocket: ",
                           [line.split('\t')
                            for line in self.ligand_binding_pocket])
                except KeyError:
                    print ('No ligand found in chain '
                           '%s of %s' % (chain, self.filename))
            return self.ligand_binding_pocket

    def write_residue_output(self):
        active_site_filename = self.pdb_dir + '/' + self.filename + \
            '_lpocket.txt'
        output_residues = open(active_site_filename, 'w')
        for line in self.ligand_binding_pocket:
            output_residues.write(line + '\t' + str(100.00) + '\n')
        output_residues.close()


class Rosetta:
    def __init__(self, pdb_code):
        self.filename = pdb_code
        self.pdb = []

    def _get_pdb(self, rosetta_min=False, refined_pocket=False):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        pdb_files = file_handlers.find_files(file_paths, 'pdb')
        for pdb_file in pdb_files:
            if rosetta_min and refined_pocket:
                print "Invalid input"
            elif rosetta_min:
                if (self.filename + '_0001') == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    print ("\n\n\nUsing Rosetta minimized structure %s for "
                           "locating "
                           "pockets." % file_handlers.get_file_name(pdb_file))
                    filepath = pdb_file
            elif refined_pocket:
                if ('pocket0') == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    print "Done locating pocket in ", self.filename
                    filepath = pdb_file
            else:
                if self.filename == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    print ("Found target structure file ",
                           (self.filename + '.pdb'))
                    filepath = pdb_file
        return filepath

    def _open_file(self, filepath):
        Data = open(filepath, 'r')
        data = Data.readlines()
        Data.close()
        os.remove(filepath)
        return data

    def _get_data(self, file_tag):
        data = []
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        txt_files = file_handlers.find_files(file_paths, 'txt')
        for txt_file in txt_files:
            if self.filename == \
                    file_handlers.get_file_name(txt_file).split('_')[0]:
                if file_tag.split('_')[1] + '.txt' == \
                        file_handlers.get_file_name(txt_file).split('_')[1]:
                    TXT = open(txt_file)
                    data = TXT.readlines()
                    TXT.close()
        return data

    def _get_surface_residues(self, file_tag):
        data = self._get_data(file_tag)
        residues = []
        for line in data:
            split_list = line.split('\t')
            residue_name = split_list[0].strip()
            residue_chain = split_list[1].strip()
            residue_number = split_list[2].strip()
            residues.append((residue_name, residue_chain, residue_number))
        return residues

    def _get_output(self):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        out_files = file_handlers.find_files(file_paths, 'out')
        for out_file in out_files:
            if 'pocket_score' == \
                    file_handlers.get_file_name(out_file).split('.')[0]:
                TXT = open(out_file)
                data = TXT.readlines()
                TXT.close()
        return data

    def _get_score(self):
        data = self._get_output()
        score = float(data[-1].split(' ')[-1].strip())
        return score

    def _get_resnums(self, filtered_data):
        residues = []
        for data in filtered_data:
            residues.append(data[0])
        return residues

    def _write_scores(self, data, handle):
        # data is a list of tuples. the format for items in this list is
        # ( (name, chain, number), score )
        out_file = os.getcwd() + '/' + self.filename + handle
        out = open(out_file, 'w')
        for tuple_element in data:
            residue_tuple = tuple_element[0]
            residue_name = residue_tuple[0]
            residue_chain = residue_tuple[1]
            residue_number = residue_tuple[2]
            out.write(residue_name + '\t' + residue_chain + '\t' +
                      residue_number + '\t' + str(tuple_element[1]) + '\n')
        out.close()

    def _write_pocket_residues(self, handle):
        out_file = os.getcwd() + '/' + self.filename + handle
        out = open(out_file, 'w')
        # dictionary with ==> ('name', 'chain', 'position') : '100.00'
        pocket_residues = self._get_pocket_residues()
        for residue in pocket_residues:
            out.write(residue[0] + '\t' + residue[1] + '\t' + residue[2] +
                      '\t' + pocket_residues[residue] + '\n')
        out.close()

    def _plot_data(self, data):
        x = []
        y = []
        for d in data:
            x.append(d[0])
            y.append(d[1])
        plt.scatter(x, y)
        plt.show()

    def _sort_scores(self, data, plt=False):
        sorted_data = sorted(data, key=itemgetter(1))
        if plt:
            self._plot_data(sorted_data)
        return sorted_data

    def _pocket_finder(self, filepath, residue_tuple_list, output=False):
        if len(residue_tuple_list) == 1 and not output:
            chain = residue_tuple_list[0][1]
            residue_number = str(residue_tuple_list[0][2])
            cmd = ['~/rosetta/main/source/bin/'
                   'pocket_measure.static.macosclangrelease -s ' + filepath +
                   ' -central_relax_pdb_num ' + residue_number + ':' + chain +
                   ' -pocket_num_angles 100 | grep Largest >> '
                   'pocket_score.out']
            subprocess.call(cmd, shell=True)
        elif len(residue_tuple_list) == 1 and output:
            chain = residue_tuple_list[0][1]
            residue_number = str(residue_tuple_list[0][2])
            cmd = ['~/rosetta/main/source/bin/'
                   'pocket_measure.static.macosclangrelease -s ' + filepath +
                   ' -central_relax_pdb_num ' + residue_number + ':' + chain +
                   ' -pocket_dump_pdbs -pocket_num_angles 100 '
                   '| grep Largest >> pocket_score.out']
            subprocess.call(cmd, shell=True)
        elif len(residue_tuple_list) == 2 and not output:
            chain1 = residue_tuple_list[0][1]
            residue_number1 = str(residue_tuple_list[0][2])
            chain2 = residue_tuple_list[1][1]
            residue_number2 = str(residue_tuple_list[1][2])
            cmd = ['~/rosetta/main/source/bin/'
                   'pocket_measure.static.macosclangrelease -s ' + filepath +
                   ' -central_relax_pdb_num ' + residue_number1 + ':' +
                   chain1 + ',' + residue_number2 + ':' + chain2 +
                   ' -pocket_num_angles 100 | grep Largest >> '
                   'pocket_score.out']
            subprocess.call(cmd, shell=True)
        elif len(residue_tuple_list) == 2 and output:
            chain1 = residue_tuple_list[0][1]
            residue_number1 = str(residue_tuple_list[0][2])
            chain2 = residue_tuple_list[1][1]
            residue_number2 = str(residue_tuple_list[1][2])
            cmd = ['~/rosetta/main/source/bin/'
                   'pocket_measure.static.macosclangrelease -s ' + filepath +
                   ' -central_relax_pdb_num ' + residue_number1 + ':' +
                   chain1 + ',' + residue_number2 + ':' + chain2 +
                   ' -pocket_dump_pdbs -pocket_num_angles 100 | '
                   'grep Largest >> pocket_score.out']
            subprocess.call(cmd, shell=True)
        else:
            print "invalid input"

    def _is_standard_res(self, filepath, residue_tuple):
        p = PDBParser(QUIET=True)
        structure = p.get_structure('protein', filepath)
        for Chain in structure.get_chains():
            if Chain.id == residue_tuple[1]:
                chain = structure[0][Chain.id]
                for residue in chain.get_residues():
                    if str(residue.id[1]) == residue_tuple[2]:
                        return residue.resname in settings.AA_CODES

    def _scan_surface(self):
        data = []
        filepath = self._get_pdb(rosetta_min=True)
        residues = self._get_surface_residues("_SurfRes")
        print 'Scanning surface for pockets...'
        for residue_tuple in residues:
            if self._is_standard_res(filepath, residue_tuple):
                self._pocket_finder(filepath, [residue_tuple])
                score = self._get_score()
                print ('Residue number: %s Score: %s' %
                       (residue_tuple, str(score)))
                data.append((residue_tuple, score))
        self._write_scores(data, '_pocket_scores.out')
        # format for items in this list is ( (name, chain, number), score )
        return data

    def _refine_pockets(self, filtered_data):
        # filtered_data is a list of tuples. the format for items in this list
        # is ( (name, chain, number), score )
        print "filtered data: ", filtered_data
        print "Refining pocket location..."
        filepath = self._get_pdb(rosetta_min=True)
        residues = self._get_resnums(filtered_data)
        combos = itertools.combinations(residues, 2)
        results = []
        for combo in combos:
            res1, res2 = combo[0], combo[1]
            self._pocket_finder(filepath, list(combo))
            score = self._get_score()
            results.append((combo, score))
            print ('Residue pair: (%s, %s) Score: %s' %
                   (str(res1), str(res2), str(score)))
        sorted_results = self._sort_scores(results, plt=False)
        self._pocket_finder(filepath, list(sorted_results[-1][0]),
                            output=True)

    def _get_pocket_coordinates(self):
        pockets_filepath = self._get_pdb(refined_pocket=True)
        pockets = self._open_file(pockets_filepath)
        pocket_coordinates = []
        pocket_data = []
        for line in pockets:
            if line[13:16] == 'TPB':
                pocket_data.append(line)
                coordinates = (line[31:38], line[39:46], line[47:54])
                pocket_coordinates.append(coordinates)
        self._extract_pocket(pocket_data)
        return pocket_coordinates

    def _extract_pocket(self, pocket_data):
        out_file = os.getcwd() + '/' + self.filename + 'main_pocket.pdb'
        out = open(out_file, 'w')
        for line in pocket_data:
            out.write(line + '\n')
        out.close()

    def _get_pocket_residues(self):
        pocket_residues = {}
        pocket_coordinates = self._get_pocket_coordinates()
        protein_filepath = self._get_pdb(rosetta_min=True)
        p = PDBParser(QUIET=True)
        structure = p.get_structure('protein', protein_filepath)
        for Chain in structure.get_chains():
            chain = structure[0][Chain.id]
            for residue in chain.get_residues():
                if residue.id[0] == ' ' and residue.resname in \
                        settings.AA_CODES:
                    for atom in residue:
                        for coordinate in pocket_coordinates:
                            if abs(float(atom.get_coord()[0]) -
                                   float(coordinate[0])) <= 2.5 and \
                               abs(float(atom.get_coord()[1]) -
                                   float(coordinate[1])) <= 2.5 and \
                               abs(float(atom.get_coord()[2]) -
                                   float(coordinate[2])) <= 2.5:
                                pocket_residues[
                                    (residue.resname, Chain.id,
                                     str(residue.id[1]))] = str(100.00)
                else:
                    pass
        # dictionary with ==> ('name', 'chain', 'position') : '100.00'
        return pocket_residues

    def _set_filtered_pocket_scores(self, data_tuples, threshold=0.90,
                                    BestScore=False):
        # data_tuples will be a list. the items will have the format:
        # ( frac, ((name, chain, number), score) )
        filtered_data = []
        if not BestScore:
            for item in data_tuples:
                if item[0] >= threshold:
                    filtered_data.append(item[1])
            if len(filtered_data) <= 1 and threshold > 0:
                new_threshold = threshold - 0.1
                filtered_data = self._set_filtered_pocket_scores(
                    data_tuples, threshold=new_threshold)
            if filtered_data == []:
                print "Failed to find pocket"
            return filtered_data
        else:
            filtered_data.append(data_tuples[-1][1])
            # filtered_data is a list of tuples. the format for items in this
            # list is ( (name, chain, number), score)
            return filtered_data

    def find_pockets(self):
        # data is a list of tuples. the format for items in this list is
        # ( (name, chain, number), score )
        data = self._scan_surface()
        sorted_data = self._sort_scores(data, plt=False)
        highest_score = float(sorted_data[-1][1])
        lowest_score = float(sorted_data[0][1])
        data_tuples = []
        for data in sorted_data:
            frac = abs((lowest_score - float(data[1])) /
                       (highest_score - lowest_score))
            # data_tuples will be a list. the items will have the format:
            # ( frac, ((name, chain, number), score) )
            data_tuples.append((frac, data))
        filtered_data = self._set_filtered_pocket_scores(data_tuples)
        self._refine_pockets(filtered_data)

        self._write_scores(filtered_data, '_pockets.txt')
        self._write_pocket_residues('_pocketres.txt')


class MutantListMaker:
    def __init__(self, pdb_code):
        self.handles = []
        self.filename = pdb_code
        self.resnums = set([])
        self.codes = {'GLY': 'G', 'PRO': 'P', 'ALA': 'A', 'VAL': 'V',
                      'LEU': 'L', 'ILE': 'I', 'MET': 'M', 'CYS': 'C',
                      'PHE': 'F', 'TYR': 'Y', 'TRP': 'W', 'HIS': 'H',
                      'LYS': 'K', 'ARG': 'R', 'GLN': 'Q', 'ASN': 'N',
                      'GLU': 'E', 'ASP': 'D', 'SER': 'S', 'THR': 'T'}
        self.inverse_codes = {}
        for key in self.codes:
            self.inverse_codes[self.codes[key]] = key
        self.amino_acids = set([])
        for key in self.codes:
            self.amino_acids.add(self.codes[key])

    def _open_file(self, filepath):
        Data = open(filepath, 'r')
        data = Data.readlines()
        Data.close()
        return data

    def _get_filepath(self, handle, data_file=False, pdb_file=False):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        if data_file:
            files = file_handlers.find_files(file_paths, 'txt')
            for path in files:
                if (self.filename + handle) == \
                        file_handlers.get_file_name(path).split('.')[0]:
                    return path
        elif pdb_file:
            files = file_handlers.find_files(file_paths, 'pdb')
            for path in files:
                if (self.filename + '_0001') == \
                        file_handlers.get_file_name(path).split('.')[0]:
                    return path
        else:
            print "Specify file type"

    def _get_resnums(self):
        resnums = set([])
        for handle in self.handles:
            filepath = self._get_filepath(handle, data_file=True)
            data = self._open_file(filepath)
            for line in data:
                resnum = line.split('\t')[0]
                resnums.add(resnum)
        self.resnums = resnums
        return resnums

    def _get_resmapping(self):
        res_mapping = []
        filepath = self._get_filepath('', pdb_file=True)
        p = PDBParser(QUIET=True)
        structure = p.get_structure('protein', filepath)
        for chain in structure.get_chains():
            chain = structure[0][chain.id]
            for residue in chain.get_residues():
                if str(residue.id[1]) in self.resnums:
                    if residue.resname not in amino_acids.longer_names.keys():
                        pass
                    else:
                        res_mapping.append(
                            (chain.id,
                             self.codes[residue.resname],
                             residue.id[1]))
        return res_mapping

    def _get_mutants(self, res_mapping):
        mutants = {}
        for mapping in res_mapping:
            resid = set(mapping[0])
            aminoacids = set(self.inverse_codes.keys())
            mutant_list = list(aminoacids.difference(resid))
            mutants[mapping] = mutant_list
        return mutants

    def _write_mutant_list(self, mutant_dict, handle):
        out_file = os.getcwd() + '/' + self.filename + handle
        out = open(out_file, 'w')
        for key_tuple in mutant_dict:
            for aa in mutant_dict[key_tuple]:
                out.write(str(key_tuple[0]) + ' ' + str(key_tuple[1]) + ' ' +
                          str(key_tuple[2]) + ' ' + aa + '\n')
        out.close()

    def generate_mutant_list(self, pocketres=False, lpocket=False,
                             SurfRes=False):
        if pocketres and lpocket and SurfRes:
            self.handles = ['_pocketres', '_lpocket', '_SurfRes']
            self._get_resnums()
        if pocketres and lpocket:
            self.handles = ['_pocketres', '_lpocket']
            self._get_resnums()
        res_mapping = self._get_resmapping()
        mutants = self._get_mutants(res_mapping)
        self._write_mutant_list(mutants, '_mutant_list.txt')


class DDGMonomer:
    def __init__(self, pdb):
        self.filename = pdb

    def _get_filepath(self, data_file=False, pdb_file=False):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        if data_file:
            files = file_handlers.find_files(file_paths, 'txt')
            for path in files:
                if (self.filename + '_mutant_list') == \
                        file_handlers.get_file_name(path).split('.')[0]:
                    return path
        elif pdb_file:
            files = file_handlers.find_files(file_paths, 'pdb')
            for path in files:
                if (self.filename + '_0001') == \
                        file_handlers.get_file_name(path).split('.')[0]:
                    return path
        else:
            print "Specify file type"

    def _run_ddg_monomer(self, pdb_filepath, mutant_list, threshold):
        print "Running ddg_monomer..."
        cmd = ['~/rosetta/main/source/bin/'
               'pmut_scan_parallel.static.macosclangrelease -jd2 -s ' +
               pdb_filepath +
               ' -ex1 -ex2 -extrachi_cutoff 1 -use_input_sc '
               '-ignore_unrecognized_res -no_his_his_pairE '
               '-multi_cool_annealer 10 -mute basic core -mutants_list ' +
               mutant_list + ' -DDG_cutoff ' + threshold +
               ' | grep PointMut|grep -v "go()"|grep -v "main()" > ' +
               self.filename + '_mutants.out']
        subprocess.call(cmd, shell=True)

    def get_targets(self, threshold):
        mutant_list = self._get_filepath(data_file=True)
        pdb_filepath = self._get_filepath(pdb_file=True)
        self._run_ddg_monomer(pdb_filepath, mutant_list, str(threshold))


class SurfaceResidues:
    def __init__(self, pdb_code, server_mode=False):
        print "\n\nCalculating solvent accessible surface area using POPS...."
        self.dir_path = os.getcwd() + '/pops_results'
        self._mkdir()
        self.filename = pdb_code
        self.file_path = ''
        self.out_filename = ''
        self.out_file_path = ''
        self.data = []
        self.SASA_dict = {}
        self.found_modres = False
        self.server_mode = server_mode
        self.pdb_dir = os.getcwd()

    def _get_file_path(self, modres=False):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        pdb_files = file_handlers.find_files(file_paths, 'pdb')
        if modres:
            for pdb_file in pdb_files:
                if (self.filename + '_0001_edit_modres') == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    self.file_path = pdb_file
                    self.out_file = \
                        file_handlers.get_file_name(pdb_file).split('.')[0] + \
                        '_pops.out'
                    self.out_file_path = self.dir_path + '/' + self.out_file
        if self.server_mode:
            for pdb_file in pdb_files:
                if (self.filename) == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    self.file_path = pdb_file
                    self.out_file = \
                        file_handlers.get_file_name(pdb_file).split('.')[0] + \
                        '_pops.out'
                    self.out_file_path = self.dir_path + '/' + self.out_file
        else:
            for pdb_file in pdb_files:
                if (self.filename + '_0001') == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    self.file_path = pdb_file
                    self.out_file = \
                        file_handlers.get_file_name(pdb_file).split('.')[0] + \
                        '_pops.out'
                    self.out_file_path = self.dir_path + '/' + self.out_file

    def _mkdir(self):
        file_handlers = FileHandlers()
        file_handlers.make_results_folder(self.dir_path.split('/')[-1])

    def _check_for_modres(self, protein_filepath):
        p = PDBParser(QUIET=True)
        structure = p.get_structure('protein', protein_filepath)
        modres_list = []
        swapped_list = []
        for chain in structure.get_chains():
            chain = structure[0][chain.id]
            for residue in chain.get_residues():
                if residue.resname not in amino_acids.longer_names.keys():
                    if residue.resname in amino_acids.modres.keys():
                        self.found_modres = True
                        modres_list.append((str(residue.id[1]),
                                            residue.resname))
                        swapped_list.append(
                            (str(residue.id[1]),
                             amino_acids.modres[residue.resname]))
        if self.found_modres:
            print ('\nIdentified modified amino acids in structure %s' %
                   self.filename)
            print '\nModified residues found in structures:', modres_list
            print ('\n\nSwapping modified residues with canonical residues in '
                   'PDB for SASA calculation.')
            print '\nSwapped residues are: ', swapped_list
            pdb_editor = EditPDB(self.filename)
            pdb_editor.edit_resname(modres_list, '_0001_edit_modres.pdb')

    def _run_POPS(self):
        self._get_file_path()
        self._check_for_modres(self.file_path)
        if self.found_modres:
            self.file_path = ''
            self._get_file_path(modres=True)
        cmd = ['pops --pdb ' + self.file_path +
               ' --coarse --compositionOut --typeOut --topologyOut '
               '--atomOut --residueOut --chainOut --popsOut ' +
               self.out_file_path]
        with open(os.devnull, 'w') as fnull:
            subprocess.call(cmd, stdout=fnull, stderr=fnull, shell=True)

    def _get_data(self):
        Data = open(self.out_file_path)
        self.data = Data.readlines()
        Data.close()

    def _build_SASA_dict(self):
        file_handlers = FileHandlers()
        self.SASA_dict[self.filename] = {}
        self._run_POPS()
        self._get_data()
        for line in self.data:
            fields = line.split('\t')
            cleaned = file_handlers.clean(fields)
            if len(cleaned) == 9:
                position = cleaned[2]
                aa = cleaned[0]
                tot_SA = cleaned[8]
                SASA = cleaned[5]
                frac_SASA = cleaned[6]
                phob = cleaned[3]
                phil = cleaned[4]
                chain = cleaned[1]
                if aa in settings.AA_CODES:
                    self.SASA_dict[self.filename][(chain, position)] = \
                        [aa, tot_SA, SASA, frac_SASA, phob, phil]
                elif aa in settings.MODRES:
                    self.SASA_dict[self.filename][(chain, position)] = \
                        [settings.MODRES[aa], tot_SA, SASA, frac_SASA, phob,
                         phil]

    def write_resi_sasa_output(self):
        if self.SASA_dict == {}:
            self._build_SASA_dict()
        sasa_b_factor_filename = self.pdb_dir + '/' + self.filename + \
            '_sasa.txt'
        output_b_factors = open(sasa_b_factor_filename, 'w')
        for key in self.SASA_dict[self.filename]:
            chain = key[0]
            position = key[1]
            output_b_factors.write(self.SASA_dict[self.filename][key][0] +
                                   '\t' + chain + '\t' + position + '\t' +
                                   self.SASA_dict[self.filename][key][2] +
                                   '\n')
        output_b_factors.close()

    def write_frac_sasa_output(self):
        if self.SASA_dict == {}:
            self._build_SASA_dict()
        sasa_b_factor_filename = self.pdb_dir + '/' + self.filename + \
            '_fracsasa.txt'
        output_b_factors = open(sasa_b_factor_filename, 'w')
        for key in self.SASA_dict[self.filename]:
            chain = key[0]
            position = key[1]
            output_b_factors.write(self.SASA_dict[self.filename][key][0] +
                                   '\t' + chain + '\t' + position + '\t' +
                                   self.SASA_dict[self.filename][key][3] +
                                   '\n')
        output_b_factors.close()

    def write_surface_resi_output(self, threshold):
        surface_residues = self._get_surface_residues(threshold)
        out_filename = self.pdb_dir + '/' + self.filename + '_SurfRes.txt'
        output = open(out_filename, 'w')
        for line in surface_residues:
            split_line = line.split('\t')
            resi_position = split_line[2]
            resi_chain = split_line[1]
            resi_name = split_line[0]
            output.write(resi_name + '\t' + resi_chain + '\t' +
                         resi_position + '\t100.00\n')
        output.close()

    def _get_surface_residues(self, threshold):
        surface_residues = []
        if self.SASA_dict == {}:
            self._build_SASA_dict()
            for pdb_code in self.SASA_dict:
                for key, SASA_info_list in \
                        self.SASA_dict[pdb_code].iteritems():
                    chain = key[0]
                    position = key[1]
                    if float(SASA_info_list[3]) > threshold:
                        surface_residues.append(SASA_info_list[0] + '\t' +
                                                chain + '\t' + position)
        else:
            for pdb_code in self.SASA_dict:
                for key, SASA_info_list in \
                        self.SASA_dict[pdb_code].iteritems():
                    chain = key[0]
                    position = key[1]
                    if float(SASA_info_list[3]) > threshold:
                        surface_residues.append(SASA_info_list[0] + '\t' +
                                                chain + '\t' + position)
        print ("\nResidues with greater than %s %% solvent accessible surface "
               "area are: " % (str(float(threshold) * 100)))
        for line in surface_residues:
            print line.split('\t')
        return surface_residues


class EditPDB:
    def __init__(self, pdb_code, server_mode=False):
        self.filename = pdb_code
        self.data = []
        self.data_dict = {}
        self.chains = set([])
        self.server_mode = server_mode
        self.pdb_dir = os.getcwd() + '/results/'

    def _get_pdb(self, modres=False):
        pdb = ''
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        pdb_files = file_handlers.find_files(file_paths, 'pdb')
        for pdb_file in pdb_files:
            if modres:
                if (self.filename + '_0001') == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    PDB = open(pdb_file)
                    pdb = PDB.readlines()
                    PDB.close()
            else:
                if self.filename == \
                        file_handlers.get_file_name(pdb_file).split('.')[0]:
                    PDB = open(pdb_file)
                    pdb = PDB.readlines()
                    PDB.close()
        return pdb

    def _get_number_offset(self):
        offset = {}
        if self.server_mode:
            for chain in self.chains:
                offset[chain] = 0
            return offset
        minimized_pdb_lines = self._get_pdb(modres=True)
        for chain in self.chains:
            for line in minimized_pdb_lines:
                if line[0:6] == "ATOM  " and line[21:22] == chain:
                    first_resnum_minimized = int(line[22:26])
                    break
            raw_pdb_lines = self._get_pdb()
            for line in raw_pdb_lines:
                if line[0:6] == "ATOM  " and line[21:22] == chain:
                    first_resnum_raw = int(line[22:26])
                    break
            offset[chain] = first_resnum_raw - first_resnum_minimized
        return offset

    def _get_data(self, file_tag):
        file_handlers = FileHandlers()
        file_paths = file_handlers.search_directory()
        txt_files = file_handlers.find_files(file_paths, 'txt')
        for txt_file in txt_files:
            if self.filename == \
                    file_handlers.get_file_name(txt_file).split('_')[0]:
                if (file_tag.split('_')[1] + '.txt') == \
                        file_handlers.get_file_name(txt_file).split('_')[1]:
                    print txt_file
                    TXT = open(txt_file)
                    self.data = TXT.readlines()
                    TXT.close()

    def _build_data_dict(self, file_tag):
        self.data_dict = {}
        self._get_data(file_tag)
        file_handlers = FileHandlers()
        for line in self.data:
            fields = line.split('\t')
            cleaned = file_handlers.clean(fields)
            (self.chains).add(cleaned[1])
            self.data_dict[(cleaned[0], cleaned[1], int(cleaned[2]))] = \
                float(cleaned[3])

    def _edit_bfactor(self, file_tag):
        raw_pdb = self._get_pdb()
        self._build_data_dict(file_tag)
        offset = self._get_number_offset()
        lines_out = []
        for line in raw_pdb:
            if line[0:6] == "ATOM  ":
                name = line[17:20].strip()
                chain = line[21:22].strip()
                resnum = int(line[22:26].strip())
                k = (name, chain, (resnum - offset[chain]))
                if chain in offset and k in self.data_dict:
                    lines_out.append("%s%6.2F%s" %
                                     (line[:60],
                                      self.data_dict[k], line[66:]))
                else:
                    lines_out.append("%s%6s%s" % (line[:60], "NA", line[66:]))
            elif line[0:6] == "HETATM":
                lines_out.append("%s%6s%s" % (line[:60], "NA", line[66:]))
            else:
                lines_out.append(line)
        return lines_out

    def edit_resname(self, reslist, file_tag):
        raw_pdb = self._get_pdb(modres=True)
        lines_out = []
        for line in raw_pdb:
            if line[0:6] == "ATOM  ":
                for resnum in reslist[0]:
                    res_num = int(line[22:26].strip())
                    if res_num == resnum:
                        lines_out.append("%s%s%s" % (line[:17],
                                         amino_acids.modres[reslist[1]],
                                         line[20:]))
                    else:
                        lines_out.append(line)
        self._write_output(lines_out, file_tag)

    def _write_output(self, lines, file_tag):
        output_file = self.pdb_dir + self.filename + file_tag
        outfile = open(output_file, 'w')
        lines = self._edit_bfactor(file_tag)
        for line in lines:
            outfile.write(line)
        outfile.close()

    def _pull_bfactor(self):
        self._get_pdb()
        lines_out = {}
        for line in self.pdb:
            if line[0:6] == "ATOM  ":
                resnum = line[23:26].strip()
                b_factor = line[60:66].strip()
                lines_out[resnum] = resnum + '\t' + b_factor + '\n'
        return lines_out

    def _sort_keys(self, input_dict):
        temp_list = []
        for key in input_dict:
            temp_list.append(int(key))
        temp_list.sort()
        return temp_list

    def edit_bfactor_sasa(self):
        lines = self._edit_bfactor("_sasa")
        self._write_output(lines, "_sasa.pdb")

    def edit_bfactor_percent_sasa(self):
        lines = self._edit_bfactor("_fracsasa")
        self._write_output(lines, "_fracsasa.pdb")

    def edit_bfactor_ligand_binding_pocket(self):
        lines = self._edit_bfactor("_lpocket")
        self._write_output(lines, "_lpocket.pdb")

    def edit_bfactor_surface_residues(self):
        lines = self._edit_bfactor("_SurfRes")
        self._write_output(lines, "_SurfRes.pdb")

    def edit_bfactor_pockets(self):
        lines = self._edit_bfactor("_pockets")
        self._write_output(lines, "_pockets.pdb")

    def edit_bfactor_pocket_residues(self):
        lines = self._edit_bfactor("_pocketres")
        self._write_output(lines, "_pocketres.pdb")

    def get_bfactor(self):
        lines = self._pull_bfactor()
        sorted_list = self._sort_keys(lines)
        output_file = os.getcwd() + "/" + self.filename + \
            '_pulled_bfactors.txt'
        outfile = open(output_file, 'w')
        for resnum in sorted_list:
            outfile.write(lines[str(resnum)])
        outfile.close()
