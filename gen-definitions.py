#!/bin/env python
# Generate a Definitions.mk file - write to standard output 

#from __future__ import print_function
#from builtins import next
##from builtins import str
#from builtins import object

#import yaml
import ruamel.yaml 
#from pathlib2 import Path
import re
import sys
import datetime
import socket 
import os
import io
import argparse
import pdb

if sys.version_info.major == 3:
    from typing import Dict
incMap = {} # type: Dict[str, str]

yaml = ruamel.yaml.YAML(typ='safe', pure=True)
yaml.default_flow_style = False

def new_compose_document(self):
    self.parser.get_event()
    node = self.compose_node(None, None)
    self.parser.get_event()
    return node

def new_yaml_include(loader, node):
    y = loader.loader
    yaml = ruamel.yaml.YAML(typ=y.typ, pure=y.pure)  # same values as including YAML
    yaml.composer.anchors = loader.composer.anchors
    incPath = IncPath().getPath()
    global incMap
    filename = loader.construct_scalar(node)
    if filename in list(incMap.keys()):
        filename = incMap[filename]
    for p in incPath:
        try:
            with open(os.path.join(p,filename), 'r') as f:
                # FIXME return last line only
                data = yaml.load(f)
                #print ("=== FILE START:", f)
                #yaml.dump(data, sys.stdout)
                #print ("=== FILE END")
                return data
                #return yaml.load(f)
        except:
            pass
    raise  Exception("%s not found in: %s" % (filename,str(incPath)))

yaml.Composer.compose_document = new_compose_document
yaml.Constructor.add_constructor("!include", new_yaml_include)

#class Loader(object):
#    def __init__(self, stream):
#        self._root = os.path.split(stream.name)[0]
#        self.incPath = IncPath().getPath()
#        super(Loader, self).__init__(stream)
#
#    def include(self, node):
#        global incMap
#        filename = self.construct_scalar(node)
#        if filename in list(incMap.keys()):
#            filename = incMap[filename]
#        # look for filename in the incPath
#        for p in self.incPath:
#            try:
#                with open(os.path.join(p,filename), 'r') as f:
#                    return yaml.load(f, Loader)
#            except:
#                pass 
#        raise  Exception("%s not found in: %s" % (filename,str(self.incPath)))
#
#Loader.add_constructor('!include', Loader.include)

class IncPath():
    def __init__(self):
        self.incPath = ['.']
        try:
            iPath = os.environ['YAML2RPM_INC']
            self.incPath.extend( iPath.split(':'))
        except:
            pass    

    def getPath(self):
        return self.incPath


class IncParser(io.FileIO):
    """ This class handles !include directives to have a more natural 'include this
            yaml file' and merge with keys """
    def __init__(self,filename,mode='r'):
        global incMap

        if filename in list(incMap.keys()):
            filename = incMap[filename]

        self.incPath = IncPath().getPath()
        self.filename = filename

        # now go the incPath looking for the file
        for p in self.incPath:
            try:
                fullpath = os.path.join(p,filename)
                super(IncParser,self).__init__(fullpath,mode)
                with open(fullpath, 'r') as f:
                    self.items = [l for l in f]
                    # pdb.set_trace()         
                    self.iter = iter(self.items)
                    self.child = []
                    return
            except:
                pass
        raise  Exception("%s not found in: %s" % (filename,str(self.incPath)))

    # We are including files, so we need to go to the current include file, which may be 
    # several layers deep. Find the correct lines to iterate through
    def getIter(self):
        if not self.child:
           return self.iter
        else:
           return self.child[0].getIter()

    def read(self,size):
        # Called by the YAML parser, it is supposed to return lines of valid YAML or comments
        # since we have includes, this is more complicated.
        try:
            line = next(self.getIter())
            # we need to NOT return text that says !include to the YAML parser, but only the included
            # text. In other words, parse the included file, but don't return !include
            if line.startswith("!include"):
                incName = line.split()[1]
                self.child.insert(0,IncParser(incName))
                return self.read(size)
            return line 
        except StopIteration:
            if not self.child:
                return ""
            # We reached the end of the current file that we were reading. go up one level and read the
            # the next line of that file 
            self.child.pop(0)
            return self.read(size)

        
