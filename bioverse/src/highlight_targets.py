import settings
from util import FileHandlers

class TargetHighlighter:
	def __init__(self, pdb_code, sequence_annotations, SurfRes=False, pocket=False, lpocket=False):
		self.filename = pdb_code
		self.sequence_annotations = sequence_annotations
		if SurfRes == True:
			file_handlers = FileHandlers()
			file_paths = file_handlers.search_directory()
			txt_files = file_handlers.find_files(file_paths, 'txt')
			for txt_file in txt_files:
				if (self.filename + '_SurfRes.txt') == file_handlers.get_file_name(txt_file):
					self.surfres_file = txt_file
				else:
					self.surfres_file = ''
		if pocket == True:
			file_handlers = FileHandlers()
			file_paths = file_handlers.search_directory()
			txt_files = file_handlers.find_files(file_paths, 'txt')
			for txt_file in txt_files:
				if (self.filename + '_pocketres.txt') == file_handlers.get_file_name(txt_file):
					self.pocketres_file = txt_file
				else:
					self.pocketres_file = ''
		if lpocket == True:
			file_handlers = FileHandlers()
			file_paths = file_handlers.search_directory()
			txt_files = file_handlers.find_files(file_paths, 'txt')
			for txt_file in txt_files:
				if (self.filename + '_lpocket.txt') == file_handlers.get_file_name(txt_file):
					self.lpocket_file = txt_file
				else:
					self.lpocket_file = ''

	def _get_data(self, file_path):
		TXT = open(file_path)
		data = TXT.readlines()
		TXT.close()
		return data

	def _build_data_structure(self, lines):
		file_handlers = FileHandlers()
		feature_data_dict = {}
		for i in range(len(self.sequence_annotations)):
			feature_data_dict[self.sequence_annotations[i][1]] = [[], self.sequence_annotations[i][3]]
			residues = []
			current_chain = self.sequence_annotations[i][0]
			for line in lines:
				fields = line.split('\t')
				cleaned = file_handlers.clean(fields)
				residue_name = cleaned[0]
				chain = cleaned[1]
				residue_number = cleaned[2]
				if chain == current_chain:
					residues.append(residue_number)
			feature_data_dict[self.sequence_annotations[i][1]][0] = residues
		return feature_data_dict # {gene_name: [ [residue numbers of interest], sequence ]}


	def build_feature_dict(self):
		if self.surfres_file != '':
			surf_res_lines = self._get_data(self.surfres_file)
			feature_data_dict = self._build_data_structure(surf_res_lines)
			return feature_data_dict
		if self.pocketres_file != '':
			pocket_res_lines = self._get_data(self.pocketres_file)
			feature_data_dict = self._build_data_structure(pocket_res_lines)
			return feature_data_dict
		if self.lpocket_file != '':
			lpocket_res_lines = self._get_data(self.lpocket_file)
			feature_data_dict = self._build_data_structure(lpocket_res_lines)
			return feature_data_dict
		else:
			return "No residues were picked."


def main():
	sequence_annotations = [['A', 'ssb', 'Escherichia coli', 'ASRGVNKVILVGNLGQDPEVRYMPNGGAVANITLATSESWEQTEWHRVVLFGKLAEVASEYLRKGSQVYIEGQLRTRKWTDQDRYTTEVVVNVGGTMQML']]
	highlighter = TargetHighlighter('1SRU', sequence_annotations, SurfRes=True)
	feature_data_dict = highlighter.build_feature_dict()
	print feature_data_dict

main()










