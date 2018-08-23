#! /bin/env python
# Generate a Definitions.mk file - write to standard output 

import yaml
import re
import sys

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

	def lookup(self,e,ldict=None,stringify=True):
		"""Looks up x.y.z references in multilevel dictionary
		   stringify: True - return a string representation of contents
                              False - return the contents (could be any python type)
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
			return str(val)
		else:
			return val

	def vLookup(self, v,vdict, stringify=True):
		"""Takes a string of the form {{ ... }} and looks up the variable name """
		return self.lookup(v.replace('{{','').replace('}}','').strip(),vdict,stringify)


	def rLookup(self,e,stringify=True):
		"""resolve lookups"""
		rhs = self.lookup(e,self.combo,stringify)
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
		self.header = ""
		self.description = ""
		self.whatis = "module-whatis %s"
		self.logger = "if { [ module-info mode load ] } {\n  %s\n}"
		self.logger2 = 'if { [ module-info mode load ] } {\n  puts stderr "%s"\n}'

 	def prepend_path(self):
		""" create the prepend-path elements """
		rstr = ""
		entries = self.mk.rLookup("module.prepend_path", stringify=False)
		paths = [ self.mk.resolveStr(p) for p in entries ]
		paths = self.mk.flatten(paths)
		template = "prepend-path\t%s\t%s\n"
		for path in paths:
			pName,pPath = path.split(None,2)
			rstr += template % ( self.mk.resolveStr(pName), self.mk.resolveStr(pPath))
		return rstr


yamlfile = sys.argv[1]
mk = mkParser()
mk.readPkgYaml(yamlfile)
mk.readDefaultsYaml("pkg-defaults.yaml")
mk.resolveVars()
keys = ("package","name","version","extension","description","root","build.configure","install.makeinstall","install.installextra") 


# The following are required keys -- throw an error if they don't exist
print "TARNAME\t = %s" % mk.rLookup("name")
print "VERSION\t = %s" % str(mk.rLookup("version"))
print "NAME\t = $(TARNAME)_$(VERSION)"
print "TARBALL-EXTENSION \t = %s" % mk.rLookup("extension")
print "DESCRIPTION \t = %s" % mk.rLookup("description")
print "PKGROOT \t = %s" % mk.rLookup("root")

# The following are optional and are put in try blocks
stdconfigure = "+=" 
try:
	print "CONFIGURE \t = %s" % mk.rLookup("build.configure")
	stdconfigure = "="
except:
	pass

try:
	print "CONFIGURE_ARGS \t %s %s" % (stdconfigure, mk.rLookup("build.configure_args"))
except:
	pass
try:
	print "MODULES \t = %s" % mk.rLookup("build.modules")
except:
	pass
try:
	print "BUILDTARGET \t = %s" % mk.rLookup("build.target")
except:
	pass
try:
	print "MAKEINSTALL \t = %s" % mk.rLookup("install.makeinstall")
except:
	pass

try:
	print "INSTALLEXTRA\t = %s" % mk.rLookup("install.installextra")
except:
	pass
try:
	print "RPM.REQUIRES\t = %s" % mk.rLookup("requires")
except:
	pass

mg = moduleGenerator(mk)
print "module prepend\n%s" %mg.prepend_path() 
