from sql_connection import SQLConnectionHandler


sqlconnection = SQLConnectionHandler()


def set_pdb_information(pdb_code, title, authors, genes, organism,
                        molecules_in_asymmetric_unit, chains,
                        chains_in_asymmetric_unit, ref_seq, product, function,
                        gene_name, spt_ref_file, aa_sequence_from_pdb):
    # Check to make sure pdb does not already exist
    sql = ("SELECT * FROM pdb_information WHERE pdb_code = %s and "
           "gene_name = %s" % ("%s", "%s"))
    try:
        exists = sqlconnection.execute_fetchall(sql, (pdb_code, gene_name))
    except Exception, e:  # on ANY error return False
        return False, "Database query error! %s" % str(e)

    if exists:
        return False, "PDB already exists!"

    columns = ["pdb_code", "title", "authors", "genes", "organism",
               "molecules_in_asymmetric_unit", "chains",
               "chains_in_asymmetric_unit", "ref_seq", "product",
               "function", "gene_name", "spt_ref_file", "aa_sequence_from_pdb"]
    values = [pdb_code, title, authors, genes, organism,
              molecules_in_asymmetric_unit, chains, chains_in_asymmetric_unit,
              ref_seq, product, function, gene_name, spt_ref_file,
              aa_sequence_from_pdb]

    sql = ("INSERT INTO pdb_information (%s) VALUES (%s)" %
           (','.join(columns), ','.join(['%s'] * len(values))))
    try:
        sqlconnection.execute(sql, values)
    except Exception, e:
        return False, "Database set error! %s" % str(e)
    return True, "Update successful!"


def get_pdb_information(pdb_code):
    columns = ("pdb_code", "title", "authors", "genes", "organism",
               "molecules_in_asymmetric_unit", "chains",
               "chains_in_asymmetric_unit", "ref_seq", "product", "function",
               "gene_name", "spt_ref_file", "aa_sequence_from_pdb")
    sql = ("SELECT * FROM pdb_information WHERE pdb_code = %s" % "%s")
    try:
        dbinfo = sqlconnection.execute_fetchall(sql, (pdb_code,))
    except Exception, e:  # on ANY error raise runtime error
        raise RuntimeError("Unable to get pdb information! %s" % str(e))
    pdb_information = {}
    for tuple_data in dbinfo:
        gene_name = tuple_data[-3]
        pdb_information[gene_name] = {}
        for pos, col in enumerate(columns):
            pdb_information[gene_name][col] = tuple_data[pos]
    return pdb_information
