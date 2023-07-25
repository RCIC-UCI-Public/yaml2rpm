#!/usr/bin/env python
# Generate a Definitions.mk file - write to standard output 

from __future__ import print_function
#from builtins import str  # does not work with python2, breaks recursion

import ruamel.yaml 
import re
import sys
import datetime
import socket 
import os
import io
import argparse
import pdb
import time
from multiprocessing import Pool


if sys.version_info.major == 3:
    from typing import Dict
    from builtins import next 
    from builtins import object

incMap = {}   # type: dictionary, represents mapping of included filenames
incStack = [] # type: list of strings keep track of ACTIVE !include maps

#yaml = ruamel.yaml.YAML(typ='safe', pure=True)
#yaml.default_flow_style = False

def new_compose_document(self):
    self.parser.get_event()
    node = self.compose_node(None, None)
    self.parser.get_event()
    return node

def new_yaml_include(loader, node):
    y = loader.loader
    incPath = IncPath().getPath()
    global incMap,incStack
    filename = loader.construct_scalar(node)
    mapped= False
    if filename in list(incMap.keys()):
        incStack.append(filename)   # Track that we are currently remapping a filename
        mapped = True
        filename = incMap[filename]
    for p in incPath:
        try:
            fname = os.path.join(p,filename)
            with open(fname, 'r') as f:
                tparser=mkParser()
                tparser.readPkgYaml(fname)
                data = tparser.combo
                if mapped: 
                    incStack.pop() 
                return data
        except Exception as err:
           pass
           #DEBUG print("Exception: %s", str(err)) 
    raise  Exception("%s not found in: %s" % (filename,str(incPath)))


#yaml.Composer.compose_document = new_compose_document
#yaml.Constructor.add_constructor("!include", new_yaml_include)

## This section of code enables yaml declarations of
##      var: !eval "<python code>"
## once all {{vars}} have been replaced, the statement itself can be evaluated. 
## The evaluation should return a single string. 
## A simple example
##     foo: !eval "'{{bar}}' if {{testval}}==5 else '{{baz}}'"

class evalStmt(object):
    def __init__(self,rhs='',evaluated=False):
        self._stmt = str(rhs)
        self._evaluated = evaluated
        self._value = str(rhs) 
    
    @property
    def stmt(self):
        return self._value if self._evaluated else self._stmt

    @stmt.setter
    def stmt(self,value):
        self._stmt=value 

    @property 
    def evaluated(self):
        return self._evaluated

    def __str__(self):
        return self.stmt 

    def __len__(self):
        return len(self.stmt)

    ## Evaluate the stmt
    def eval(self):
        if  not self._evaluated:
            self._value = eval(self.stmt)
            self._evaluated = True
        return self._value

## This is subclass of eval that execs more complicated python code. The code MUST
## set the variable __rval as the value "returned" from the exec
## eg. get that PATH variable from the environment
##    foo: !exec "import os; __rval=os.environ['PATH']"

class execStmt(evalStmt):
    def eval(self):
        # Create a dictionary of "globals", code should set __rval
        gdict={'__rval':''}
        if not self._evaluated:
            exec(self.stmt,gdict)
            self._value = gdict['__rval']
            self._evaluated = True
        return self._value 
      
def yaml_python_eval(loader, node):
    stmt = loader.construct_scalar(node)
    return evalStmt(stmt)
   
def yaml_python_exec(loader, node):
    stmt = loader.construct_scalar(node)
    return execStmt(stmt)
   
def yaml_python_ifeq(loader, node):
    ### !ifeq "x,y,<true result>[,<false result>]
    template= "'%s' if '%s' == '%s' else '%s'"
    return parseIfstmt(loader, node, template)

def yaml_python_ifneq(loader, node):
    ### !ifneq "x,y,<true result>[,<false result>]
    template= "'%s' if '%s' != '%s' else '%s'"
    return parseIfstmt(loader, node, template)

def parseIfstmt(loader,node,template):
    raw = loader.construct_scalar(node)
    parsed = [ x.strip() for x in raw.split(",")]
    try:
         (what,compare,truestmt,elsestmt) = parsed
    except:
         elsestmt = ''
         (what,compare,truestmt)= parsed
    return evalStmt(template % (truestmt,what,compare,elsestmt))
    
