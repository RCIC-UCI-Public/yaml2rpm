#! /bin/env python
# Generate a Definitions.mk file - write to standard output 

import yaml
import re
import sys
import datetime
import socket 
import getopt

class mkParser(object):
	def __init__(self):
		self.varsdict = {}
		self.varpat = re.compile('{{[A-Za-z0-9_\. ]+}}')
		self.kvdict = None   
		self.defaults = None 
		self.combo = None 

	def readPkgYaml(self,fname):
		with open(fname,"r") as f: 
			self.kvdict = yaml.load(f)
			self.combine()
	
	def readDefaultsYaml(self,fname):
		with open(fname,"r") as f: 
			self.defaults = yaml.load(f)
			self.combine()


	def combine(self):
		""" Combine pkg and defaults """
		# logic: if either defaults or kvdict is None, combo is whatever we have
                # if both are available combine
		if self.defaults is None or self.kvdict is None:
			if self.defaults is not None:
				self.combo = self.defaults.copy() 
			elif self.kvdict is not None:
				self.combo = self.kvdict[0].copy() 
		if self.defaults is not None and self.kvdict is not None:
			self.combo = self.defaults.copy()
			self.combo.update(self.kvdict[0])

	def lookup(self,e,ldict=None,stringify=True,listSep=None):
		"""Looks up x.y.z references in multilevel dictionary
		   stringify: True - return a string representation of contents
                              False - return the contents (could be any python type)
		   listSep:  for String representations of lists use listSep as separator
                             if L=[a,b,c] will return 'a' listSep 'b' listSep 'c'
                   if the returned value is a list, this will flatten the list for
                   simplicity """

		if ldict is None:
			ldict = self.combo
		comps=e.split('.')
		dkey = map(lambda x: "['%s']"%x, comps)
		try:
			val = eval("ldict%s"%"".join(dkey))
		except:
			val = ldict[e]
		#### print "BBBB", val
		if type(val) is list: 
			val = self.flatten(val)
		if stringify:
			if listSep is not None:
				return listSep.join(val)
			else:
				return str(val)
		else:
			return val

	def vLookup(self, v,vdict, stringify=True):
		"""Takes a string of the form {{ ... }} and looks up the variable name """
		return self.lookup(v.replace('{{','').replace('}}','').strip(),vdict,stringify)


	def rLookup(self,e,stringify=True,listSep=None):
		"""resolve lookups"""
		rhs = self.lookup(e,self.combo,stringify,listSep)
		if stringify:
			resolved = self.replaceVars(rhs,self.varsdict)
		else:
			resolved = rhs
		if resolved == "None":
			return ''
		return resolved
		
	def resolveStr(self,str):
		""" Resolve a string with vars """
		return self.replaceVars(str,self.varsdict)

	def hasVars(self,s):
		""" determine if a string has vars {{ }} """
		return len(re.findall(self.varpat,str(s))) > 0

	def varsInString(self,s):
		""" Return all the variable patterns in the supplied string """
		return re.findall(self.varpat,str(s))

	def extractVars(self,s):
		""" return a list of 'stripped' var names """
		lvars = map(lambda x: x.replace('{{','').replace('}}','').strip(), 
		re.findall(self.varpat,str(s)))
		return lvars

	def replaceVars(self, src, vdict):
		""" replace the vars in src with variables in a variables dict  """
		### print "XXXX", src, type(src)
		work = src
		if type(src) is not list:
			work = [ str(src) ]
		rwork=[]
		for elem in work:
			if type(elem) is type("string"):
				newlist = []
				for var in self.varsInString(elem):
					expand = self.vLookup(var,vdict,stringify=False)
					if type(expand) is type("string"):
						elem = elem.replace(var,expand)
					else:
						# Variable expanded to another list, recurse
						tmp = self.replaceVars(expand,vdict)
						newlist.extend(tmp)
				if len(newlist) == 0:
					rwork.append(elem)
				else:	
					rwork.extend(newlist)
			else:
				tmp = self.replaceVars(elem,vdict)
				rwork.append(tmp)
		### print "ZZZZ", rwork
		if len(rwork) == 1:
			return rwork[0]
		else:
			return rwork

	def setVar(self,vdict,v,value=''):
		vdict[v] = value


	def resolveVars(self):
		""" Resolve all variables in the combo dictionary. As variables are 
                    are resolved, the object varsdict will hold the resolved versions """

		# This loop finds all the vars that need to be replaced  in any definition
		for key in self.combo.keys():
			rhs = self.combo[key]
			if self.hasVars(rhs):
				for v in self.extractVars(rhs):
					self.setVar(self.varsdict,v,rhs)

		# Do an initial pass of setting key-value pairs
		# Do NOT Stringify at this point
		for v in self.varsdict.keys():
			self.setVar(self.varsdict,v,self.lookup(v,self.combo,False))

		# print "QQQQ", "vardict", self.varsdict
		while True:
			changed = 0
			for v in self.varsdict.keys():
				if self.hasVars(self.varsdict[v]):
					rhs = self.replaceVars(self.varsdict[v],self.combo)
					self.varsdict[v] = rhs
					changed = 1
			if changed == 0:
				break


	def flatten(self, mllist):
		""" recursive method to flatten list of elements where each element
			might itself be a list """
		if type(mllist) is not list:
			return None
		sublists = filter(lambda x: type(x) is list, mllist)
		literals = filter(lambda x: type(x) is not list, mllist)
		if len(sublists) == 0:
			return literals
		else:
			literals.extend(self.flatten([val for sub in sublists for val in sub]))
			return literals