class mkParser(object):
    def __init__(self):
        self.varsdict = {}
        self.varpat = re.compile('{{[A-Za-z0-9_\. ]+}}')
        self.kvdict = None   
        self.defaults = None 
        self.combo = None 
        self.incPath = IncPath().getPath()

    def readPkgYaml(self,fname):
        f = IncParser(fname)
        docs = yaml.load_all(f)
        self.kvdict = self.mergeDocs(docs) 
        self.combine()
    
    def readDefaultsYaml(self,fname):
        fnames = [fname]
        fnames.extend( [os.path.join(p,fname) for p in self.incPath])
        for name in fnames: 
            try:
                f = IncParser(name)
                docs = yaml.load_all(f)
                self.defaults = self.mergeDocs(docs)
                self.combine()
                return
            except Exception as ex: 
                pass
        raise Exception("Could not find defaults file in %s" % str(fnames))

    def mergeDocs(self,docs):
        """ Merge parsed YAML docs into a single dictionary. Keys are overwritten if 
            multiple docs have the same key. If a key is a dictionary old and new are merged
            the latter fileds are overwriting the former """
        fullDict = {}
        for d in docs: 
            if type(d) is list:
                srcDct = d[0]
            else:
                srcDct = d
            for k in list(srcDct.keys()):
                if type(srcDct[k]) is dict:
                    if "OVERWRITE" in srcDct[k]:  # overwrite whole dict
                        fullDict[k] = srcDct[k]
                    elif k in fullDict:           # merge with previus dict, overwrite with new key values
                        context = fullDict[k].copy()
                        context.update(srcDct[k])
                        fullDict[k] = context
                    else:                         # add new dict item
                        fullDict[k] = srcDct[k]
                else:
                    fullDict[k] = srcDct[k]

        return fullDict

    def combine(self):
        """ Combine pkg and defaults """
        # logic: if either defaults or kvdict is None, combo is whatever we have
        # if both are available combine
        if self.defaults is None or self.kvdict is None:
            if self.defaults is not None:
                self.combo = self.defaults.copy() 
            elif self.kvdict is not None:
                self.combo = self.kvdict.copy() 
        if self.defaults is not None and self.kvdict is not None:
            self.combo = self.defaults.copy()
            self.combo.update(self.kvdict)

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
        dkey = ["['%s']"%x for x in comps]
        try:
            val = eval("ldict%s"%"".join(dkey))
        except:
            val = ldict[e]
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
        rhs = self.lookup(e,self.combo,stringify,listSep=listSep)
        if stringify:
            resolved = self.replaceVars(rhs,self.varsdict)
        else:
            resolved = rhs
        if resolved == "None":
            return ''
        return resolved
        
    def resolveStr(self,str,listSep=None):
        """ Resolve a string with vars """
        return self.replaceVars(str,self.varsdict,listSep)

    def lookupAndResolve(self,keyword,joinString,listSep=None):
        """ Lookup a keyword/keyval pair. 
            if keval is a list, join the elements
            via the joinString, then resolve elements 
                    Note: throws an exception if keyword does not exist """

        elems =  self.rLookup(keyword,stringify=False,listSep=listSep )
        #pdb.set_trace()
        if type(elems) is list:
            rv = []
            for e in elems:
                expanded = self.replaceVars(e,self.varsdict)
                if type(expanded) is list:
                     rv.extend(expanded)
                else: 
                     rv.extend([expanded])
            elems = joinString.join(rv) 
        return self.resolveStr(elems,listSep)

    def hasVars(self,s):
        """ determine if a string has vars {{ }} """
        return len(re.findall(self.varpat,str(s))) > 0

    def varsInString(self,s):
        """ Return all the variable patterns in the supplied string """
        return re.findall(self.varpat,str(s))

    def extractVars(self,s):
        """ return a list of 'stripped' var names """
        lvars = [x.replace('{{','').replace('}}','').strip() for x in re.findall(self.varpat,str(s))]
        return lvars

    def replaceVars(self, src, vdict, listSep=None):
        """ replace the vars in src with variables in a variables dict  """
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
                        tmp = self.replaceVars(expand,vdict,listSep)
                        if listSep is None:
                            if type(tmp) is list:
                                newlist.extend(tmp)
                            else:
                                newlist.extend([tmp])
                        else:
                            if type(tmp) is list:
                                elem = elem.replace(var, listSep.join(tmp))
                            else:
                                elem = elem.replace(var, tmp)
                if len(newlist) == 0:
                    rwork.append(elem)
                else:    
                    rwork.extend(newlist)
            else:
                tmp = self.replaceVars(elem,vdict,listSep)
                rwork.append(tmp)
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
        for key in list(self.combo.keys()):
            rhs = self.combo[key]
            if self.hasVars(rhs):
                for v in self.extractVars(rhs):
                    self.setVar(self.varsdict,v,rhs)


        # Do an initial pass of setting key-value pairs
        # Do NOT Stringify at this point
        for v in list(self.varsdict.keys()):
            self.setVar(self.varsdict,v,self.lookup(v,self.combo,False))

        while True:
            changed = 0
            for v in list(self.varsdict.keys()):
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
        sublists = list([x for x in mllist if type(x) is list])
        literals = list([x for x in mllist if type(x) is not list])
        if len(sublists) == 0:
            return literals
        else:
            literals.extend(self.flatten([val for sub in sublists for val in sub]))
            return literals