class IncPath(object):
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
        global incMap,incStack
        if filename in list(incMap.keys()) and filename not in incStack:
            filename = incMap[filename]

        # now go the incPath looking for the file
        self.incPath = IncPath().getPath()
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
        self.combo = {} 
        self.yaml = ruamel.yaml.YAML(typ='safe', pure=True)
        self.yaml.default_flow_style = False
        self.yaml.Composer.compose_document = new_compose_document
        self.yaml.Constructor.add_constructor("!include", new_yaml_include)
        self.yaml.Constructor.add_constructor("!eval", yaml_python_eval)
        self.yaml.Constructor.add_constructor("!exec", yaml_python_exec)
        self.yaml.Constructor.add_constructor("!ifeq", yaml_python_ifeq)
        self.yaml.Constructor.add_constructor("!ifneq", yaml_python_ifneq)

    def readPkgYaml(self,fname):
        """ read yaml file, proesss loading of all included yamls,
            merge all into one dictionary and update self.combo with the result """
        f = IncParser(fname)
        docs = list(filter(lambda x: x is not None,list(self.yaml.load_all(f))))
        kvdict = self.mergeDocs(docs) 
        self.combo.update(kvdict)
    
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

    def lookup(self,e,ldict=None,stringify=True):
        """Looks up x.y.z references in multilevel dictionary
           stringify: True - return a string representation of contents
                      False - return the contents (could be any python type)"""

        if ldict is None:
            ldict = self.combo
        comps=e.split('.')
        dkey = ["['%s']"%x for x in comps]
        try:
            val = eval("ldict%s"%"".join(dkey))
        except:
            val = ldict[e]
        if type(val) is list: 
            val = [_f for _f in val if _f]                  # filter out  empty string
            val = [word for word in val if word != 'None']  # filter out  None
            val = self.flatten(val)
        if val is None: # definition in yaml was empty. TODO remove this check
            return ''
        if isinstance(val,evalStmt) and val.evaluated:  # replace evalStmt with string version ASAP
            val = str(val)
        if stringify:
            return str(val)
        if type(val) in [type(1),type(1.1),type(True)]:
            return str(val)
        return val

    def lookupAndResolve(self,keyword,joinString):
        """ Lookup a value for key.  if val is a list, join the elements
            via the joinString. 
            Note: throws an exception if keyword does not exist """

        elems = self.lookup(keyword,stringify=False)
        if type(elems) is list:
            elems = joinString.join(elems) 
        elif type(elems) is bool: # convert boolean to string
            elems = str(elems)
        return elems

    def stringRep(self, obj):
        """recursively expand object to provide a string representation"""
        basetypes = [type(""), type(1.0), type(1), type(True)]
        if isinstance(obj,evalStmt) or type(obj) in basetypes:
           return str(obj)
        try:
            return " ".join([self.stringRep(x) for x in obj.values()])
        except:
            return " ".join([self.stringRep(x) for x in obj])


    def hasVars(self,s):
        """ determine if an object has vars {{ }} """
        return len(re.findall(self.varpat,self.stringRep(s))) > 0

    def varsInString(self,s):
        """ Return all the variable patterns in the supplied string """
        return re.findall(self.varpat,self.stringRep(s))

    def extractVars(self,s):
        """ return a list of 'stripped' var names """
        lvars = [x.replace('{{','').replace('}}','').strip() for x in re.findall(self.varpat,self.stringRep(s))]
        res = []
        [res.append(x) for x in lvars if x not in res] # remove duplicates
        lvars = res
        return lvars

    def replaceStr(self, elem, vdict):
        if not self.hasVars(elem):
            return elem
        for var in self.varsInString(elem):
            subvar = var.replace('{{','').replace('}}','').strip()
            expand = self.lookup(subvar,vdict,stringify=False)
            if type(expand) is type("string"):
                elem = elem.replace(var,expand)
            if type(expand) is list:
                check = elem.replace('{{','').replace('}}','').strip()
                if len(check) > len(subvar):
                    elem = elem.replace(var, " ".join(expand)) # variable was inside a string, join list with ' '
                else:
                    elem = expand
        return elem
            
    def replaceVars(self, src, vdict):
        """ replace the vars in src with variables from vdict
            recursively call if src is type list or type dictionary
        """
        if type(src) is type(None):
            work = ''
        if type(src) is type("string"):
            work = self.replaceStr(src, vdict)
        if isinstance(src,evalStmt):
            src.stmt = self.replaceStr(src.stmt, vdict) 
            if not self.hasVars(src.stmt):
               src.eval()   # evaluate the statement as soon as possible
            work = src.stmt
        if type(src) is list:
            work = []
            for elem in src:
                work.append(self.replaceVars(elem, vdict))
        if type(src) is dict:
            work = {}
            for key in src.keys():
                work[key] = self.replaceVars(src[key], vdict)
        return work

    def setVar(self,vdict,v,value=''):
        vdict[v] = value

    def replaceNoneIntFloat(self):
        """ replace all None and int values as '' """
        tvect = [type(1),type(1.1),type(True)]
        for key in self.combo.keys():
            rhs = self.combo[key]
            if rhs is None: 
                self.combo[key] = ''
            elif rhs is type(""): 
                self.combo[key] = rhs.rstrip("\n") 
            elif type(rhs) in tvect:
                self.combo[key] = str(rhs)
            elif type(rhs) is type({}):
                d = self.combo[key]
                for k,v in d.items():
                    if type(v) in tvect:
                        d[k] = str(v)
                    elif v is None:
                        d[k] = ''
                    elif type(v) is type(""):
                        d[k] = v.rstrip("\n")
                    else:
                        pass
                self.combo[key] = d

    def resolveVars(self):
        """ Resolve all variables in the combo dictionary. As variables are 
            are resolved, the object varsdict will hold the resolved versions """

        # replace None,float,int values with strings
        self.replaceNoneIntFloat()

        # find all the vars that need to be replaced in any definition
        for key in list(self.combo.keys()):
            rhs = self.combo[key]
            if self.hasVars(rhs):
                for v in self.extractVars(rhs):
                    self.setVar(self.varsdict,v,'')

        # initial setting of key-value pairs from combo dict, no strignigy
        for v in self.varsdict.keys():
            self.setVar(self.varsdict,v,self.lookup(v,self.combo,stringify=False))

        # resolve all variables in varsdict
        while True:
            changed = 0
            for v in self.varsdict.keys():
                if self.hasVars(self.varsdict[v]):
                    rhs = self.replaceVars(self.varsdict[v],self.varsdict) 
                    # special handling of evalStmt objects 
                    var = self.varsdict[v]
                    if isinstance(var,evalStmt):
                        rhs = type(var)(rhs,var.evaluated)  # new instance with some/all vars replaced
                    self.varsdict[v] = rhs
                    changed = 1
            if changed == 0:
                break

        # update combo/varsdict values with resolved from varsdict
        for key, val in self.varsdict.items():
            if isinstance(val,evalStmt):
               resolved = val.eval()
               self.varsdict[key] = resolved
               val = resolved
            self.combo[key] = val

        # resolve all variables in combo dict
        while True:
            changed = 0
            for v in self.combo.keys():
                if self.hasVars(self.combo[v]):
                    rhs = self.replaceVars(self.combo[v],self.combo) 
                    var = self.combo[v]
                    if isinstance(var,evalStmt):
                        rhs = type(var)(rhs,var.evaluated)
                    self.combo[v] = rhs
                    changed = 1
                elif isinstance(self.combo[v],evalStmt):
                    self.combo[v] = self.combo[v].eval()
            if changed == 0:
                break

    def flatten(self, mllist):
        """ recursive method to flatten list of elements where each element
            might itself be a list. Returns a list """
        sublists = [x for x in mllist if type(x) is list] 
        literals = [x for x in mllist if type(x) is not list] 
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
            self.category = self.mk.lookup("category") 
        except:
            self.category = ""

        try:
            self.description = self.mk.lookup("description") 
        except:
            self.description = ""

        try:
            self.logname = self.mk.lookup("module.logname") 
        except:
            self.logname = ""

        try:
            self.version = self.mk.lookup("version") 
        except:
            self.version = ""

        try:
            self.name = self.mk.lookup("name")
            self.descriptionList = self.description.split("\n")[:-1] # description as list of lines
            self.logger = "\nif { [ module-info mode load ] } {\n  %s\n}"
            self.listPrereqs()
            try:
                self.reqs = self.mk.lookup("requires",stringify=False)
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
        rstr = profile % (str(datetime.date.today()),socket.gethostname()) # faster than socket.getfqdn()
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

    def gen_lines(self, keyword, word):
        """ Create elements based on keyword and word for tempalte """
        rstr = ""
        try:
            entries = self.mk.lookup(keyword, stringify=False)
        except:
            return rstr
        Vars = self.mk.flatten(entries)
        template = word + "\t%s\t%s\n"
        for Var in Vars:
            eName,eVal = re.split('[ \t]+', Var, 1)
            rstr += template % (eName, eVal)
        return rstr

    def listPrereqs(self):
        """ find prerequisite modules """
        self.prereqModules = []
        try:
            prereqs = self.mk.lookup("module.prereq", stringify=False)
            if type(prereqs) is str:
                    prereqs = prereqs.split(" ")
            prereqs = [_f for _f in prereqs if _f]  # filter ''
            self.prereqModules = prereqs
        except:
            return 

    def gen_prereqs(self):
        """ load other modules as prereqs """
        rstr = ""
        template = 'if { [module-info mode load] } { LoadPrereq "%s" }\nprereq\t%s\n'
        for mod in self.prereqModules:
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

    def generateModFile(self):
        """ return a string that can written as  module file """
        rstr = ""
        rstr += self.gen_header()
        rstr += self.gen_help()
        rstr += self.gen_whatis()
        rstr += self.gen_prereqs()
        rstr += self.gen_lines("module.setenv", "setenv")
        rstr += self.gen_lines("module.alias", "set-alias")
        rstr += self.gen_lines("module.prepend_path", "prepend-path")
        rstr += self.gen_tail() 
        rstr += self.gen_logger() 
        return rstr