class moduleGenerator(object):
	def __init__(self,mkp):
		""" mkp is an mkParser, already initialized """
		self.mk = mkp
		self.name = self.mk.rLookup("name")
		self.version = self.mk.rLookup("version")
		self.description = self.mk.rLookup("description") 
		self.logger = "if { [ module-info mode load ] } {\n  %s\n}"
		self.logger2 = 'if { [ module-info mode load ] } {\n  puts stderr "%s"\n}'

	def gen_header(self):
		profile = """#%%Module1.0#####################################################################
## module.skeleton adapted from modulizer script originally written by Harry Mangalam (hjm)
## Date: %s
## Built on: %s
""" 
		rstr = profile % (str(datetime.date.today()),socket.getfqdn())	
		return rstr
	def gen_whatis(self):
		desc = """set DESC \"                            %s/%s
%s
\"
"""
		rstr =  desc % (self.name, self.version, self.description)
		rstr += 'module-whatis "\n$DESC\n"\n'
		return rstr

 	def prepend_path(self):
		""" create the prepend-path elements """
		rstr = ""
		try:
			entries = self.mk.rLookup("module.prepend_path", stringify=False)
		except:
			return rstr
		paths = [ self.mk.resolveStr(p) for p in entries ]
		paths = self.mk.flatten(paths)
		template = "prepend-path\t%s\t%s\n"
		for path in paths:
			pName,pPath = re.split('[ \t]+', path, 1) 
			rstr += template % ( self.mk.resolveStr(pName), self.mk.resolveStr(pPath))
		return rstr


 	def gen_setenv(self):
		""" Create Environment Variables from module.setenv list """
		rstr = ""
		try:
			entries = self.mk.rLookup("module.setenv", stringify=False)
		except:
			return rstr
		envVars = [ self.mk.resolveStr(p) for p in entries ]
		envVars = self.mk.flatten(envVars)
		template = "setenv\t%s\t%s\n"
		for envVar in envVars:
			eName,eVal = re.split('[ \t]+', envVar, 1)
			rstr += template % ( self.mk.resolveStr(eName), self.mk.resolveStr(eVal))
		return rstr

	def generate(self):
		""" return a string that can written as  module file """
		rstr = ""
		rstr += self.gen_header()
		rstr += self.gen_whatis()
		rstr += self.gen_setenv()
		rstr += self.prepend_path() 
		return rstr

class makeIncludeGenerator(object):
	""" Create output for Definitions.mk """
	def __init__(self,mkp):
		""" mkp is an mkParser, already initialized """
		self.mk = mkp

	def generate(self):
		rstr = ""
		# The following are required keys -- throw an error if they don't exist
		rstr += "TARNAME\t = %s\n" % self.mk.rLookup("name")
		rstr += "VERSION\t = %s\n" % str(self.mk.rLookup("version"))
		try:
			rstr += "NAME\t = %s\n" % self.mk.rLookup("pkgname")
		except:
			rstr += "NAME\t = $(TARNAME)_$(VERSION)\n"
		rstr += "TARBALL-EXTENSION \t = %s\n" % self.mk.rLookup("extension")
		rstr += "DESCRIPTION \t = %s\n" % self.mk.rLookup("description")
		rstr += "PKGROOT \t = %s\n" % self.mk.rLookup("root")

		try:
			rstr += "VENDOR\t = %s\n" % self.mk.rLookup("vendor")
		except:
			pass
		try:
			rstr +=  "SRC_DIR\t = %s\n" % self.mk.rLookup("src_dir")
		except:
			pass

		# The following are optional and are put in try blocks
		try:
			rstr +=  "PRECONFIGURE\t = %s\n" % self.mk.rLookup("build.preconfigure")
		except:
		 	rstr += "PRECONFIGURE = echo no preconfigure required\n"

		stdconfigure = "+=" 
		try:
			rstr +=  "CONFIGURE \t = %s\n" % self.mk.rLookup("build.configure")
			stdconfigure = "="
		except:
			pass

		try:
			rstr += "CONFIGURE_ARGS \t %s %s\n" %  \
				(stdconfigure, self.mk.rLookup("build.configure_args"))
		except:
			pass
		try:
			mods = self.mk.rLookup("build.modules", stringify=False)
			if type(mods) is list:
				jmods = ",".join(mods)
				mods=jmods
			if mods is None:
				mods = ""
			rstr += "MODULES \t = %s\n" % self.mk.resolveStr(mods) 
		except:
			pass

		try:
                        mpath = ''
			mpath = self.mk.rLookup("module.path")
		except:
			pass
		rstr += "MODULESPATH \t = %s\n" % mpath 

		try:
                        mname = ''
			mname = self.mk.rLookup("module.name")
		except:
			pass
		rstr += "MODULENAME \t = %s\n" % mname 

		try:
			rstr += "BUILDTARGET \t = %s\n" % self.mk.rLookup("build.target")
		except:
			pass

		try:
			rstr += "PKGMAKE \t = %s\n" % self.mk.rLookup("build.pkgmake")
		except:
			pass

		try:
			rstr += "PATCH_FILE \t = %s\n" % self.mk.rLookup("build.patchfile")
			rstr += "PATCH_METHOD \t = $(PATCH_CMD)\n" 
		except:
			rstr += "PATCH_METHOD \t = $(PATCH_NONE)\n" 

		try:
			rstr += "MAKEINSTALL \t = %s\n" % self.mk.rLookup("install.makeinstall")
		except:
			pass

		try:
			rstr += "INSTALLEXTRA\t = %s\n" % self.mk.rLookup("install.installextra")
		except:
			pass
		try:
			reqs =  self.mk.rLookup("requires",stringify=False)
			### print reqs,type(reqs)
			if type(reqs) is list:
				jreqs = ",".join(reqs)
				reqs = jreqs
			rstr += "RPM.REQUIRES\t = %s\n" % self.mk.resolveStr(reqs)
		except:
			pass


		try:
			files =  self.mk.rLookup("files",stringify=False)
			if type(files) is list:
				allfiles = " \\n\\\n".join(files)
				files = allfiles 
			rstr += "RPM.FILES\t = %s\n" % self.mk.resolveStr(files) 
		except:
			rstr += "RPM.FILES\t = $(PKGROOT)\n" 

		return rstr

