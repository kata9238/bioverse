#from datetime import datetime

#from bcrypt import hashpw, gensalt
import psycopg2
from sql_connection import SQLConnectionHandler
#from forge_design.util import create_rand_string, checkempty

sqlconnection = SQLConnectionHandler()

def set_pdb_information(pdb_code, title, authors, genes, organism, molecules_in_asymmetric_unit, chains, chains_in_asymmetric_unit, ref_seq, product, function, gene_name, spt_ref_file, aa_sequence_from_pdb):
    # Check to make sure pdb does not already exist
    sql = "SELECT * FROM pdb_information WHERE pdb_code = %s and gene_name = %s" % ("%s", "%s")
    #sql = "SELECT count(1) FROM pdb_information WHERE pdb_code = %s"
    try:
        exists = sqlconnection.execute_fetchall(sql, (pdb_code, gene_name))
    except Exception, e: # on ANY error return False
        return False, "Database query error! %s" % str(e)

    if exists:
        return False, "PDB already exists!"

    columns = ["pdb_code", "title", "authors", "genes", "organism", "molecules_in_asymmetric_unit", "chains", "chains_in_asymmetric_unit", "ref_seq", "product", "function", "gene_name", "spt_ref_file", "aa_sequence_from_pdb"]
    values = [pdb_code, title, authors, genes, organism, molecules_in_asymmetric_unit, chains, chains_in_asymmetric_unit, ref_seq, product, function, gene_name, spt_ref_file, aa_sequence_from_pdb]

    sql = ("INSERT INTO pdb_information (%s) VALUES (%s)" %
           (','.join(columns), ','.join(['%s'] * len(values))))
    try:
        sqlconnection.execute(sql, values)
    except Exception, e:
        return False, "Database set error! %s" % str(e)
    return True, "Update successful!"


def get_pdb_information(pdb_code):
    columns = ("pdb_code", "title", "authors", "genes", "organism", "molecules_in_asymmetric_unit", "chains", "chains_in_asymmetric_unit", "ref_seq", "product", "function", "gene_name", "spt_ref_file", "aa_sequence_from_pdb")
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


# EVERYTHING BELOW IS FROM THE FORGE PROJECT 2014