class makeIncludeGenerator(object):
    """ Create output for Definitions.mk """
    def __init__(self,mkp):
        """ mkp is an mkParser, already initialized """
        self.mk = mkp

    def generateDefs(self):
        rstr = ""
        # The following are "Required" keys - meaning packaging should fail without them
        # However, if we use this parsing for other reasons, having these be missing might be OK 
        options=[ ("TARNAME","name"),("VERSION", "version")]
        options.extend([ ("NAME","pkgname","$(TARNAME)_$(VERSION)") ])
        options.extend([ ("TARBALL-EXTENSION","extension") ])
        options.extend([ ("PKGROOT","root") ])

        rstr += "DESCRIPTION \t = " 
        try:
            self.description = self.mk.lookup("description") 
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
        # Format of these tuples (MAKEFILE VAR, YAML VAR, [default])
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
                rVar = self.mk.lookup(yamlVar)
                rstr += "%s\t = %s\n" % (mfVar,rVar)
            except:
                # if it has a default value, print it. 
                if len(option) == 3: 
                   rstr += "%s\t = %s\n" % (mfVar,option[2])
                
        # Handle configure separately
        stdconfigure = "+=" 
        try:
            cprog = self.mk.lookup("build.configure")
            rstr +=  "CONFIGURE \t = %s\n" % cprog
            stdconfigure = "="
        except:
            pass

        try:
            cargs = self.mk.lookup("build.configure_args")
            rstr += "CONFIGURE_ARGS \t %s %s\n" % (stdconfigure, cargs)
        except:
            pass

        try:
            mods =  self.mk.lookupAndResolve("build.modules"," ")
            rstr += "MODULES \t = %s\n" % mods 
        except:
            pass

        try:
            rstr += "PATCH_FILE \t = %s\n" % self.mk.lookup("build.patchfile")
            rstr += "PATCH_METHOD \t = $(PATCH_CMD)\n" 
        except:
            rstr += "PATCH_METHOD \t = $(PATCH_NONE)\n" 

        try:
            reqs =  self.mk.lookupAndResolve("requires"," ")
            rstr += "RPM.REQUIRES\t = %s\n" % reqs
        except:
            pass

        try:
            provs =  self.mk.lookupAndResolve("provides"," ")
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
            extras = self.mk.lookup("rpm.extras",stringify=False)
            rstr += "RPM.EXTRAS\t = %s\n" % extras 
        except:
            pass
            
        return rstr

