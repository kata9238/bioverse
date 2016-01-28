from django.shortcuts import render
from django.views.generic import FormView
from .forms import ProteinForm

from src.pdb import CIFFParser, PDBPreProcessor
from src.jmol_spt_writer import JmolSPTWriter
from src.library_calculator import LibraryCalculator
from src.pdb_info_getter import PDBinfoGetter
from src.pdb_status_getter import PDBstatusGetter
from data_access.bioverse_sql import set_pdb_information


def index(request):
    return render(request, 'bioverse/index.html')


def protein(request):
    return render(request, 'bioverse/protein.html')


class Protein(FormView):
    code = ''
    msg = ''
    spt_ref_file = ''
    uniprot_id = ''
    genbank = ''
    title = ''
    target_residue_files = None
    template_name = 'bioverse/protein.html'
    sequence_annotations = []
    length_sa = len(sequence_annotations)
    form_class = ProteinForm
    resolution = ''
    experiment = ''
    colors = []
    full_saturation_library_size = []
    number_of_structures = ''
    str_chains = ''
    authors = []
    gene_info = None
    chains = None
    genes = None
    organisms = None
    pdb_sequences = None

    def get(self, request, format=None):
        return render(request, self.template_name,
                      {'code': self.code,
                       'msg': self.msg,
                       'spt_ref_file': self.spt_ref_file,
                       'uniprot_id': self.uniprot_id,
                       'genbank': self.genbank,
                       'title': self.title,
                       'target_residue_files': self.target_residue_files,
                       'sequence_annotations': self.sequence_annotations,
                       'length_sa': self.length_sa})

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            query_text = request.POST["pdb_code"]
            print query_text

            pdb_status_getter = PDBstatusGetter(query_text)
            pdb_status = pdb_status_getter.get_status()
            status_text = str(pdb_status)

            if status_text == 'False':
                pdb_info_getter = PDBinfoGetter(query_text)
                pdb_map = pdb_info_getter.main()
                print pdb_map
                return render(request, self.template_name,
                              {'pdb_map': pdb_map,
                               'code': query_text,
                               'pdb_status': pdb_status,
                               'msg': self.msg,
                               'spt_ref_file': self.spt_ref_file,
                               'uniprot_id': self.uniprot_id,
                               'genbank': self.genbank,
                               'title': self.title,
                               'target_residue_files':
                               self.target_residue_files,
                               'sequence_annotations':
                               self.sequence_annotations,
                               'length_sa': self.length_sa})

            elif status_text == 'True':
                pdb_code = query_text.upper()
                # Check if the pdb and ciff files have been downloaded. If not,
                # then fetch them.
                preprocessor = PDBPreProcessor(pdb_code)
                preprocessor.preprocess_check()
                number_of_structures, chains_in_asymmetric_unit = \
                    preprocessor.count_structures_in_asymmetric_unit()
                experiment = preprocessor.get_experiment_type()
                resolution = preprocessor.get_diffraction_resolution()
                # Get organism ID, gene names, pdb_sequences, and paper
                # metadata from .ciff file
                cif_parser = CIFFParser(pdb_code)
                chains, genes, organisms, pdb_sequences, title, authors = \
                    cif_parser.get_gene_annotations()
                sequence_annotations = \
                    cif_parser.collate_sequence_annotations()
                cif_parser.write_fasta(sequence_annotations)
                gene_info = cif_parser.get_gene_info_from_genbank()
                spt_writer = JmolSPTWriter(pdb_code)
                spt_writer.write_spt()
                spt_ref_file = 'jmol_script_' + pdb_code + '.spt'
                if sequence_annotations != []:
                    for gene in gene_info:
                        gene_name = gene_info[gene]['GENE'][0]
                        product = gene_info[gene]['PRODUCT']
                        function = gene_info[gene]['FUNCTION']
                        ref_seq = gene_info[gene]['PROTEIN_ID']
                        for information in sequence_annotations:
                            if gene_name.upper() == information[1]:
                                information[1] = gene_name
                                chain = information[0]
                                organism = information[2]
                                aa_sequence = information[3]
                                # Add data to database
                                created, msg = \
                                    set_pdb_information(
                                        pdb_code, title, authors, genes,
                                        organism, number_of_structures, chain,
                                        chains_in_asymmetric_unit, ref_seq,
                                        product, function, gene_name,
                                        spt_ref_file, aa_sequence)
                                print msg
                    colors = ['yellow', 'green', 'red', 'blue', 'orange',
                              'purple', 'grey']
                    recorded_info = {}
                    for entry in sequence_annotations:
                        if entry[1].upper() in gene_info:
                            recorded_info[entry[1].upper()] = \
                                gene_info[entry[1].upper()]
                            recorded_info[entry[1].upper()]['SEQUENCE'] = \
                                entry[3]
                            recorded_info[entry[1].upper()]['CHAIN'] = \
                                entry[0]
                            recorded_info[entry[1].upper()]['ORGANISM'] = \
                                entry[2]
                            library_calculator = \
                                LibraryCalculator(aa_sequence=entry[3])
                            saturated_library_size = \
                                library_calculator.calculate_library_size(
                                    full_saturation=True)
                            recorded_info[entry[1].upper()]['LIBRARY_SIZE'] = \
                                saturated_library_size
                            recorded_info[entry[1].upper()]['COLOR'] = \
                                colors[sequence_annotations.index(entry)]
                        tot_library_size = 0
                        for key in recorded_info:
                            tot_library_size += \
                                recorded_info[key]['LIBRARY_SIZE']
                        print "recorded_info:", recorded_info
                        print "sequence annotations:", sequence_annotations
                        print "gene info:", gene_info
                return render(request, self.template_name,
                              {'tot_library_size': tot_library_size,
                               'recorded_info': recorded_info,
                               'resolution': resolution,
                               'experiment': experiment,
                               'colors': colors,
                               'msg': self.msg,
                               'target_residue_files':
                               self.target_residue_files,
                               'number_of_structures': number_of_structures,
                               'str_chains': chains_in_asymmetric_unit,
                               'title': title,
                               'authors': authors,
                               'gene_info': gene_info,
                               'spt_ref_file': spt_ref_file,
                               'code': pdb_code,
                               'chains': chains,
                               'genes': genes,
                               'organisms': organisms,
                               'pdb_sequences': pdb_sequences,
                               'sequence_annotations': sequence_annotations})
            else:
                return render(request, self.template_name,
                              {'code': query_text,
                               'pdb_status': pdb_status,
                               'msg': self.msg,
                               'spt_ref_file': self.spt_ref_file,
                               'uniprot_id': self.uniprot_id,
                               'genbank': self.genbank,
                               'title': self.title,
                               'target_residue_files':
                               self.target_residue_files,
                               'sequence_annotations':
                               self.sequence_annotations,
                               'length_sa': self.length_sa})
