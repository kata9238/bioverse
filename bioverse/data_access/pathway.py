from sys import argv

from bioservices import UniChem, ChEBI, Kegg, KeggParser
from tornado.httpclient import HTTPClient, HTTPError
from SOAPpy import SOAPProxy
from indigo import Indigo

# use tornado httpclient to get initial compound ids for smiles
def get_compound_id(smiles):
    """ returns kegg id for compund with given smiles """
    indigo = Indigo()
    #convert smiles to standard format
    mol = indigo.loadMolecule(smiles)
    mol.aromatize()
    moi_smiles = mol.canonicalSmiles()

    # Get list of possible kegg IDs
    url = "http://rest.genome.jp/subcomp/?smiles=%s&cutoff=1.0" % smiles
    http_client = HTTPClient()
    try:
        response = http_client.fetch(url).body
    except HTTPError as e:
        raise RuntimeError("Error:", str(e))
    http_client.close()
    subcomp_results = response.split("\n")
    subcomp_results.pop()
    subcomp_results = ([i.split('\t')[0] for i in subcomp_results])

    # get smiles for all compound IDs found
    all_smiles = []
    uni = UniChem()
    mapping = uni.get_mapping("kegg_ligand", "chebi")
    ch = ChEBI()
    all_smiles = [ch.getCompleteEntity(mapping[x]).smiles
                  for x in subcomp_results]

    # convert smiles to a standard format
    for pos, mol in enumerate(all_smiles):
        m = indigo.loadMolecule(mol)
        m.aromatize()
        all_smiles[pos] = m.canonicalSmiles()

    # check if smiles matches given and, if so, use that compound ID
    # if not, errors out
    try:
        index = all_smiles.index(moi_smiles)
    except:
        raise RuntimeError("SMILES unmatchable to: %s" % str(all_smiles))
    return subcomp_results[index]


def get_compound_name(keggid):
    """ returns the compund IUPAC and coloquial name for a given KEGG ID """
    kegg = Kegg(verbose=False)
    name = kegg.find("compound", keggid).strip()
    return name.split('\t')[1]


def get_reaction_ids(keggid):
    """Returns list of kegg reaction IDs for creation of compund with given
     kegg ID"""
    keggparser = KeggParser()
    search = keggparser.get(keggid)
    parsed = keggparser.parse(search)
    if 'reaction' in parsed:
        reaction_ids = []
        reaction_num = parsed['reaction']
        if isinstance(reaction_num, dict):
            for key, value in reaction_num.items():
                reaction_ids.append(key)
                reaction_ids.extend(value.split())
        elif isinstance(reaction_num, str):
            reaction_ids = reaction_num.split()
        return reaction_ids
    else:
        return []


def get_enzyme_equation(rxnid, equation=True):
    """ Gets the kegg ID, name, and equation of enzyme catalizing reaction in
        rxnid"""
    keggparser = KeggParser()
    search_rxn = keggparser.get(rxnid)
    rxninfo = keggparser.parse(search_rxn)

    if equation and 'equation' in rxninfo:
        equation = rxninfo['equation']
    else:
        raise RuntimeError("Equation unavailable for given reaction")
    if 'name' in rxninfo:
        name = rxninfo['name']
    else:
        raise RuntimeError("Name unavailable for given reaction enzyme")
    if 'enzyme' in rxninfo:
        enzyme = rxninfo['enzyme']
    else:
        raise RuntimeError("Enzyme id unavailable for given reaction")

    if equation:
        return enzyme, name, equation
    else:
        return enzyme, name


def get_brenda_info(ecnum):
    """Returns protein sequence and accompanying info from brenda database"""
    url = "http://www.brenda-enzymes.info/soap2/brenda_server.php"
    client = SOAPProxy(url)
    result = client.getSequence("ecNumber*%s" % ecnum)
    result_lines = result.split("#")
    ecnum = result_lines[0].split("*")
    final_info = []
    currinfo = {"ecNumber": ecnum[1]}
    for info in result_lines[1:-1]:
        key, value = info.split("*")
        if key == "!ecNumber":
            final_info.append(currinfo)
            currinfo = {"ecNumber": value}
        else:
            currinfo[key] = value
    final_info.append(currinfo)
    return final_info


def main(smiles):
    print "STARTING SMILES:", smiles
    cid = get_compound_id(smiles)
    print "compund id:", cid
    name = get_compound_name(cid)
    print "name:", name
    rxnids = get_reaction_ids(cid)
    print "reaction ids:", rxnids
    enzyme, name, equation = get_enzyme_equation(rxnids[0])
    print "enzyme:", enzyme, name
    print "equation:", equation
    info = get_brenda_info(enzyme)
    print "brendainfo:", info

if __name__ == "__main__":
    if len(argv) == 1:
        smiles = "CC(C)O"
    else:
        smiles = argv[1]
    main(smiles)
