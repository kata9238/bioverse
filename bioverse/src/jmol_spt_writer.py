from util import FileHandlers

class JmolSPTWriter:
	def __init__(self, pdb_code, tag=''):
		self.filename = pdb_code
		self.spt_filename = "/Users/andrea/repositories/bioverse_beta/bioverse/static/results/jmol_script.spt"
		self.tag = tag

	def _get_filename(self):
		file_handlers = FileHandlers()
		file_paths = file_handlers.search_directory()
		pdb_files = file_handlers.find_files(file_paths, 'pdb')
		if self.tag == '':
			for pdb_file in pdb_files:
				if self.filename == file_handlers.get_file_name(pdb_file).split('.')[0]:
					return file_handlers.get_file_name(pdb_file).split('.')[0]
		else:
			for pdb_file in pdb_files:
				if (self.filename + self.tag) == file_handlers.get_file_name(pdb_file).split('.')[0]:
					return file_handlers.get_file_name(pdb_file).split('.')[0]

	def _get_spt_content(self):
		Data = open(self.spt_filename, 'r')
		data = Data.readlines()
		Data.close()
		return data

	def write_spt(self):
		pdb_file = self._get_filename
		lines = self._get_spt_content()
		if self.tag == '':
			filename = self.spt_filename.split('.')[0] + '_' + self.filename + '.spt'
		else:
			filename = self.spt_filename.split('.')[0] + '_' + self.filename + self.tag + '.spt'
		outfile = open(filename, 'w')
		for line in lines:
			fields = line.split(' ')
			if len(fields) == 5:
				if fields[2] == 'load':
					new_contents = fields[-2].split('/')
					if self.tag == '':
						new_contents[-1] = (self.filename).strip() + '.pdb";'
					else:
						new_contents[-1] = (self.filename + self.tag).strip() + '.pdb";'
					joined_new_contents = '/'.join(new_contents)
					fields[-2] = joined_new_contents
					outfile.write(''.join(fields))
				else:
					outfile.write(line)
			else:
					outfile.write(line)
		outfile.close()

		
				