class moduleGenerator(object):
    def __init__(self,mkp):
        """ mkp is an mkParser, already initialized """
        self.mk = mkp
        try:
            self.category = self.mk.rLookup("category") 
        except:
            self.category = ""

        try:
            self.description = self.mk.rLookup("description") 
        except:
            self.description = ""

        try:
            self.logname = self.mk.rLookup("module.logname") 
        except:
            self.logname = ""

        try:
            self.version = self.mk.rLookup("version") 
        except:
            self.version = ""

        try:
            self.name = self.mk.rLookup("name")
            self.descriptionList = self.description.split("\n")[:-1] # description as list of lines
            self.logger = "\nif { [ module-info mode load ] } {\n  %s\n}"
            self.listPrereqs()
            try:
                self.reqs =  self.mk.lookupAndResolve("requires"," " )
                if type(self.reqs) is str:
                    self.reqs = self.reqs.split(" ")
            except:
                self.reqs =  []
        except:
            pass


    def gen_header(self):
        profile = """#%%Module1.0
#####################################################################
## Date: %s
## Built on: %s
## Standard header for invoking autoloading functionality 
##
source /opt/rcic/include/rcic-module-head.tcl
""" 
        rstr = profile % (str(datetime.date.today()),socket.getfqdn())    
        return rstr


    def gen_tail(self):
        profile = """
#####################################################################
## Standard tail for invoking autoloading functionality 
## 
source /opt/rcic/include/rcic-module-tail.tcl
""" 
        rstr = profile 
        return rstr

    def gen_help(self):
        """ generate ModuleHelp function """
        rstr =  '\nproc ModulesHelp { } {\n'
        if len(self.version) > 0:
            rstr += '        puts stderr "\\tModule: %s version %s"\n' % (self.name, self.version)
        else:
            rstr += '        puts stderr "\\tModule: %s"\n' % (self.name)
        template = '        puts stderr "\\t%s"\n'
        for txtline in self.descriptionList: 
            rstr += template % txtline
        rstr =  rstr[0:-2] + '\\n"\n' # add NL to the last line item 
        rstr += '}\n\n'
        return rstr

    def gen_whatis(self):
        """ generate module-whatis lines """
        rstr = 'module-whatis "Category_______ %s"\n' % self.category
        rstr += 'module-whatis "Name___________ %s"\n' % self.name
        if len(self.version) > 0:
            rstr += 'module-whatis "Version________ %s"\n' % self.version
        rstr += self.genMultiLine('module-whatis "Description____ %s"\n', self.descriptionList)
        if self.prereqModules:
            rstr += self.genMultiLine('module-whatis "Load modules___ %s"\n', self.prereqModules)
        if self.reqs:
            #print ("DEBUG3", type(self.reqs), self.reqs)
            rstr += self.genMultiLine('module-whatis "Prerequisites__ %s"\n', self.reqs)
        rstr += '\n'
        return rstr

    def genMultiLine(self, headline, items):
        """ generate multi-line item for module-whatis """
        if items == []:
            return  headline % "none"
        template = 'module-whatis "                %s"\n'
        rstr = headline % items[0]
        for txtline in items[1:]:
            rstr += template % txtline
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


    def gen_alias(self):
        """ Create Aliases from module.alias list """
        rstr = ""
        try:
            entries = self.mk.rLookup("module.alias", stringify=False)
        except:
            return rstr
        aliasVars = [ self.mk.resolveStr(p) for p in entries ]
        aliasVars = self.mk.flatten(aliasVars)
        template = "set-alias\t%s\t%s\n"
        for aliasVar in aliasVars:
            aName,aVal = re.split('[ \t]+', aliasVar, 1)
            rstr += template % ( self.mk.resolveStr(aName), self.mk.resolveStr(aVal))
        return rstr

    def listPrereqs(self):
        """ find prerequisite modules """
        self.prereqModules = []
        try:
            entries = self.mk.rLookup("module.prereq", stringify=False)
        except:
            return 
        prereqs = [ self.mk.resolveStr(p) for p in entries ]
        self.prereqModules = self.mk.flatten(prereqs)

    def gen_prereqs(self):
        """ load other modules as prereqs """
        rstr = ""
        template = 'if { [module-info mode load] } { LoadPrereq "%s" }\nprereq\t%s\n'
        for prereq in self.prereqModules:
            mod = self.mk.resolveStr(prereq)
            rstr += template % (mod,mod)
        return rstr

    def gen_logger(self):
        """ Create logging statement """
        if len(self.logname) > 0:
            logstr = "exec /bin/logger -p local6.notice -t module-hpc $env(USER) %s" % (self.logname)
        elif len(self.version) > 0:
            logstr = "exec /bin/logger -p local6.notice -t module-hpc $env(USER) %s/%s" % (self.name, self.version)
        else:
            logstr = "exec /bin/logger -p local6.notice -t module-hpc $env(USER) %s" % (self.name)
        rstr =  self.logger % logstr
        return rstr

    def generate(self):
        """ return a string that can written as  module file """
        rstr = ""
        rstr += self.gen_header()
        rstr += self.gen_help()
        rstr += self.gen_whatis()
        rstr += self.gen_prereqs()
        rstr += self.gen_setenv()
        rstr += self.gen_alias()
        rstr += self.prepend_path() 
        rstr += self.gen_tail() 
        rstr += self.gen_logger() 
        return rstr

