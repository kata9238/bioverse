import urllib2
import xmltodict


class PDBstatusGetter:
    def __init__(self, query):
        self.query = query
        self.url = 'http://www.rcsb.org/pdb/rest/idStatus?structureId='

    def set_url(self):
        return self.url + self.query

    def query_pdb(self):
        url = self.set_url()
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        the_page = response.read()
        data = xmltodict.parse(the_page)
        return data

    def get_status(self):
        data = self.query_pdb()
        return data['idStatus']['record']['@status'] == 'CURRENT'