class queryProcessor(object):
    """ Query based on the yaml file """
    def __init__(self,mkp):
        """ mkp is an mkParser, already initialized """
        self.mk = mkp

    def processQuery(self,query,quiet=False):
        rq = query.strip().lower()
        if rq == "patch":
            rq = "build.patchfile"
        elif rq == "source":
            rq = "vendor_source"

        if rq == "tarball":
            try: 
               rstr = self.mk.lookup("src_tarball")
            except:
               rstr = self.mk.lookup("name")
               rstr += "-%s" % str(self.mk.lookup("version"))
               rstr += ".%s" % self.mk.lookup("extension")
            return rstr
        if rq == "pkgname":
            try:
                rstr = self.mk.lookup("pkgname")
            except:
                rstr = "%s_%s" % (self.mk.lookup("name"), self.mk.lookup("version")) 
            return rstr
        try:
            rval = self.mk.lookupAndResolve(rq,' ')
        except:
            if not quiet:
                return('False')
            return ""

        if len(rval) > 0:
            return rval
        elif not quiet:
            return 'True'

    def processCategory(self):
        try:
            pkgname = self.mk.lookup("pkgname")
        except:
            pkgname = "%s_%s" % (self.mk.lookup("name"), self.mk.lookup("version")) 

        try:
            category = self.mk.lookup("category",stringify=False)
            provides = self.mk.lookup("module.logname") 
        except:
            category = False
            provides = False

        try:
            if category: # for module file
                requires = self.mk.lookup("module.prereq",stringify=False)
            else: # for regular package file
                requires = self.mk.lookup("build.modules",stringify=False)
            if type(requires) is str:
                requires = requires.split(" ")
        except:
            requires = []

        # list can contain '' , remove all occurences
        requires = [value for value in requires if value != '']

        rstr =  "%s:\n" % pkgname
        rstr += "  category: %s" % category
        rstr += "\n  requires:" 
        for i in requires:
            rstr += "\n    - %s" % i
        rstr += "\n  provides:"
        if provides:
            rstr += "\n    - %s" % provides
        return rstr

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

    helpcategory = "does a multiquery for requries, provides and category\n"

    helpdefaults = "specify packaging defaults yaml file to use. If none is provided, use:\n"
    helpdefaults += "(1) specific ./%s in the current yamlspecs/ directory; if exists \n" % dflts_file
    helpdefaults += "(2) default /opt/rocks/yaml2rpm/sys/%s otherwise \n" % dflts_file 

    helpskipdefaults = "To skips all defaults reading" 

    helpmap = "use mapping to substitute a default file with a replacement. Can use when building multiple versions of the\n"
    helpmap += "package. Mapping is  python dictionary, ke is the original file, and the value is the substitute file. For \n"
    helpmap += "example, -map=\"{'gcc-versions.yaml':'gcc-versions-8.yaml'}\" replaces default yaml file with a specific version"

    helpver = "replace versions.yaml in any !includes with new file. E.g. --versions=versions8.yaml \n"
    helpver += "will replace versions.yaml with versions8.yaml. Use either --map or --versions"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    # optional arguments
    parser.add_argument("-d", "--defaults", dest="dflts_file", default=dflts_file, help=helpdefaults)
    parser.add_argument("-D", "--no-defaults", dest="skipDefaults", default=False, action='store_true', help=helpskipdefaults)
    parser.add_argument("-m", "--module",   dest="doModule",   default=False, action='store_true', help="generate environment modules file")
    parser.add_argument("-q", "--query",    dest="doQuery",    default=False, help=helpquery)
    parser.add_argument("-c", "--category", dest="doCategory", default=False, action='store_true',help=helpcategory)
    parser.add_argument("-p", "--parallel", dest="parallel", default=8, action='store',help="How many yaml files to process in parallel")
    parser.add_argument("-Q", "--quiet",    dest="quiet",      default=False, action='store_true', help="supress output of query processing")
    parser.add_argument("-M", "--map",      dest="mapf",       default=False, help=helpmap)
    parser.add_argument("-V", "--versions", dest="versions",       default=False, help=helpver)
    # required positional argument
    parser.add_argument("yamlfiles", nargs="+", help="YAML file(s) with packaging definitions") 
    args = parser.parse_args()
    
    # Check for existence of args.yamlfiles
    for yamlfile in args.yamlfiles:
       if not os.path.isfile(yamlfile):
           sys.stderr.write("yaml file(s) %s does not exist\n" % yamlfile)
           sys.exit(-1)
    if args.mapf: 
        incMap.update(eval(args.mapf))
    if args.versions:
        incMap.update({'versions.yaml':args.versions})

    outputs = processInParallel(args)
    for yamlfile in args.yamlfiles:
        print(outputs[yamlfile])