class makeIncludeGenerator(object):
    """ Create output for Definitions.mk """
    def __init__(self,mkp):
        """ mkp is an mkParser, already initialized """
        self.mk = mkp

    def generate(self):
        rstr = ""
        # The following are "Required" keys - meaning packaging should fail without them
        # However, if we use this parsing for other reasons, having these be missing might be OK 
        # The following are required keys -- throw an error if they don't exist
        options=[ ("TARNAME","name"),("VERSION", "version")]
        options.extend([ ("NAME","pkgname","$(TARNAME)_$(VERSION)") ])
        options.extend([ ("TARBALL-EXTENSION","extension") ])
        options.extend([ ("PKGROOT","root") ])

        rstr += "DESCRIPTION \t = " 
        try:
            self.description = self.mk.rLookup("description") 
            self.descriptionList = self.description.split("\n")[:-1] # description as list of lines
            if len(self.descriptionList) == 0:
                rstr += self.description + "\n"
            else:
                for txtline in self.descriptionList: 
                    rstr += "%s \\\n" % txtline
                rstr =  rstr[0:-3] + "\n" # rm last ' \' and add NL back
        except:
            rstr += "\n"

        # Standard options and defaults, if defined
        # Format of these tuples
        #           (MAKEFILE VAR, YAML VAR, [default])
        options.extend([ ("RELEASE","release"),("VENDOR", "vendor"), ("SRC_TARBALL","src_tarball") ])
        options.extend([ ("RPM.ARCH", "arch")])
        options.extend([ ("SRC_DIR","src_dir"),("NO_SRC_DIR", "no_src_dir") ])
        options.extend([ ("PRECONFIGURE", "build.preconfigure","echo no preconfigure required")])
        options.extend([ ("BUILDTARGET", "build.target")])
        options.extend([ ("PKGMAKE", "build.pkgmake")])
        options.extend([ ("MAKEINSTALL", "install.makeinstall")])
        options.extend([ ("INSTALLEXTRA", "install.installextra")])
        options.extend([ ("MODULENAME", "module.name","")])
        options.extend([ ("MODULESPATH", "module.path","")])
        options.extend([ ("RPMS.SCRIPTLETS.FILE", "rpm.scriptlets")])
        options.extend([ ("RPM.OBSOLETES", "obsoletes")])
        options.extend([ ("RPM.CONFLICTS", "conflicts")])
        
        # The options look the same in the Makefile, some have defaults
        for option in options:
            mfVar = option[0]
            yamlVar = option[1]
            try:
                rVar = self.mk.rLookup(yamlVar)
                rstr += "%s\t = %s\n" % (mfVar,rVar)
            except:
                # if it has a default value, print it. 
                if len(option) == 3: 
                   rstr += "%s\t = %s\n" % (mfVar,option[2])
                
        # Handle configure separately
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
            mods =  self.mk.lookupAndResolve("build.modules"," ")
            if mods == "None":
                mods = ""
            rstr += "MODULES \t = %s\n" % mods 
        except:
            pass

        try:
            rstr += "PATCH_FILE \t = %s\n" % self.mk.rLookup("build.patchfile")
            rstr += "PATCH_METHOD \t = $(PATCH_CMD)\n" 
        except:
            rstr += "PATCH_METHOD \t = $(PATCH_NONE)\n" 

        try:
            reqs =  self.mk.lookupAndResolve("requires"," ")
            if type(reqs) is list:
                reqs = " ".join(reqs)
            rstr += "RPM.REQUIRES\t = %s\n" % reqs
        except:
            pass

        try:
            provs =  self.mk.lookupAndResolve("provides"," ")
            if type(provs) is list:
                provs = " ".join(provs)
            rstr += "RPM.PROVIDES\t = %s\n" % provs
        except:
            rstr += "RPM.PROVIDES\t = \n" 


        try:
            files =  self.mk.lookupAndResolve("files","\\n\\\n")
            rstr += "RPM.FILES\t = %s\n" % files 
        except:
            try:
                files =  self.mk.lookupAndResolve("fileslist","\\n\\\n")
                rstr += "RPM.FILESLIST\t = %s\n" % files 
            except:
                rstr += "RPM.FILES\t = $(PKGROOT)\n" 


        try:
            extras =  self.mk.lookupAndResolve("rpm.extras","\\n\\\n",listSep=" ")
            rstr += "RPM.EXTRAS\t = %s\n" % extras 

        except:
            pass
            
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
            try: 
               rstr = self.mk.rLookup("src_tarball")
            except:
               rstr = self.mk.rLookup("name")
               rstr += "-%s" % str(self.mk.rLookup("version"))
               rstr += ".%s" % self.mk.rLookup("extension")
            print(rstr)
            sys.exit(0)
        if rq == "pkgname":
            try:
                rstr = self.mk.rLookup("pkgname")
            except:
                rstr = "%s_%s" % (self.mk.rLookup("name"), self.mk.rLookup("version")) 
            print(rstr)
            sys.exit(0)
        try:
            rval = self.mk.lookupAndResolve(rq,listSep,listSep=listSep)
        except:
            if not quiet:
                print('False')
            sys.exit(-1)
            
        if len(rval) > 0:
            print(rval)
        elif not quiet:
            print('True')