##      # SQL FUNCTIONS
##      def _change_pass(username, password):
##          # hash new password and store in database
##          hashedpw, salt = create_hashedpw(password)
##          sql = """UPDATE forge.forge_user SET password = %s, salt = %s WHERE
##                   email = %s"""
##          try:
##              sqlconnection.execute(sql, (hashedpw, salt, username))
##          except Exception, e:
##              raise RuntimeError("Unable to add password to database! %s" % str(e))
##      
##      
##      def create_hashedpw(password, salt=None):
##          """ Hashes password
##      
##          Parameters
##          ----------
##          password: str
##              Plaintext password
##          salt: str, optional
##              Salt used for hashing the password. If not given, generated before hash
##      
##          Returns
##          -------
##          hashedpw: str
##              Hashed password
##          salt: str
##              Salt used for hashing the password.
##          """
##          if salt is None:
##              salt = gensalt()
##          hashedpw = hashpw(str(password), str(salt))
##          return hashedpw, salt
##      
##      
##      def get_user_level(username):
##          """Checks database to see if user email is verified"""
##          sql = "SELECT user_level_id FROM forge.forge_user WHERE email = %s"
##          try:
##              code = sqlconnection.execute_fetchone(sql, (username,))[0]
##          except Exception, e:  # on ANY error return False
##              return False, "Database query error! %s" % str(e)
##      
##          return code
##      
##      
##      def set_verified(verify_code):
##          """Sets user to starndard user"""
##          sql = ("SELECT count(1) from forge.forge_user WHERE user_verify_code = %s")
##          try:
##              exists = sqlconnection.execute_fetchone(sql, (verify_code,))[0]
##          except Exception, e:  # on ANY error return False
##              return "Database query error! %s" % str(e)
##          if not exists:
##              return "Code not in database"
##      
##          # 3 is magic number for standard user
##          sql = ("UPDATE forge.forge_user set user_level_id = 3, "
##                 "user_verify_code = '' WHERE user_verify_code = %s")
##          try:
##              sqlconnection.execute(sql, (verify_code,))
##          except Exception, e:  # on ANY error return False
##              return "Database query error! %s" % str(e)
##          return ""
##      
##      
##      def check_password(username, password):
##          """Checks database to see if password is valid
##      
##          Parameters
##          ----------
##          username : str
##          password : str
##              Cleartext, unhashed password to check for `username`
##      
##          Returns
##          -------
##          bool
##              ``True`` if `password` is correct, else ``False``
##          """
##          sql = "SELECT password, salt from forge.forge_user WHERE email = %s"
##      
##          try:
##              dbinfo = sqlconnection.execute_fetchone(sql, (username,))
##              dbpass = dbinfo[0]
##              salt = dbinfo[1]
##          except:  # on ANY error return false
##              return False
##      
##          hashedpw, salt = create_hashedpw(password, salt)
##          return hashedpw == dbpass
##      
##      
##      def create_user(username, password, extrainfo=None):
##          """Creates a user in the database
##      
##          Parameters
##          ----------
##          username : str
##              Username (in this case email) of the user to create
##          password : str
##              Cleartext password for `username`
##          extrainfo : dict, optional
##              Defaults to ``None``. Other information to store. valid keys: "name",
##              "affiliation", "address", "phone"
##      
##          Returns
##          -------
##          bool
##              ``True`` if successful, else ``False``
##          str
##              Error message if unsuccessful, else verification code
##          """
##          if username == "":
##              return "No username given!"
##          if password == "":
##              return "No password given!"
##      
##          # Check to make sure user does not already exist
##          sql = "SELECT count(1) FROM forge.forge_user WHERE email = %s"
##          try:
##              exists = sqlconnection.execute_fetchone(sql, (username,))[0]
##          except Exception, e:  # on ANY error return False
##              return False, "Database query error! %s" % str(e)
##      
##          if exists:
##              return False, "Username already exists!"
##          if extrainfo is None:
##              extrainfo = {}
##      
##          verify_code = create_rand_string(20, punct=False)
##          hashedpw, salt = create_hashedpw(password)
##          columns = ["email", "password", "salt", "user_verify_code"]
##          values = [username, hashedpw, salt, verify_code]
##          for column, value in extrainfo.items():
##              columns.append(column)
##              values.append(value)
##      
##          sql = ("INSERT INTO forge.forge_user (%s) VALUES (%s)" %
##                 (','.join(columns), ','.join(['%s'] * len(values))))
##          try:
##              sqlconnection.execute(sql, values)
##          except Exception, e:
##              return False, "Database set error! %s" % str(e)
##          return True, verify_code
##      
##      
##      def get_profile(username):
##          """Returns the profile information for a given username
##      
##          Parameters
##          ----------
##          username : str
##              Username to get profile information of
##      
##          Returns
##          -------
##          profile : dict
##              Profile information in the form {column: info}
##      
##          Raises
##          ------
##          ValueError
##              If `username` is the empty string
##          RuntimeError
##              If profile cannot be retrieved from database
##          """
##          checkempty(username)
##          columns = ("email", "name", "affiliation", "address", "phone")
##      
##          sql = ("SELECT %s FROM forge.forge_user WHERE email = %s" %
##                 (', '.join(columns), "%s"))
##          try:
##              dbinfo = sqlconnection.execute_fetchone(sql, (username,))
##          except Exception, e:  # on ANY error raise runtime error
##              raise RuntimeError("Unable to get profile! %s" % str(e))
##          # format into dictionary and return
##          profile = {}
##          for pos, col in enumerate(columns):
##              profile[col] = dbinfo[pos]
##          return profile
##      
##      
##      def change_password(username, oldpass, newpass):
##          """Changes the password for a given user
##      
##          Parameters
##          ----------
##          username : str
##              Username (in this case email) of the user to create
##          oldpass : str
##              Cleartext current password for `username`
##          newpass : dict
##              Cleartext new password for `username`
##      
##          Returns
##          -------
##          str
##              Error message if unsuccessful, else empty string
##      
##          Raises
##          ------
##          ValueError
##              If any of `username`, `oldpass`, or `newpass` is the empty string
##          """
##          checkempty(username)
##          checkempty(oldpass)
##          checkempty(newpass)
##          # make sure old and new pass are different
##          if oldpass == newpass:
##              return "New password is same as current password"
##          # make sure old password is the real password for user
##          if not check_password(username, oldpass):
##              return "Current password is incorrect"
##          try:
##              _change_pass(username, newpass)
##          except:
##              return "Unable to add password to database"
##      
##          return ""
##      
##      
##      def change_profile(username, profile):
##          checkempty(username)
##          values = []
##          update = ""
##          # create update string for sql, slicing off extra comma, and values list
##          for key, val in profile.items():
##              update = ' '.join([update, key, "= %s,"])
##              values.append(val)
##          update = update[:-1]
##          values.append(username)
##      
##          sql = "UPDATE forge.forge_user SET %s WHERE email = %s" % (update, "%s")
##          try:
##              sqlconnection.execute(sql, values)
##          except Exception, e:
##              return "Unable to update user profile! %s" % str(e)
##          return "Update successful"
##      
##      
##      def forgot_password(username):
##          """Generates the code and timestamp for a lost password reset
##      
##          Parameters
##          ----------
##          username : str
##              Username (in this case email) of the user who forgot password
##      
##          Returns
##          -------
##          bool
##              Whether or not code was generated
##          str
##              The code for the forgotten password request, if it was successfully
##              generated, or the error generated if it wasn't
##      
##          Raises
##          ------
##          ValueError
##              If `username` is the empty string
##          RuntimeError
##              If unable to check code or insert code into database.
##          """
##          checkempty(username)
##          # check if username exists
##          sql = """SELECT count(1) FROM forge.forge_user WHERE email = %s"""
##          try:
##              # timestamp from machine running webserver so no confusion
##              exists = sqlconnection.execute_fetchone(sql, (username,))[0]
##          except:
##              raise RuntimeError("Unable to check reset code!")
##          if not exists:
##              return False, "Email not in database"
##      
##          # create code and enter it into database
##          code = create_rand_string(20, punct=False)
##          sql = """UPDATE forge.forge_user SET pass_reset_code = %s,
##                   pass_reset_timestamp = %s WHERE email = %s"""
##          try:
##              # timestamp from machine running webserver so no confusion
##              sqlconnection.execute(sql, (code, datetime.now(), username))
##          except:
##              raise RuntimeError("Unable to create reset code!")
##      
##          return True, code
##      
##      
##      def check_forgot_code(reset_code):
##          """Makes sure the reset code given is in the database
##      
##          Parameters
##          ----------
##          reset_code : str
##              reset code to check
##      
##          Returns
##          -------
##          exists : bool
##              ``True`` if exists, else ``False``
##      
##          Raises
##          ------
##          ValueError
##              If `reset_code` is the empty string
##          RuntimeError
##              If unable to check code into database.
##          """
##          checkempty(reset_code)
##          sql = "SELECT count(1) FROM forge.forge_user WHERE pass_reset_code = %s"
##          try:
##              # timestamp from machine running webserver so no confusion
##              exists = sqlconnection.execute_fetchone(sql, (reset_code,))[0]
##          except:
##              raise RuntimeError("Unable to check reset code!")
##          return bool(exists)
##      
##      
##      def change_forgot_password(username, reset_code, newpass):
##          """Checks reset code and time for user and changes forgotten password
##      
##          Parameters
##          ----------
##          username : str
##              Username (in this case email) of the user who forgot password
##          reset_code : str
##              Reset code for the user to validate it is truly them
##          newpass : str
##              Cleartext password to use as new password
##      
##          Returns
##          -------
##          str
##              Error message if unsuccessful, else empty string
##      
##          Raises
##          ------
##          ValueError
##              If `reset_code` not correct for `username`
##          """
##          checkempty(username)
##          checkempty(reset_code)
##          checkempty(newpass)
##          # get information from database
##          sql = """SELECT pass_reset_code, pass_reset_timestamp FROM forge.forge_user
##                 WHERE email = %s"""
##          try:
##              dbinfo = sqlconnection.execute_fetchone(sql, (username,))
##              dbcode = dbinfo[0]
##              dbtimestamp = dbinfo[1]
##          except Exception, e:  # on ANY error raise runtime error
##              return "Unable to get reset code & timestamp! %s" % str(e)
##      
##          # check we are within valid time frame (30 min)
##          diff = datetime.now() - dbtimestamp
##          if diff.seconds > 1800:
##              return "Past 30 minute window, restart reset process"
##      
##          # check reset code valid
##          if dbcode != reset_code:
##              raise ValueError("Code does not exist in database!")
##      
##          # reset password
##          try:
##              _change_pass(username, newpass)
##          except:
##              return "Unable to add password to database"
##      
##          return ""
##      
##      
##      def get_primers():
##          """Gets all data from primers table in forge database.
##      
##          Returns
##          -------
##          dbinfo: list
##              List of information from forge.primer
##      
##          Raises
##          ------
##          RunTimeError
##              If call to database fails
##          """
##          return sqlconnection.execute_fetchall("SELECT * FROM forge.primer")
##      
##      
##      def get_rbs():
##          """Gets all data from primers table in forge database.
##      
##          Returns
##          -------
##          dbinfo: list
##              List of information from forge.rbs
##      
##          Raises
##          ------
##          RunTimeError
##              If call to database fails
##          """
##          return sqlconnection.execute_fetchall("SELECT * FROM forge.rbs")
##      
##      
##      def get_promoters():
##          """Gets all data from promoters table in forge database.
##      
##          Returns
##          -------
##          dbinfo: list
##              List of information from forge.promoter
##      
##          Raises
##          ------
##          RunTimeError
##              If call to database fails
##          """
##          return sqlconnection.execute_fetchall("SELECT * FROM forge.promoter")