def processInParallel(args): 
    rval = dict()
    for yamlfile in args.yamlfiles:
        rval[yamlfile] = ""
    subargs = [(yf,args) for yf in args.yamlfiles]

    with Pool(int(args.parallel)) as pool:
       for result in pool.imap_unordered(processFile, subargs):
           rval[result[0]] = result[1]           
    return rval


def processFile(subargs):
    """subargs = (yamlfile, args) 
       returns = (yamlfile, output)
    """
    yamlfile = subargs[0]
    args = subargs[1]
    # Open input yaml files, parse, generate
    mkP = mkParser()
    mkP.readPkgYaml(yamlfile)
    if not args.skipDefaults:
        mkP.readPkgYaml(args.dflts_file)
    mkP.resolveVars()

    ### DEBUG
    #a = mkP.__dict__['varsdict']
    #print ("DEBUG varsdict", type(a), a.keys())

    if args.doModule: 
        mg = moduleGenerator(mkP)
        output = mg.generateModFile()
    elif args.doQuery:
        qp = queryProcessor(mkP)
        output = qp.processQuery(args.doQuery,args.quiet)
    elif args.doCategory:
        qp = queryProcessor(mkP)
        output=qp.processCategory()
    else:
        mig = makeIncludeGenerator(mkP)
        output = mig.generateDefs()
    return (yamlfile,output)

if __name__ == "__main__":
    main(sys.argv[1:])
