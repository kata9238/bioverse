import settings

class LibraryCalculator:
	def __init__(self, pdb_code='', aa_sequence=''):
		self.filename = pdb_code
		self.aa_sequence = aa_sequence

	def calculate_library_size(self, full_saturation=False, target_site_saturation=False, filtered_site=False):
		library_size = 0
		if full_saturation == True:
			sequence_length = len(self.aa_sequence)
			mutations = {}
			for i in range(len(self.aa_sequence)):
				#mutations[i] = [ key for key in settings.E_COLI_CODON_USAGE if key != self.aa_sequence[i] and key != 'X' ]
				mutations[i] = [ key for key in settings.E_COLI_CODON_USAGE if key != self.aa_sequence[i] ]
			for resnum in mutations:
				library_size += len(mutations[resnum])
		if target_site_saturation == True:
			pass
		return library_size


#def main():
#	calculator = LibraryCalculator(aa_sequence = 'MISLIAALAVDRVIGMENAMPWNLPADLAWFKRNTLNKPVIMGRHTWESIGRPLPGRKNIILSSQPGTDDRVTWVKSVDEAIAACGDVPEIMVIGGGRVYEQFLPKAQKLYLTHIDAEVEGDTHFPDYEPDDWESVFSEFHDADAQNSHSYCFEILERR')
#	library_size = calculator.calculate_library_size(full_saturation=True)
#	print "library size for complete saturation (with highest usage codons and no stop codons):", library_size
#
#main()
