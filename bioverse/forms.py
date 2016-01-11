from django import forms

class ProteinForm(forms.Form):
	pdb_code = forms.CharField(label='Enter a sequence identifier', max_length=100)