## *****************************
## main routine
## *****************************

def main(argv):
    global incMap

    dflts_file = 'pkg-defaults.yaml'  # defaults package file, assume in the current yamlspecs/ directory 

    # descriptionand help lines for the usage  help
    description = "The definitions parser gen-defintions.py reads the yaml descripton file\n" 
    description += "and creates include and module files needed for generating of RPM package"

    helpquery = "query if value exists in the yaml file and  print  the result on stdout. Valid types are the keywords in the\n"
    helpquery += "the yaml file: patch, module, source, pkgname, etc. Example: --query=source. If nout found, prints 'False'\n"

    helpdefaults = "specify packaging defaults yaml file to use. If none is provided, use:\n"
    helpdefaults += "(1) specific ./%s in the current yamlspecs/ directory; if exists \n" % dflts_file
    helpdefaults += "(2) default /opt/rocks/yaml2rpm/sys/%s otherwise \n" % dflts_file 

    helpskipdefaults = "To skips all defaults reading" 

    helplsep = "use a list separator for printing a query result as a string in the case when multiple items are returned.\n"
    helplsep += "Valid when -q option is present. Default output is a single element (str) or an array of elements [str,str]."

    helpmap = "use mapping to substitute a default file with a replacement. Can use when building multiple versions of the\n"
    helpmap += "package. Mapping is  python dictionary, ke is the original file, and the value is the substitute file. For \n"
    helpmap += "example, -map=\"{'gcc-versions.yaml':'gcc-versions-8.yaml'}\" replaces default yaml file with a specific version"

    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    # optional arguments
    parser.add_argument("-d", "--defaults", dest="dflts_file", default=dflts_file, help=helpdefaults)
    parser.add_argument("-D", "--no-defaults", dest="skipDefaults", default=False, action='store_true', help=helpskipdefaults)
    parser.add_argument("-m", "--module",   dest="doModule",   default=False, action='store_true', help="generate environment modules file")
    parser.add_argument("-q", "--query",    dest="doQuery",    default=False, help=helpquery)
    parser.add_argument("-l", "--listsep",  dest="listSep",    default=None,  help=helplsep)
    parser.add_argument("-Q", "--quiet",    dest="quiet",      default=False, action='store_true', help="supress output of query processing")
    parser.add_argument("-M", "--map",      dest="mapf",       default=False, help=helpmap)
    # required positional argument
    parser.add_argument("yamlfile",  action="store", help="main YAML file with packaging definitions") 
    args = parser.parse_args()
    
    if args.mapf: 
        incMap.update(eval(args.mapf))

    # Open input yaml files, parse, generate
    mkP = mkParser()
    mkP.readPkgYaml(args.yamlfile)
    if not args.skipDefaults:
        mkP.readDefaultsYaml(args.dflts_file)
    mkP.resolveVars()

    ### DEBUG
    #a = mkP.__dict__['varsdict']
    #print ("DEBUG", type(a), a.keys())

    mg = moduleGenerator(mkP)
    #print ("DEBUG2", mg.__dict__['reqs'])

    mig = makeIncludeGenerator(mkP)
    qp = queryProcessor(mkP)

    if args.doModule: 
        print(mg.generate() )
    elif args.doQuery:
        qp.processQuery(args.doQuery,args.quiet,args.listSep)
    else:
        print(mig.generate())

if __name__ == "__main__":
    main(sys.argv[1:])
        