class queryProcessor(object):
	""" Query based on the yaml file """
	def __init__(self,mkp):
		""" mkp is an mkParser, already initialized """
		self.mk = mkp

	def processQuery(self,query,quiet=False,listSep=None):
		rq = query.strip().lower()
		if rq == "patch":
			rq = "build.patchfile"
		elif rq == "source":
			rq = "vendor_source"

		if rq == "tarball":
			rstr = self.mk.rLookup("name")
			rstr += "-%s" % str(self.mk.rLookup("version"))
			rstr += ".%s" % self.mk.rLookup("extension")
			print rstr
			sys.exit(0)
		if rq == "pkgname":
			try:
				rstr = self.mk.rLookup("pkgname")
			except:
				rstr = "%s_%s" % (self.mk.rLookup("name"), self.mk.rLookup("version")) 
			print rstr
			sys.exit(0)
		try:
			rval = self.mk.rLookup(rq,listSep=listSep)
			if type(rval) is list and listSep is not None:
				rval = listSep.join(rval)
		except:
			if not quiet:
				print 'False'
			sys.exit(-1)
			
		if not quiet:
			if len(rval) > 0:
				print rval
			else:
				print 'True'

## *****************************
## main routine
## *****************************

def usage():
	print 'gen-defintions.py [-d <defaults file>] [-m] [-h] <pkg file>'
	print '     -d <defaults file>  - YAML file for packaging defaults'
	print '     -m                  - generate environment modules file'
	print '	    -q <type>		- query [types: patch, module, source, pkgname, tarball]'
	print '     -h                  - print this help'
	print '     <pkg file>  	- YAML file with packaging definitions'

def main(argv):
	doModule = False 
	doQuery = False 
	queryType = ''
	quiet = False
	dflts_file = 'pkg-defaults.yaml'
	listSep = None
	try:
		opts, args = getopt.getopt(argv,"d:hl:mq:Q",["defaults=","help","module","listsep=","query=","quiet"])
	except getopt.GetoptError:
		usage()
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
		 	usage()	
			sys.exit()
		elif opt in ("-d", "--defaults"):
			dflts_file = arg
		elif opt in ("-l", "--listsep"):
		 	listSep = arg	
		elif opt in ("-m", "--module"):
		 	doModule = True	
		elif opt in ("-q", "--query"):
		 	doQuery = True	
			queryType = arg
		elif opt in ("-Q", "--quiet"):
		 	quiet = True	

##	Open files, parse, generate
	yamlfile = sys.argv[-1]
	mkP = mkParser()
	mkP.readPkgYaml(yamlfile)
	mkP.readDefaultsYaml(dflts_file)
	mkP.resolveVars()

	mg = moduleGenerator(mkP)
	mig = makeIncludeGenerator(mkP)
	qp = queryProcessor(mkP)

	if doModule: 
		print mg.generate() 
	elif doQuery:
		qp.processQuery(queryType,quiet,listSep)
	else:
		print mig.generate()

if __name__ == "__main__":
	main(sys.argv[1:])
		
