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

	def lookup(self,e,ldict=None):
		"""Looks up x.y.z references in multilevel dictionary"""
		if ldict is None:
			ldict = self.combo
		comps=e.split('.')
		dkey = map(lambda x: "['%s']"%x, comps)
		try:
			rstr = str(eval("ldict%s"%"".join(dkey)))
		except:
			rstr = str(ldict[e])
		return rstr 

	def vLookup(self, v,vdict):
		""" Takes a string of the form {{ ... }} and looks up the variable name """
		return self.lookup(str(v).replace('{{','').replace('}}','').strip(),vdict)


	def rLookup(self,e):
		"""resolve lookups"""
		rhs = self.lookup(e)
		resolved = self.replaceVars(rhs,self.varsdict)
		if resolved == "None":
			return ''
		return resolved
		
	def hasVars(self,s):
		""" determine if a string has vars {{ }} """
		return len(re.findall(self.varpat,str(s))) > 0

	def varsInString(self,s):
		""" Return all the variable patterns in the supplied string """
		return re.findall(self.varpat,str(s))

	def extractVars(self,s):
		""" return a list of "stripped" var names """
		lvars = map(lambda x: x.replace('{{','').replace('}}','').strip(), 
		re.findall(self.varpat,str(s)))
		return lvars

	def replaceVars(self, s, vdict):
		""" replace the vars in string s with variables in a variables dict """
		rval = str(s)
		for var in self.varsInString(s):
			rval = rval.replace(str(var),self.vLookup(var,vdict))
		return rval 

	def setVar(self,vdict,v,value=''):
		vdict[v] = value


	def resolveVars(self):
		# This loop finds all the vars that need to be replaced 
		for key in self.combo.keys():
			rhs = self.combo[key]
			if self.hasVars(rhs):
				for v in self.extractVars(rhs):
					self.setVar(self.varsdict,v)
		""" Do an initial pass of setting key-value pairs """
		for v in self.varsdict.keys():
			self.setVar(self.varsdict,v,self.lookup(v,self.combo))

		while True:
			changed = 0
			for v in self.varsdict.keys():
				if self.hasVars(self.varsdict[v]):
					rhs = self.replaceVars(self.varsdict[v],self.combo)
					self.varsdict[v] = rhs
					changed = 1
			if changed == 0:
				break



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
try:
	print "CONFIGURE \t = %s" % mk.rLookup("build.configure")
except:
	pass

try:
	print "CONFIGURE_ARGS \t += %s" % mk.rLookup("build.configure_args")
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
